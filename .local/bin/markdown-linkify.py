#!/usr/bin/env python3
"""Convert plain .md file references in markdown files to relative links.

Scans all .md files in the repository recursively, finds references to .md
files that are not already Markdown links, and converts them to relative links.

- Backtick references like `file.md` become [`file.md`](file.md)
- Plain text references like file.md become [file.md](file.md)
- References to non-existent files are left unchanged with a stderr warning
- Fenced code blocks and YAML frontmatter are skipped
- Quiet on success; prints total converted references at the end
"""

import argparse
import os
import re
import sys

# Matches existing Markdown links: [text](target)
LINK_RE = re.compile(r'\[([^\]]*)\]\([^)]*\)')

# Matches backtick-enclosed .md references: `file.md`, `path/to/file.md#anchor`
BACKTICK_RE = re.compile(r'`([^`]*\.md(?:#[^`]*)?)`')

# Matches any backtick span (to protect plain-text refs inside inline code)
BACKTICK_SPAN_RE = re.compile(r'`[^`]*`')

# Matches plain text .md references (not in backticks): file.md, dir/file.md#anchor
PLAIN_MD_RE = re.compile(r'(?<![\w`/])((?:[\w-]+/)*[\w-]+\.md(?:#[^\s)\]]+)?)(?![\w])')

SKIP_DIRS = {'.git', '.firecrawl', '__pycache__', 'tmp', '.opencode'}


def is_url(s):
    return s.startswith(('http://', 'https://', 'ftp://'))


def has_filename(ref):
    """Return True if the reference has a real filename, not just '.md'."""
    path = ref.split('#')[0]
    basename = os.path.basename(path)
    return bool(re.match(r'\w', basename))


def file_exists(repo_root, source_dir, ref):
    """Check if the referenced file exists relative to source dir or repo root."""
    path = ref.split('#')[0]
    for base in (source_dir, repo_root):
        full = os.path.normpath(os.path.join(base, path))
        if os.path.isfile(full):
            return True
    return False


def find_ranges(line, pattern):
    return [(m.start(), m.end()) for m in pattern.finditer(line)]


def in_ranges(pos, ranges):
    return any(s <= pos < e for s, e in ranges)


def process_file(filepath, repo_root):
    source_dir = os.path.dirname(filepath)
    count = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_code_block = False
    in_frontmatter = False
    new_lines = []
    first_line = True

    for line_num, line in enumerate(lines, 1):
        # --- Handle YAML frontmatter (skip it entirely) ---
        if first_line:
            first_line = False
            if line.strip() == '---':
                in_frontmatter = True
                new_lines.append(line)
                continue
        if in_frontmatter:
            if line.strip() == '---':
                in_frontmatter = False
            new_lines.append(line)
            continue

        # --- Handle fenced code blocks ---
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            new_lines.append(line)
            continue
        if in_code_block:
            new_lines.append(line)
            continue

        # --- Process backtick-enclosed .md references ---
        link_ranges = find_ranges(line, LINK_RE)
        replacements = []

        for m in BACKTICK_RE.finditer(line):
            ref = m.group(1)
            if is_url(ref) or not has_filename(ref):
                continue
            if in_ranges(m.start(), link_ranges):
                continue
            if file_exists(repo_root, source_dir, ref):
                replacements.append((m.start(), m.end(), f'[`{ref}`]({ref})'))
                count += 1
            else:
                print(f"Warning: {os.path.relpath(filepath, repo_root)}:{line_num}: "
                      f"file not found: {ref}", file=sys.stderr)
                print(f"  {line.rstrip()}", file=sys.stderr)

        for start, end, repl in sorted(replacements, key=lambda x: -x[0]):
            line = line[:start] + repl + line[end:]

        # --- Process plain text .md references ---
        link_ranges = find_ranges(line, LINK_RE)
        backtick_ranges = find_ranges(line, BACKTICK_SPAN_RE)
        replacements = []

        for m in PLAIN_MD_RE.finditer(line):
            ref = m.group(1)
            if is_url(ref) or not has_filename(ref):
                continue
            if in_ranges(m.start(), link_ranges) or in_ranges(m.start(), backtick_ranges):
                continue
            if file_exists(repo_root, source_dir, ref):
                replacements.append((m.start(), m.end(), f'[{ref}]({ref})'))
                count += 1
            else:
                print(f"Warning: {os.path.relpath(filepath, repo_root)}:{line_num}: "
                      f"file not found: {ref}", file=sys.stderr)
                print(f"  {line.rstrip()}", file=sys.stderr)

        for start, end, repl in sorted(replacements, key=lambda x: -x[0]):
            line = line[:start] + repl + line[end:]

        new_lines.append(line)

    if count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return count


def main():
    parser = argparse.ArgumentParser(
        description='Convert plain .md file references in markdown files to relative links.')
    parser.add_argument('directory', nargs='?',
        help='Repository root directory to scan (default: current working directory).')
    args = parser.parse_args()

    repo_root = args.directory if args.directory else os.getcwd()
    if not os.path.isdir(repo_root):
        parser.error(f"not a directory: {repo_root}")
    repo_root = os.path.abspath(repo_root)

    total = 0

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if f.endswith('.md'):
                total += process_file(os.path.join(root, f), repo_root)

    print(f"Total references converted: {total}")


if __name__ == '__main__':
    main()
