#!/usr/bin/env python3
"""
research-save-page: Log a page fetch into a research run's searches.jsonl.

Appends a single "fetch" entry to <run-dir>/searches.jsonl, recording either a
successful fetch (with the saved file under pages/) or a failed one (with an
error message). The run must exist and still be "running".

Usage:
  research-save-page <run-dir> --url "<URL>" --file "<name>" --ok
  research-save-page <run-dir> --url "<URL>" --error "<message>"

Exactly one of --ok or --error must be provided.
  --ok     requires --file; the file must exist (non-empty) under pages/.
  --error  must not be used with --file.

Exit codes:
  0  success; fetch entry appended to searches.jsonl
  1  validation or filesystem error
  2  invalid arguments
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

PAGES_DIR = "pages"
VALID_URL_SCHEMES = ("http", "https")


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


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme in VALID_URL_SCHEMES and bool(parsed.netloc)


def append_entry(run_dir: Path, entry: dict) -> None:
    path = run_dir / "searches.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False))
        f.write("\n")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="research-save-page",
        description="Log a page fetch into a research run's searches.jsonl.",
    )
    parser.add_argument(
        "run_dir",
        help="Path to the run directory (e.g. <research-dir>/runs/<run-id>).",
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Full, unencoded URL that was fetched.",
    )
    parser.add_argument(
        "--file",
        help="Filename of the saved page inside the run's pages/ directory "
        "(required with --ok, forbidden with --error).",
    )
    outcome = parser.add_mutually_exclusive_group(required=True)
    outcome.add_argument(
        "--ok",
        action="store_true",
        help="Record a successful fetch.",
    )
    outcome.add_argument(
        "--error",
        metavar="MESSAGE",
        help="Record a failed fetch with the given error message.",
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

    if not is_valid_url(args.url):
        print(f"error: invalid URL: {args.url!r}", file=sys.stderr)
        return 1

    if args.ok:
        if not args.file:
            print("error: --file is required with --ok", file=sys.stderr)
            return 2

        page_path = run_dir / PAGES_DIR / args.file
        if not page_path.is_file():
            print(
                f"error: file not found in {PAGES_DIR}/: {args.file}",
                file=sys.stderr,
            )
            return 1

        byte_count = page_path.stat().st_size
        if byte_count == 0:
            print(
                f"error: file is empty: {PAGES_DIR}/{args.file}",
                file=sys.stderr,
            )
            return 1

        entry = {
            "type": "fetch",
            "timestamp": utc_now_iso(),
            "url": args.url,
            "status": "ok",
            "file": args.file,
            "byte_count": byte_count,
        }
    else:  # --error
        if args.file is not None:
            print("error: --file cannot be used with --error", file=sys.stderr)
            return 2

        error_msg = args.error.strip()
        if not error_msg:
            print("error: --error message must not be empty", file=sys.stderr)
            return 2

        entry = {
            "type": "fetch",
            "timestamp": utc_now_iso(),
            "url": args.url,
            "status": "error",
            "error": error_msg,
        }

    try:
        append_entry(run_dir, entry)
    except OSError as e:
        print(f"error: failed to write searches.jsonl: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
