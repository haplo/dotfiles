#!/usr/bin/env python3
"""Download and update opencode skills from GitHub repositories.

Usage:
  skill-downloader.py                              Print help
  skill-downloader.py <url> [--ref main]           Add skills from a GitHub repo
  skill-downloader.py -u [namespace]               Update installed skills

Each namespace (skills/<namespace>/) gets a .source.json file describing where
the skills came from and which directories are installed or ignored.

.source.json format:
{
  "type": "github-dir",
  "repo": "owner/repo",
  "ref": "main",
  "path": "skills/",
  "dirs": ["engineering/tdd/", ...],
  "ignore": ["misc/some-skill/", ...]
}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

SKILLS_DIR = Path("~/.config/opencode/skills").expanduser()

SOURCE_FILENAME = ".source.json"


# ---------------------------------------------------------------------------
# URL parsing
# ---------------------------------------------------------------------------

def parse_github_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL or owner/repo shorthand.

    Supports:
      https://github.com/owner/repo
      https://github.com/owner/repo.git
      https://github.com/owner/repo/tree/main
      git@github.com:owner/repo.git
      owner/repo
    """
    # SSH form: git@github.com:owner/repo.git
    m = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", url)
    if m:
        return m.group(1), m.group(2)

    # HTTPS form
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$", url)
    if m:
        return m.group(1), m.group(2)

    # owner/repo shorthand
    m = re.match(r"^([^/\s]+)/([^/\s]+)$", url)
    if m:
        return m.group(1), m.group(2)

    raise ValueError(f"Could not parse GitHub URL: {url}")


# ---------------------------------------------------------------------------
# Tarball download / extraction
# ---------------------------------------------------------------------------

def download_tarball(owner: str, repo: str, ref: str, dest: Path) -> None:
    """Download a repo tarball and extract it into *dest* (stripping the top-level dir)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/tarball/{ref}"
    print(f"  Downloading {url} ...")
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        urllib.request.urlretrieve(url, tmp_path)
        with tarfile.open(tmp_path, "r:gz") as tar:
            members = tar.getmembers()
            if not members:
                raise RuntimeError("Tarball is empty")
            # Top-level directory name (e.g. owner-repo-abcdef/)
            top = members[0].name.split("/")[0]
            for member in members:
                if member.name == top:
                    continue
                # Strip the top-level prefix
                member.name = member.name[len(top) + 1:]
                if member.name:
                    tar.extract(member, dest)
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Skill discovery
# ---------------------------------------------------------------------------

def find_skill_dirs(root: Path) -> list[str]:
    """Return repo-relative paths to every directory containing a SKILL.md."""
    skills = []
    for skill_file in root.rglob("SKILL.md"):
        rel = skill_file.parent.relative_to(root)
        skills.append(rel.as_posix() + "/")
    skills.sort()
    return skills


def common_prefix(paths: list[str]) -> str:
    """Find the longest common path prefix among *paths* (path components)."""
    if not paths:
        return ""
    split_paths = [p.split("/") for p in paths]
    prefix_parts = []
    for parts in zip(*split_paths):
        if all(p == parts[0] for p in parts):
            prefix_parts.append(parts[0])
        else:
            break
    # Keep trailing component if it's a real directory segment (not the skill name)
    prefix = "/".join(prefix_parts)
    # Ensure it ends with /
    if prefix and not prefix.endswith("/"):
        prefix += "/"
    return prefix


# ---------------------------------------------------------------------------
# .source.json read / write
# ---------------------------------------------------------------------------

def read_source(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def write_source(path: Path, data: dict) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


# ---------------------------------------------------------------------------
# File syncing
# ---------------------------------------------------------------------------

def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sync_skill_dir(
    upstream_dir: Path,
    local_dir: Path,
    *,
    dry_run: bool = False,
) -> list[str]:
    """Sync *local_dir* to match *upstream_dir*. Returns list of changed file names."""
    changed: list[str] = []

    upstream_files: dict[str, str] = {}
    for f in upstream_dir.rglob("*"):
        if f.is_file() and f.name != ".source.json":
            rel = f.relative_to(upstream_dir).as_posix()
            upstream_files[rel] = file_sha256(f)

    local_files: set[str] = set()
    for f in local_dir.rglob("*"):
        if f.is_file() and f.name != ".source.json":
            local_files.add(f.relative_to(local_dir).as_posix())

    # Copy new/changed files
    for rel, sha in upstream_files.items():
        local_path = local_dir / rel
        local_path.parent.mkdir(parents=True, exist_ok=True)
        if not local_path.exists() or file_sha256(local_path) != sha:
            if not dry_run:
                shutil.copy2(upstream_dir / rel, local_path)
            changed.append(rel)

    # Remove files that no longer exist upstream
    for rel in local_files - set(upstream_files.keys()):
        if not dry_run:
            (local_dir / rel).unlink()
        changed.append(f"deleted: {rel}")

    # Remove empty directories
    if not dry_run:
        for d in sorted(local_dir.rglob("*"), reverse=True):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()

    return changed


# ---------------------------------------------------------------------------
# Interactive prompts
# ---------------------------------------------------------------------------

def prompt_select(items: list[str], prompt: str) -> set[int]:
    """Display a numbered list and let the user pick entries.

    Returns a set of selected indices (0-based).
    """
    if not items:
        return set()

    for i, item in enumerate(items, 1):
        print(f"  {i:3d}. {item}")

    while True:
        answer = input(f"\n{prompt} (e.g. 1,3,5-10 / all / none): ").strip().lower()
        if answer == "all":
            return set(range(len(items)))
        if answer == "none" or answer == "":
            return set()

        try:
            selected: set[int] = set()
            for part in answer.split(","):
                part = part.strip()
                if "-" in part:
                    lo, hi = part.split("-", 1)
                    selected.update(range(int(lo) - 1, int(hi)))
                else:
                    selected.add(int(part) - 1)
            if all(0 <= i < len(items) for i in selected):
                return selected
        except ValueError:
            pass
        print("  Invalid input. Try again.")


# ---------------------------------------------------------------------------
# Add command
# ---------------------------------------------------------------------------

def cmd_add(url: str, ref: str, namespace: str | None) -> None:
    owner, repo = parse_github_url(url)
    ns = namespace or owner

    ns_dir = SKILLS_DIR / ns
    source_path = ns_dir / SOURCE_FILENAME

    if source_path.exists():
        print(f"Namespace '{ns}' already has a .source.json at {source_path}")
        print("Use the update command instead: skill-downloader.py -u", ns)
        return

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        download_tarball(owner, repo, ref, tmp_dir)

        all_skill_paths = find_skill_dirs(tmp_dir)
        if not all_skill_paths:
            print("No skills (SKILL.md files) found in this repository.")
            return

        # Determine the common path prefix, then strip it so dirs are relative
        path_prefix = common_prefix(all_skill_paths)
        all_skills = []
        for s in all_skill_paths:
            if path_prefix and s.startswith(path_prefix):
                all_skills.append(s[len(path_prefix):])
            else:
                all_skills.append(s)
        all_skills.sort()

        print(f"\nFound {len(all_skills)} skill(s) in {owner}/{repo}:\n")
        selected = prompt_select(all_skills, "Select skills to install")

        if not selected:
            print("No skills selected. Nothing to do.")
            return

        dirs = sorted(all_skills[i] for i in selected)
        ignore = sorted(all_skills[i] for i in range(len(all_skills)) if i not in selected)

        # Create namespace dir and copy selected skills
        ns_dir.mkdir(parents=True, exist_ok=True)

        for d in dirs:
            src = tmp_dir / (path_prefix + d)
            dst = ns_dir / d
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  Installed: {d}")

        write_source(source_path, {
            "type": "github-dir",
            "repo": f"{owner}/{repo}",
            "ref": ref,
            "path": path_prefix,
            "dirs": dirs,
            "ignore": ignore,
        })

        print(f"\nDone. {len(dirs)} skill(s) installed to {ns_dir}")
        print(f"Source file: {source_path}")
        if ignore:
            print(f"  {len(ignore)} skill(s) marked as ignored")


# ---------------------------------------------------------------------------
# Update command
# ---------------------------------------------------------------------------

def cmd_update(namespace: str | None) -> None:
    if not SKILLS_DIR.exists():
        print("No skills directory found.")
        return

    # Find all .source.json files
    source_files = sorted(SKILLS_DIR.glob("*/" + SOURCE_FILENAME))
    if not source_files:
        print("No .source.json files found.")
        return

    if namespace:
        source_files = [f for f in source_files if f.parent.name == namespace]
        if not source_files:
            print(f"No .source.json found for namespace '{namespace}'.")
            return

    for source_path in source_files:
        ns = source_path.parent.name
        print(f"\n{'=' * 60}")
        print(f"Updating namespace: {ns}")
        print(f"{'=' * 60}")

        data = read_source(source_path)
        source_type = data.get("type", "")
        if source_type != "github-dir":
            print(f"  Unknown type '{source_type}', skipping.")
            continue

        repo = data["repo"]
        ref = data.get("ref", "main")
        path_prefix = data.get("path", "")
        dirs = data.get("dirs", [])
        ignore = data.get("ignore", [])

        owner, repo_name = repo.split("/", 1)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            try:
                download_tarball(owner, repo_name, ref, tmp_dir)
            except Exception as e:
                print(f"  Failed to download: {e}")
                continue

            upstream_skills = find_skill_dirs(tmp_dir)

            # Normalize: strip path_prefix if present
            upstream_relative = []
            for s in upstream_skills:
                if path_prefix and s.startswith(path_prefix):
                    upstream_relative.append(s[len(path_prefix):])
                else:
                    upstream_relative.append(s)
            upstream_relative.sort()

            existing = set(dirs) | set(ignore)
            new_skills = [s for s in upstream_relative if s not in existing]

            # Prompt for new skills
            new_dirs: list[str] = []
            new_ignore: list[str] = []
            if new_skills:
                print(f"\n  {len(new_skills)} new skill(s) found upstream:\n")
                selected = prompt_select(new_skills, "  Select new skills to install")
                new_dirs = sorted(new_skills[i] for i in selected)
                new_ignore = sorted(new_skills[i] for i in range(len(new_skills)) if i not in selected)

                # Copy newly selected skills
                for d in new_dirs:
                    src = tmp_dir / (path_prefix + d)
                    dst = source_path.parent / d
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    print(f"  Installed: {d}")

            # Sync existing dirs
            all_dirs = dirs + new_dirs
            synced_count = 0
            for d in all_dirs:
                src = tmp_dir / (path_prefix + d)
                dst = source_path.parent / d
                if not src.exists():
                    print(f"  WARNING: '{d}' no longer exists upstream. Keeping local copy.")
                    continue
                if not dst.exists():
                    print(f"  WARNING: '{d}' is in .source.json but not installed locally. Copying from upstream.")
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(src, dst)
                    continue
                changed = sync_skill_dir(src, dst)
                if changed:
                    synced_count += 1
                    print(f"  Updated: {d} ({len(changed)} file(s))")
                    for c in changed:
                        print(f"    {c}")

            # Detect dirs/ignore entries that disappeared upstream
            upstream_set = set(upstream_relative)
            stale_dirs = [d for d in all_dirs if d not in upstream_set]
            stale_ignore = [d for d in ignore if d not in upstream_set]
            for d in stale_dirs:
                print(f"  WARNING: '{d}' no longer exists upstream. Keeping local copy, removing from .source.json.")
            for d in stale_ignore:
                print(f"  NOTE: '{d}' (ignored) no longer exists upstream. Removing from .source.json.")

            # Rewrite .source.json
            updated_dirs = sorted(set(all_dirs) - set(stale_dirs))
            updated_ignore = sorted((set(ignore) | set(new_ignore)) - set(stale_ignore))

            write_source(source_path, {
                "type": "github-dir",
                "repo": data["repo"],
                "ref": ref,
                "path": path_prefix,
                "dirs": updated_dirs,
                "ignore": updated_ignore,
            })

            print(f"\n  Synced {synced_count} skill(s).")
            if new_dirs:
                print(f"  Added {len(new_dirs)} new skill(s).")
            if stale_dirs or stale_ignore:
                print(f"  Removed {len(stale_dirs) + len(stale_ignore)} stale entr(ies).")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skill-downloader.py",
        description="Download and update opencode skills from GitHub repositories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  skill-downloader.py https://github.com/mattpocock/skills
  skill-downloader.py mattpocock/skills --ref dev
  skill-downloader.py -u                    # update all namespaces
  skill-downloader.py -u mattpocock         # update only the mattpocock namespace
""",
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="GitHub URL or owner/repo shorthand to add skills from",
    )
    parser.add_argument(
        "-u", "--update",
        action="store_true",
        help="Update installed skills (optionally filter by namespace)",
    )
    parser.add_argument(
        "--ref",
        default="main",
        help="Branch, tag, or commit to fetch (default: main)",
    )
    parser.add_argument(
        "--namespace",
        help="Override the namespace directory name (default: GitHub owner name)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.update:
        # When updating, positional arg (if any) is the namespace
        ns = args.url  # argparse puts it in 'url' since it's positional
        cmd_update(ns)
        return 0

    if not args.url:
        parser.print_help()
        return 0

    cmd_add(args.url, args.ref, args.namespace)
    return 0


if __name__ == "__main__":
    sys.exit(main())
