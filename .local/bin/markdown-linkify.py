#!/usr/bin/env python3
"""Convert plain .md file references in markdown files to relative links.

Scans all .md files in the repository recursively, finds references to .md
files that are not already Markdown links, and converts them to relative links.

- Backtick references like `file.md` become [`file.md`](file.md)
- Plain text references like file.md become [file.md](file.md)
- Backtick directory references like `dir/` become [`dir/`](dir/) if the directory exists
- Plain text directory references like dir/ become [dir/](dir/) if the directory exists
- References to non-existent files are left unchanged with a stderr warning
- Directory references to non-existent directories are left unchanged (no warning,
  since trailing slashes are common in prose)
- Fenced code blocks and YAML frontmatter are skipped
- Files can be excluded with -e/--exclude GLOB (repeatable, anchored at the
  scanned directory; * matches one level, ** matches multiple levels). If -e
  is not given, patterns are read from MARKDOWN_LINKIFY_EXCLUDE (|-separated)
- -v prints each parsed file; -vv also prints each updated line as
  file:LINE  <updated line>
- -n/--dry-run writes no changes (useful combined with -v)
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

# Matches backtick-enclosed directory references: `dir/`, `path/to/dir/`
BACKTICK_DIR_RE = re.compile(r'`((?:[\w-]+/)+)`')

# Matches plain text directory references (not in backticks): dir/, path/to/dir/
PLAIN_DIR_RE = re.compile(r'(?<![\w`/])((?:[\w-]+/)+)(?![\w])')

SKIP_DIRS = {'.git', '.firecrawl', '__pycache__', 'tmp', '.opencode'}


def glob_to_regex(pattern):
    """Translate a glob pattern to a compiled regex, anchored at both ends.

    * and ? match within a path segment; ** matches across segments;
    **/ also matches zero directories (so **/x.md matches ./x.md too).
    """
    if pattern.startswith('./'):
        pattern = pattern[2:]
    i, n = 0, len(pattern)
    out = []
    while i < n:
        c = pattern[i]
        if c == '*':
            if pattern[i:i + 2] == '**':
                while i < n and pattern[i] == '*':
                    i += 1
                if pattern[i:i + 1] == '/':
                    out.append('(?:.*/)?')
                    i += 1
                else:
                    out.append('.*')
            else:
                out.append('[^/]*')
                i += 1
        elif c == '?':
            out.append('[^/]')
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile('^' + ''.join(out) + '$')


def is_excluded(relpath, matchers):
    return any(m.match(relpath) for m in matchers)


def is_url(s):
    return s.startswith(('http://', 'https://', 'ftp://'))


def has_filename(ref):
    """Return True if the reference has a real filename, not just '.md'."""
    path = ref.split('#')[0]
    basename = os.path.basename(path)
    return bool(re.match(r'\w', basename))


def resolve_file(repo_root, source_dir, ref):
    """Return the full path of the referenced file if it exists, else None."""
    path = ref.split('#')[0]
    for base in (source_dir, repo_root):
        full = os.path.normpath(os.path.join(base, path))
        if os.path.isfile(full):
            return full
    return None


def dir_exists(repo_root, source_dir, ref):
    """Check if the referenced directory exists relative to source dir or repo root."""
    path = ref.rstrip('/')
    for base in (source_dir, repo_root):
        full = os.path.normpath(os.path.join(base, path))
        if os.path.isdir(full):
            return True
    return False


def find_ranges(line, pattern):
    return [(m.start(), m.end()) for m in pattern.finditer(line)]


def in_ranges(pos, ranges):
    return any(s <= pos < e for s, e in ranges)


def process_file(filepath, repo_root, verbose=0, dry_run=False):
    source_dir = os.path.dirname(filepath)
    relpath = os.path.relpath(filepath, repo_root)
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

        original_line = line

        # --- Process backtick-enclosed .md references ---
        link_ranges = find_ranges(line, LINK_RE)
        replacements = []

        for m in BACKTICK_RE.finditer(line):
            ref = m.group(1)
            if is_url(ref) or not has_filename(ref):
                continue
            if in_ranges(m.start(), link_ranges):
                continue
            resolved = resolve_file(repo_root, source_dir, ref)
            if resolved is not None:
                if resolved == os.path.normpath(filepath) and '#' not in ref:
                    continue
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
            resolved = resolve_file(repo_root, source_dir, ref)
            if resolved is not None:
                if resolved == os.path.normpath(filepath) and '#' not in ref:
                    continue
                replacements.append((m.start(), m.end(), f'[{ref}]({ref})'))
                count += 1
            else:
                print(f"Warning: {os.path.relpath(filepath, repo_root)}:{line_num}: "
                      f"file not found: {ref}", file=sys.stderr)
                print(f"  {line.rstrip()}", file=sys.stderr)

        for start, end, repl in sorted(replacements, key=lambda x: -x[0]):
            line = line[:start] + repl + line[end:]

        # --- Process backtick-enclosed directory references ---
        link_ranges = find_ranges(line, LINK_RE)
        replacements = []

        for m in BACKTICK_DIR_RE.finditer(line):
            ref = m.group(1)
            if is_url(ref):
                continue
            if in_ranges(m.start(), link_ranges):
                continue
            if dir_exists(repo_root, source_dir, ref):
                replacements.append((m.start(), m.end(), f'[`{ref}`]({ref})'))
                count += 1

        for start, end, repl in sorted(replacements, key=lambda x: -x[0]):
            line = line[:start] + repl + line[end:]

        # --- Process plain text directory references ---
        link_ranges = find_ranges(line, LINK_RE)
        backtick_ranges = find_ranges(line, BACKTICK_SPAN_RE)
        replacements = []

        for m in PLAIN_DIR_RE.finditer(line):
            ref = m.group(1)
            if is_url(ref):
                continue
            if in_ranges(m.start(), link_ranges) or in_ranges(m.start(), backtick_ranges):
                continue
            if dir_exists(repo_root, source_dir, ref):
                replacements.append((m.start(), m.end(), f'[{ref}]({ref})'))
                count += 1

        for start, end, repl in sorted(replacements, key=lambda x: -x[0]):
            line = line[:start] + repl + line[end:]

        if verbose >= 2 and line != original_line:
            print(f"{relpath}:{line_num}  {line.rstrip()}")

        new_lines.append(line)

    if count > 0 and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return count


def main():
    parser = argparse.ArgumentParser(
        description='Convert plain .md file references in markdown files to relative links.',
        epilog='If -e is not given, exclude patterns are read from the '
               'MARKDOWN_LINKIFY_EXCLUDE environment variable (|-separated).')
    parser.add_argument('directory', nargs='?',
        help='Repository root directory to scan (default: current working directory).')
    parser.add_argument('-e', '--exclude', action='append', default=[], metavar='GLOB',
        help='Glob pattern of files to exclude, anchored at the scanned directory '
             '(* = one level, ** = multiple levels); may be given multiple times.')
    parser.add_argument('-v', '--verbose', action='count', default=0,
        help='Print each parsed file; use -vv to also print each updated line.')
    parser.add_argument('-n', '--dry-run', action='store_true',
        help='Write no changes; useful combined with -v to see what would change.')
    args = parser.parse_args()

    repo_root = args.directory if args.directory else os.getcwd()
    if not os.path.isdir(repo_root):
        parser.error(f"not a directory: {repo_root}")
    repo_root = os.path.abspath(repo_root)

    patterns = args.exclude
    if not patterns:
        patterns = os.environ.get('MARKDOWN_LINKIFY_EXCLUDE', '').split('|')
    matchers = [glob_to_regex(p) for p in (p.strip() for p in patterns) if p]

    total = 0

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if not f.endswith('.md'):
                continue
            filepath = os.path.join(root, f)
            relpath = os.path.relpath(filepath, repo_root)
            if is_excluded(relpath, matchers):
                continue
            if args.verbose >= 1:
                print(relpath)
            total += process_file(filepath, repo_root, verbose=args.verbose,
                                  dry_run=args.dry_run)

    suffix = ' (dry run, no files written)' if args.dry_run else ''
    print(f"Total references converted: {total}{suffix}")


if __name__ == '__main__':
    main()
