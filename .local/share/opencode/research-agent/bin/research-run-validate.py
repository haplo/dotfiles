#!/usr/bin/env python3
"""
research-run-validate: Validate a research run directory and finalize meta.json.

Checks that mandatory files exist and are non-empty, parses searches.jsonl,
computes query/result/fetch counts, and writes the finalized meta.json with
status="complete". Warns (does not fail) on missing recommended files.

Usage:
  research-run-validate <run_dir>
  research-run-validate <run_dir> --mark-failed --error "searcher crashed"

Exit codes:
  0  validation succeeded; meta.json finalized as "complete"
     (or --mark-failed succeeded; meta.json finalized as "failed")
  1  validation failed or filesystem error; meta.json updated to "failed"
     when possible
  2  invalid arguments or run directory does not exist
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

MANDATORY_FILES = ("meta.json", "searches.jsonl", "response.md")
RECOMMENDED_FILES = ("notes.md",)
VALID_ENTRY_TYPES = ("search", "fetch")


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def atomic_write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp.replace(path)


def load_meta(run_dir: Path) -> dict:
    meta_path = run_dir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError("meta.json not found")
    with meta_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check_mandatory_files(run_dir: Path) -> list[str]:
    errors = []
    for name in MANDATORY_FILES:
        path = run_dir / name
        if not path.exists():
            errors.append(f"missing mandatory file: {name}")
        elif path.stat().st_size == 0:
            errors.append(f"mandatory file is empty: {name}")
    return errors


def check_recommended_files(run_dir: Path) -> list[str]:
    warnings = []
    for name in RECOMMENDED_FILES:
        path = run_dir / name
        if not path.exists():
            warnings.append(f"missing recommended file: {name}")
        elif path.stat().st_size == 0:
            warnings.append(f"recommended file is empty: {name}")
    return warnings


def empty_counts() -> dict:
    return {
        "query_count": 0,
        "result_count": 0,
        "fetch_count": 0,
        "fetch_error_count": 0,
    }


def parse_searches_jsonl(run_dir: Path) -> tuple[dict, list[str]]:
    """Parse searches.jsonl and return (counts, errors).

    Returns empty counts and a single error if the file is unreadable or
    missing. Otherwise returns per-line errors for malformed entries and
    counts for the valid ones.
    """
    counts = empty_counts()
    path = run_dir / "searches.jsonl"

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return counts, [f"failed to read searches.jsonl: {e}"]

    errors: list[str] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"searches.jsonl line {lineno}: invalid JSON ({e.msg})")
            continue
        if not isinstance(entry, dict):
            errors.append(f"searches.jsonl line {lineno}: entry is not a JSON object")
            continue

        entry_type = entry.get("type")
        if entry_type not in VALID_ENTRY_TYPES:
            errors.append(
                f"searches.jsonl line {lineno}: invalid or missing 'type' "
                f"(expected one of {list(VALID_ENTRY_TYPES)})"
            )
            continue

        if entry_type == "search":
            counts["query_count"] += 1
            results = entry.get("results")
            if not isinstance(results, list):
                errors.append(
                    f"searches.jsonl line {lineno}: search entry missing 'results' list"
                )
            else:
                counts["result_count"] += len(results)
        else:  # fetch
            counts["fetch_count"] += 1
            if entry.get("error"):
                counts["fetch_error_count"] += 1

    return counts, errors


def finalize_meta(
    run_dir: Path,
    meta: dict,
    counts: dict,
    status: str,
    error: str | None,
) -> None:
    meta["finalized_at"] = utc_now_iso()
    meta["status"] = status
    meta["query_count"] = counts.get("query_count")
    meta["result_count"] = counts.get("result_count")
    meta["fetch_count"] = counts.get("fetch_count")
    meta["fetch_error_count"] = counts.get("fetch_error_count")
    if error is not None:
        meta["error"] = error
    atomic_write_json(run_dir / "meta.json", meta)


def try_finalize_failed(run_dir: Path, counts: dict, error_msg: str) -> None:
    """Best-effort meta.json update on validation failure. Never raises."""
    try:
        meta = load_meta(run_dir)
    except (OSError, ValueError, FileNotFoundError):
        return
    try:
        finalize_meta(run_dir, meta, counts, status="failed", error=error_msg)
    except OSError:
        pass


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="research-run-validate",
        description="Validate a research run directory and finalize meta.json.",
    )
    parser.add_argument(
        "run_dir",
        help="Path to the run directory (e.g. .research/runs/<run-id>).",
    )
    parser.add_argument(
        "--mark-failed",
        action="store_true",
        help="Skip validation; mark the run as failed in meta.json.",
    )
    parser.add_argument(
        "--error",
        help="Error message to record in meta.json (use with --mark-failed).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    run_dir = Path(args.run_dir)

    if not run_dir.is_dir():
        print(f"error: not a directory: {run_dir}", file=sys.stderr)
        return 2

    try:
        meta = load_meta(run_dir)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: failed to read meta.json: {e}", file=sys.stderr)
        return 1

    # --mark-failed path: don't validate, just record the failure.
    if args.mark_failed:
        counts = empty_counts()
        if (run_dir / "searches.jsonl").exists():
            counts, _ = parse_searches_jsonl(run_dir)
        try:
            finalize_meta(
                run_dir,
                meta,
                counts,
                status="failed",
                error=args.error or "marked as failed by researcher",
            )
        except OSError as e:
            print(f"error: failed to write meta.json: {e}", file=sys.stderr)
            return 1
        print(f"marked {run_dir.as_posix()} as failed", file=sys.stderr)
        return 0

    # Normal validation path.
    if meta.get("status") == "complete":
        print(
            f"error: run already validated as complete: {run_dir.as_posix()}",
            file=sys.stderr,
        )
        return 1

    file_errors = check_mandatory_files(run_dir)
    if file_errors:
        for err in file_errors:
            print(f"error: {err}", file=sys.stderr)
        try_finalize_failed(run_dir, empty_counts(), "; ".join(file_errors))
        return 1

    counts, parse_errors = parse_searches_jsonl(run_dir)
    if parse_errors:
        for err in parse_errors:
            print(f"error: {err}", file=sys.stderr)
        try_finalize_failed(run_dir, counts, "; ".join(parse_errors[:3]))
        return 1

    for w in check_recommended_files(run_dir):
        print(f"warning: {w}", file=sys.stderr)

    try:
        finalize_meta(run_dir, meta, counts, status="complete", error=None)
    except OSError as e:
        print(f"error: failed to write meta.json: {e}", file=sys.stderr)
        return 1

    summary = {
        "run_id": meta.get("run_id"),
        "status": "complete",
        "query_count": counts["query_count"],
        "result_count": counts["result_count"],
        "fetch_count": counts["fetch_count"],
        "fetch_error_count": counts["fetch_error_count"],
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
