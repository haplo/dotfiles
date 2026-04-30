#!/usr/bin/env python3
"""
research-run-init: Initialize a research run directory.

Creates `.research/runs/<run-id>/` with an initial meta.json and prints the
relative path to the created directory on stdout.

Run ID format: YYYYMMDD-HHMMSS-<slug>
On collision (same second, same slug): retries with a short random suffix.

Usage:
  research-run-init --slug <slug> \\
                    --research-prompt "<user's prompt to the researcher>" \\
                    --searcher-prompt "<researcher's prompt to the searcher>"

Exit codes:
  0  success; run directory path printed to stdout
  1  filesystem or unexpected error
  2  invalid arguments
"""

import argparse
import json
import re
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

RUNS_DIR = Path(".research/runs")
SLUG_MAX_LENGTH = 40
MAX_COLLISION_RETRIES = 16


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def sanitize_slug(raw: str) -> str:
    s = raw.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    if len(s) > SLUG_MAX_LENGTH:
        s = s[:SLUG_MAX_LENGTH].rstrip("-")
    if not s:
        raise ValueError("slug is empty after sanitization")
    return s


def build_run_id(slug: str, collision_suffix: str = "") -> str:
    base = f"{utc_now_compact()}-{slug}"
    return f"{base}-{collision_suffix}" if collision_suffix else base


def create_run_dir(slug: str) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    for attempt in range(MAX_COLLISION_RETRIES):
        suffix = secrets.token_hex(2) if attempt > 0 else ""
        run_id = build_run_id(slug, suffix)
        run_dir = RUNS_DIR / run_id
        try:
            run_dir.mkdir(parents=False, exist_ok=False)
            return run_dir
        except FileExistsError:
            continue
    raise RuntimeError(
        f"failed to create unique run directory after {MAX_COLLISION_RETRIES} attempts"
    )


def write_initial_meta(
    run_dir: Path, research_prompt: str, searcher_prompt: str
) -> None:
    meta = {
        "run_id": run_dir.name,
        "created_at": utc_now_iso(),
        "finalized_at": None,
        "research_prompt": research_prompt,
        "searcher_prompt": searcher_prompt,
        "agent_model": None,
        "status": "running",
        "query_count": None,
        "result_count": None,
        "fetch_count": None,
        "fetch_error_count": None,
        "error": None,
    }
    meta_path = run_dir / "meta.json"
    tmp_path = meta_path.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp_path.replace(meta_path)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="research-run-init",
        description="Initialize a research run directory.",
    )
    parser.add_argument(
        "--slug",
        required=True,
        help="Short kebab-case identifier for the research topic.",
    )
    parser.add_argument(
        "--research-prompt",
        required=True,
        help="The user's prompt to the researcher agent.",
    )
    parser.add_argument(
        "--searcher-prompt",
        required=True,
        help="The researcher's delegation prompt to the web-searcher subagent.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    try:
        slug = sanitize_slug(args.slug)
    except ValueError as e:
        print(f"error: invalid slug: {e}", file=sys.stderr)
        return 2

    if not args.research_prompt.strip():
        print("error: --research-prompt must not be empty", file=sys.stderr)
        return 2
    if not args.searcher_prompt.strip():
        print("error: --searcher-prompt must not be empty", file=sys.stderr)
        return 2

    try:
        run_dir = create_run_dir(slug)
    except (OSError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        write_initial_meta(run_dir, args.research_prompt, args.searcher_prompt)
    except OSError as e:
        print(f"error: failed to write meta.json: {e}", file=sys.stderr)
        try:
            run_dir.rmdir()
        except OSError:
            pass
        return 1

    print(run_dir.as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())#!/usr/bin/env python3
"""
research-run-init: Initialize a research run directory.

Creates `.research/runs/<run-id>/` with an initial meta.json and prints the
relative path to the created directory on stdout.

Run ID format: YYYYMMDD-HHMMSS-<slug>
On collision (same second, same slug): retries with a short random suffix.

Usage:
  research-run-init --slug <slug> \\
                    --research-prompt "<user's prompt to the researcher>" \\
                    --searcher-prompt "<researcher's prompt to the searcher>"

Exit codes:
  0  success; run directory path printed to stdout
  1  filesystem or unexpected error
  2  invalid arguments
"""

import argparse
import json
import re
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

RUNS_DIR = Path(".research/runs")
SLUG_MAX_LENGTH = 40
MAX_COLLISION_RETRIES = 16


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def sanitize_slug(raw: str) -> str:
    s = raw.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    if len(s) > SLUG_MAX_LENGTH:
        s = s[:SLUG_MAX_LENGTH].rstrip("-")
    if not s:
        raise ValueError("slug is empty after sanitization")
    return s


def build_run_id(slug: str, collision_suffix: str = "") -> str:
    base = f"{utc_now_compact()}-{slug}"
    return f"{base}-{collision_suffix}" if collision_suffix else base


def create_run_dir(slug: str) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    for attempt in range(MAX_COLLISION_RETRIES):
        suffix = secrets.token_hex(2) if attempt > 0 else ""
        run_id = build_run_id(slug, suffix)
        run_dir = RUNS_DIR / run_id
        try:
            run_dir.mkdir(parents=False, exist_ok=False)
            return run_dir
        except FileExistsError:
            continue
    raise RuntimeError(
        f"failed to create unique run directory after {MAX_COLLISION_RETRIES} attempts"
    )


def write_initial_meta(
    run_dir: Path, research_prompt: str, searcher_prompt: str
) -> None:
    meta = {
        "run_id": run_dir.name,
        "created_at": utc_now_iso(),
        "finalized_at": None,
        "research_prompt": research_prompt,
        "searcher_prompt": searcher_prompt,
        "agent_model": None,
        "status": "running",
        "query_count": None,
        "result_count": None,
        "fetch_count": None,
        "fetch_error_count": None,
        "error": None,
    }
    meta_path = run_dir / "meta.json"
    tmp_path = meta_path.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp_path.replace(meta_path)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="research-run-init",
        description="Initialize a research run directory.",
    )
    parser.add_argument(
        "--slug",
        required=True,
        help="Short kebab-case identifier for the research topic.",
    )
    parser.add_argument(
        "--research-prompt",
        required=True,
        help="The user's prompt to the researcher agent.",
    )
    parser.add_argument(
        "--searcher-prompt",
        required=True,
        help="The researcher's delegation prompt to the web-searcher subagent.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    try:
        slug = sanitize_slug(args.slug)
    except ValueError as e:
        print(f"error: invalid slug: {e}", file=sys.stderr)
        return 2

    if not args.research_prompt.strip():
        print("error: --research-prompt must not be empty", file=sys.stderr)
        return 2
    if not args.searcher_prompt.strip():
        print("error: --searcher-prompt must not be empty", file=sys.stderr)
        return 2

    try:
        run_dir = create_run_dir(slug)
    except (OSError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        write_initial_meta(run_dir, args.research_prompt, args.searcher_prompt)
    except OSError as e:
        print(f"error: failed to write meta.json: {e}", file=sys.stderr)
        try:
            run_dir.rmdir()
        except OSError:
            pass
        return 1

    print(run_dir.as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
