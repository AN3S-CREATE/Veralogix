#!/usr/bin/env python3
"""Rewrite local asset references so they are relative to the docs root.

This script scans HTML documents inside the provided root directory and rewrites
attributes that reference local resources so that they become relative to the
root. It is useful when files are moved around and existing relative paths break
because they are anchored to their original directory.

Usage examples
--------------
Dry run:
    python scripts/update_relative_links.py --root docs --dry-run

Apply changes:
    python scripts/update_relative_links.py --root docs
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup

ATTRIBUTE_NAMES: Tuple[str, ...] = ("href", "src", "data-src", "poster", "srcset")
SKIP_PREFIXES: Tuple[str, ...] = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
    "javascript:",
    "data:",
    "#",
    "//",
)
HTML_EXTENSIONS: Tuple[str, ...] = (".html", ".htm", ".xhtml")


def is_local_reference(value: str) -> bool:
    """Return True if *value* looks like a local filesystem reference."""

    stripped = value.strip()
    if not stripped:
        return False
    return not stripped.startswith(SKIP_PREFIXES)


def normalise_path(value: str) -> str:
    """Normalise path separators to forward slashes for HTML usage."""

    return value.replace(os.sep, "/")


def rewrite_url(value: str, base_file: Path, root: Path) -> Optional[str]:
    """Rewrite a single URL to be relative to *root* if it is local."""

    if not isinstance(value, str):
        return None

    raw_value = value.strip()
    if not raw_value or not is_local_reference(raw_value):
        return None

    parts = urlsplit(raw_value)

    # If the URL already has a scheme or network location treat it as external.
    if parts.scheme or parts.netloc:
        return None

    path = parts.path
    if not path:
        return None

    base_dir = base_file.parent
    try:
        if path.startswith("/"):
            target = (root / path.lstrip("/")).resolve()
        else:
            target = (base_dir / path).resolve()
    except FileNotFoundError:
        return None

    try:
        relative_target = target.relative_to(root)
    except ValueError:
        return None

    rewritten_path = normalise_path(str(relative_target))
    rebuilt = urlunsplit(("", "", rewritten_path, parts.query, parts.fragment))

    return rebuilt if rebuilt != raw_value else None


def rewrite_srcset(value: str, base_file: Path, root: Path) -> Tuple[Optional[str], List[Tuple[str, str]]]:
    """Rewrite the srcset attribute value, returning new value and per-entry changes."""

    entries = [entry.strip() for entry in value.split(",")]
    new_entries: List[str] = []
    changes: List[Tuple[str, str]] = []
    changed = False

    for entry in entries:
        if not entry:
            continue

        parts = entry.split()
        if not parts:
            continue

        original_url = parts[0]
        rewritten_url = rewrite_url(original_url, base_file, root)
        if rewritten_url:
            parts[0] = rewritten_url
            changed = True
            changes.append((original_url, rewritten_url))

        new_entries.append(" ".join(parts))

    if not changed:
        return None, []

    return ", ".join(new_entries), changes


def find_html_files(root: Path) -> Iterable[Path]:
    """Yield HTML files inside *root* sorted for determinism."""

    for file_path in sorted(root.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in HTML_EXTENSIONS:
            yield file_path


def process_file(file_path: Path, root: Path, dry_run: bool) -> bool:
    """Process a single HTML file and optionally rewrite it."""

    try:
        original_text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        relative_name = normalise_path(str(file_path.relative_to(root)))
        print(f"Skipping {relative_name}: {exc}", file=sys.stderr)
        return False

    soup = BeautifulSoup(original_text, "html.parser")

    recorded_changes: List[Tuple[str, str, str]] = []

    for tag in soup.find_all(True):
        for attribute in ATTRIBUTE_NAMES:
            if not tag.has_attr(attribute):
                continue

            value = tag.get(attribute)
            if value is None:
                continue

            if attribute == "srcset":
                new_value, entry_changes = rewrite_srcset(str(value), file_path, root)
                if new_value:
                    tag[attribute] = new_value
                    for old, new in entry_changes:
                        recorded_changes.append((attribute, old, new))
            else:
                new_value = rewrite_url(str(value), file_path, root)
                if new_value:
                    tag[attribute] = new_value
                    recorded_changes.append((attribute, str(value), new_value))

    if not recorded_changes:
        return False

    relative_name = normalise_path(str(file_path.relative_to(root)))
    print(f"{relative_name}")
    for attribute, old, new in recorded_changes:
        print(f"  {attribute}: {old} -> {new}")

    if not dry_run:
        file_path.write_text(soup.decode(formatter="html"), encoding="utf-8")

    return True


def update_links(root: Path, dry_run: bool) -> int:
    """Update links for every HTML file under *root* and return number of files touched."""

    updated_files = 0
    for html_file in find_html_files(root):
        if process_file(html_file, root, dry_run=dry_run):
            updated_files += 1

    if updated_files == 0:
        message = "No local links required rewriting." if dry_run else "No files were updated."
        print(message)

    return updated_files


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="docs", help="Path to the documentation root directory.")
    parser.add_argument("--dry-run", action="store_true", help="Preview the changes without writing files.")

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    if not root.exists():
        print(f"Root directory '{root}' does not exist. Nothing to rewrite.", file=sys.stderr)
        return 0

    updated_files = update_links(root, dry_run=args.dry_run)

    if args.dry_run:
        print(f"Dry run complete. {updated_files} file(s) would be updated.")
    else:
        print(f"Update complete. {updated_files} file(s) updated.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
