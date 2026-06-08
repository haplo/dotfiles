#!/usr/bin/env python3
"""
research-run-init: Initialize a research run directory.

Creates `<dir>/<run-id>/` with an initial meta.json and prints the
path to the created directory on stdout.

Run ID format: YYYYMMDD-HHMMSS-<slug>
On collision (same second, same slug): retries with a short random suffix.

Usage:
  research-run-init --dir <dir> --slug <slug> \\
                    --user-prompt "<user's prompt to the researcher>" \\
                    --researcher-prompt "<researcher goal from user and notes>"

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


def create_run_dir(base_dir: Path, slug: str) -> Path:
    for attempt in range(MAX_COLLISION_RETRIES):
        suffix = secrets.token_hex(2) if attempt > 0 else ""
        run_id = build_run_id(slug, suffix)
        run_dir = base_dir / run_id
        try:
            run_dir.mkdir(parents=False, exist_ok=False)
            # create pages directory
            pages_dir = run_dir / "pages"
            pages_dir.mkdir(parents=False, exist_ok=False)
            return run_dir
        except FileExistsError:
            continue
    raise RuntimeError(
        f"failed to create unique run directory after {MAX_COLLISION_RETRIES} attempts"
    )


def write_initial_meta(run_dir: Path, user_prompt: str, researcher_prompt: str) -> None:
    meta = {
        "run_id": run_dir.name,
        "created_at": utc_now_iso(),
        "finalized_at": None,
        "user_prompt": user_prompt,
        "researcher_prompt": researcher_prompt,
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
        "--dir",
        required=True,
        help="Existing directory under which the run subdirectory is created.",
    )
    parser.add_argument(
        "--slug",
        required=True,
        help="Short kebab-case identifier for the research topic.",
    )
    parser.add_argument(
        "--user-prompt",
        required=True,
        help="The user's prompt to the researcher agent.",
    )
    parser.add_argument(
        "--researcher-prompt",
        required=True,
        help="The researcher goal derived from the user's prompt and notes.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    base_dir = Path(args.dir)
    if not base_dir.exists():
        print(f"error: --dir does not exist: {base_dir}", file=sys.stderr)
        return 2
    if not base_dir.is_dir():
        print(f"error: --dir is not a directory: {base_dir}", file=sys.stderr)
        return 2

    # Ensure run directories always live inside a runs/ subdirectory.
    if base_dir.name != "runs":
        base_dir = base_dir / "runs"
    try:
        base_dir.mkdir(parents=False, exist_ok=True)
    except OSError as e:
        print(f"error: failed to create runs directory: {e}", file=sys.stderr)
        return 1

    try:
        slug = sanitize_slug(args.slug)
    except ValueError as e:
        print(f"error: invalid slug: {e}", file=sys.stderr)
        return 2

    if not args.user_prompt.strip():
        print("error: --user-prompt must not be empty", file=sys.stderr)
        return 2

    if not args.researcher_prompt.strip():
        print("error: --researcher-prompt must not be empty", file=sys.stderr)
        return 2

    try:
        run_dir = create_run_dir(base_dir, slug)
    except (OSError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        write_initial_meta(run_dir, args.user_prompt, args.researcher_prompt)
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
