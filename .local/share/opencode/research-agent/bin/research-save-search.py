#!/usr/bin/env python3
"""
research-save-search: Log a web search into a research run's searches.jsonl.

Appends a single "search" entry to <run-dir>/searches.jsonl, recording the
query and its results. The run must exist and still be "running".

Usage:
  research-save-search <run-dir> --query "<query>" \\
                       --results '[{"title": "...", "url": "...", "snippet": "..."}, ...]'
  research-save-search <run-dir> --query "<query>" \\
                       --results-file results.json
  research-save-search <run-dir> --query "<query>" \\
                       --firecrawl-file firecrawl-output.json

Exactly one of --results, --results-file, or --firecrawl-file must be provided.
With --results-file, the named file is read and used as the results array. With
--firecrawl-file, the named file is parsed as raw `firecrawl search` output and
each web result is mapped to the results array (its "description" becomes the
"snippet").

Each result must be a JSON object with non-empty "title", "url", and "snippet".

Exit codes:
  0  success; search entry appended to searches.jsonl
  1  validation or filesystem error
  2  invalid arguments
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RESULT_FIELDS = ("title", "url", "snippet")


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def load_meta(run_dir: Path) -> dict:
    meta_path = run_dir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError("meta.json not found")
    with meta_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_results(data: list, label: str) -> list[dict]:
    """Validate a list of result objects.

    Returns the normalized list of result objects, or raises ValueError with a
    human-readable message (prefixed with ``label``) describing the first
    problem found.
    """
    normalized: list[dict] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"{label}[{i}] is not a JSON object")
        result = {}
        for field in RESULT_FIELDS:
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{label}[{i}] missing or empty '{field}' (string required)"
                )
            result[field] = value
        normalized.append(result)
    return normalized


def parse_results(raw: str) -> list[dict]:
    """Parse and validate the --results JSON array.

    Returns the normalized list of result objects, or raises ValueError with a
    human-readable message describing the first problem found.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"--results is not valid JSON: {e.msg}")

    if not isinstance(data, list):
        raise ValueError("--results must be a JSON array")

    return validate_results(data, "--results")


def parse_firecrawl(raw: str) -> list[dict]:
    """Parse raw `firecrawl search` output into the results array.

    Navigates to ``data.web`` and maps each item's "description" to "snippet".
    Raises ValueError with a human-readable message on any problem.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"--firecrawl-file is not valid JSON: {e.msg}")

    if not isinstance(data, dict):
        raise ValueError("--firecrawl-file must be a JSON object")

    payload = data.get("data")
    if not isinstance(payload, dict):
        raise ValueError("--firecrawl-file missing 'data' object")

    web = payload.get("web")
    if not isinstance(web, list):
        raise ValueError("--firecrawl-file missing 'data.web' array")

    mapped: list[dict] = []
    for i, item in enumerate(web):
        if not isinstance(item, dict):
            raise ValueError(f"--firecrawl-file 'data.web'[{i}] is not a JSON object")
        mapped.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "snippet": item.get("description"),
            }
        )

    return validate_results(mapped, "--firecrawl-file")


def append_entry(run_dir: Path, entry: dict) -> None:
    path = run_dir / "searches.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False))
        f.write("\n")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="research-save-search",
        description="Log a web search into a research run's searches.jsonl.",
    )
    parser.add_argument(
        "run_dir",
        help="Path to the run directory (e.g. <research-dir>/runs/<run-id>).",
    )
    parser.add_argument(
        "--query",
        required=True,
        help="The full search query string.",
    )
    results_group = parser.add_mutually_exclusive_group(required=True)
    results_group.add_argument(
        "--results",
        help='JSON array of result objects, each with "title", "url", '
        'and "snippet".',
    )
    results_group.add_argument(
        "--results-file",
        help="Path to a file containing the JSON array of result objects "
        "(alternative to --results).",
    )
    results_group.add_argument(
        "--firecrawl-file",
        help="Path to a file containing raw `firecrawl search` output; its web "
        "results are mapped into the results array (alternative to --results).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    run_dir = Path(args.run_dir)

    if not run_dir.is_dir():
        print(f"error: not a directory: {run_dir}", file=sys.stderr)
        return 1

    try:
        meta = load_meta(run_dir)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: failed to read meta.json: {e}", file=sys.stderr)
        return 1

    status = meta.get("status")
    if status != "running":
        print(
            f"error: run is not running (status: {status!r}): {run_dir.as_posix()}",
            file=sys.stderr,
        )
        return 1

    if not args.query.strip():
        print("error: --query must not be empty", file=sys.stderr)
        return 2

    if args.firecrawl_file is not None:
        try:
            raw_results = Path(args.firecrawl_file).read_text(encoding="utf-8")
        except OSError as e:
            print(f"error: failed to read firecrawl file: {e}", file=sys.stderr)
            return 2
        parser_fn = parse_firecrawl
    elif args.results_file is not None:
        try:
            raw_results = Path(args.results_file).read_text(encoding="utf-8")
        except OSError as e:
            print(f"error: failed to read results file: {e}", file=sys.stderr)
            return 2
        parser_fn = parse_results
    else:
        raw_results = args.results
        parser_fn = parse_results

    try:
        results = parser_fn(raw_results)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    entry = {
        "type": "search",
        "timestamp": utc_now_iso(),
        "query": args.query,
        "results": results,
    }

    try:
        append_entry(run_dir, entry)
    except OSError as e:
        print(f"error: failed to write searches.jsonl: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
