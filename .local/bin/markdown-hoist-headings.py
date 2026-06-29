#!/usr/bin/env python3
"""Hoists headings up one level after the title heading.

Detects a single level-1 (ATX) heading, optionally after YAML frontmatter, decreases
every other heading level by one. Outputs to stdout by default, or overwrites the file
in place with --inplace.

"""

import argparse
import os
import re
import sys
import tempfile

ATX_HEADING_RE = re.compile(r"^( {0,3})(#{1,6})(\s|$)")
H1_RE = re.compile(r"^ {0,3}#(\s|$)")
FENCE_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})")
YAML_FENCE_RE = re.compile(r"^---[ \t]*$")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=(
            "Remove the title (single level-1) heading from a Markdown file "
            "and hoist the other headings up one level."
        ),
    )
    parser.add_argument("file", help="path to the Markdown file to process")
    parser.add_argument(
        "-i",
        "--inplace",
        action="store_true",
        help="overwrite the original file instead of writing to stdout",
    )
    return parser.parse_args(argv)


def split_frontmatter(text):
    """Split a document into (frontmatter, body).

    Frontmatter is returned including its closing fence (or empty string if
    there is none). The body is the remainder.
    """
    lines = text.splitlines(keepends=True)
    if not lines or not YAML_FENCE_RE.match(lines[0].rstrip("\r\n")):
        return "", text
    for i in range(1, len(lines)):
        if YAML_FENCE_RE.match(lines[i].rstrip("\r\n")):
            frontmatter = "".join(lines[: i + 1])
            body = "".join(lines[i + 1 :])
            return frontmatter, body
    # Opening fence never closed: treat whole document as body.
    return "", text


def find_h1_lines(body_lines):
    """Return indices of ATX level-1 heading lines, ignoring code blocks."""
    h1_indices = []
    in_fenced = False
    fence_marker = None
    fence_indent = 0
    for i, line in enumerate(body_lines):
        stripped = line.rstrip("\r\n")

        if in_fenced:
            m = FENCE_RE.match(stripped)
            if (
                m
                and len(m.group(2)) == len(fence_marker)
                and m.group(2)[0] == fence_marker[0]
                and len(m.group(1)) >= fence_indent
            ):
                in_fenced = False
                fence_marker = None
            continue

        m = FENCE_RE.match(stripped)
        if m:
            in_fenced = True
            fence_marker = m.group(2)
            fence_indent = len(m.group(1))
            continue

        if stripped.startswith("    "):
            # Indented code block line (4+ spaces). Headings here are ignored.
            continue

        if H1_RE.match(stripped):
            h1_indices.append(i)
    return h1_indices


def hoist_heading(line):
    """Decrease an ATX heading level by one (>=2 -> >=1). Non-headings untouched."""
    rstripped = line.rstrip("\r\n")
    eol = line[len(rstripped):]
    m = ATX_HEADING_RE.match(rstripped)
    if not m or len(m.group(2)) < 2:
        return line
    indent, hashes, rest = m.group(1), m.group(2), m.group(3)
    return f"{indent}{hashes[1:]}{rest}{rstripped[m.end():]}{eol}"


def transform(body):
    """Transform the body: remove the single H1 and hoist the rest. Return new body."""
    body_lines = body.splitlines(keepends=True)
    h1_indices = find_h1_lines(body_lines)

    if len(h1_indices) == 0:
        print(
            "warning: no level-1 heading found; leaving document unchanged.",
            file=sys.stderr,
        )
        return body
    if len(h1_indices) > 1:
        print(
            f"warning: {len(h1_indices)} level-1 headings found; expected exactly 1; leaving document unchanged.",
            file=sys.stderr,
        )
        return body

    target = h1_indices[0]
    out = []
    for i, line in enumerate(body_lines):
        out.append(hoist_heading(line))
    return "".join(out)


def write_output(args, text):
    if not args.inplace:
        sys.stdout.write(text)
        return
    src = args.file
    dir_ = os.path.dirname(os.path.abspath(src)) or "."
    fd, tmp = tempfile.mkstemp(prefix=".md-remove-title-", dir=dir_)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        st = os.stat(src)
        os.chmod(tmp, st.st_mode)
        os.replace(tmp, src)
        print(f"success: updated {src}")
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if not os.path.isfile(args.file):
        print(f"error: not a regular file: {args.file}", file=sys.stderr)
        return 1

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(f"error: could not read {args.file}: {e}", file=sys.stderr)
        return 1

    frontmatter, body = split_frontmatter(text)
    new_body = transform(body)
    result = frontmatter + new_body

    try:
        write_output(args, result)
    except OSError as e:
        print(f"error: could not write output: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
