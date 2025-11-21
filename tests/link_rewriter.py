"""Utilities for rewriting links to relative paths within generated HTML."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Sequence, Tuple

from bs4 import BeautifulSoup

SKIP_PREFIXES: Tuple[str, ...] = (
    "http://",
    "https://",
    "//",
    "#",
    "tel:",
    "mailto:",
    "javascript:",
    "data:",
)


def find_html_files(root: Path) -> List[Path]:
    html_files: List[Path] = []
    for file_path in root.rglob("*"):
        if file_path.suffix.lower() in {".html", ".php"} and file_path.is_file():
            html_files.append(file_path)
    return html_files


def _should_skip(value: str) -> bool:
    if not value:
        return True
    if value == "%url%" or "external.html" in value or "\\\"" in value:
        return True
    return value.startswith(SKIP_PREFIXES)


def _update_attribute(html_path: Path, attribute: str, value: str, root: Path) -> str | None:
    clean_value = value.split("?")[0]

    if clean_value.startswith("/"):
        candidate = root / clean_value.lstrip("/")
        if candidate.exists():
            return _relative_path(candidate, html_path.parent)

    resolved = html_path.parent / clean_value
    if resolved.exists():
        return None

    fallback = root / Path(clean_value).name
    if fallback.exists():
        return _relative_path(fallback, html_path.parent)

    return None


def _relative_path(target: Path, base: Path) -> str:
    return os.path.relpath(target, base).replace("\\", "/")


def rewrite_links(root: Path) -> Sequence[Path]:
    if not root.exists():
        raise FileNotFoundError(f"Root directory '{root}' does not exist.")

    modified_files: List[Path] = []

    for html_file in find_html_files(root):
        try:
            content = html_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"Warning: Could not decode file {html_file} as UTF-8. Skipping.")
            continue

        soup = BeautifulSoup(content, "html.parser")
        modified = False

        for tag_name, attribute in (("a", "href"), ("img", "src")):
            for tag in soup.find_all(tag_name, attrs={attribute: True}):
                raw_value = tag.get(attribute)
                if raw_value is None or _should_skip(raw_value):
                    continue

                updated = _update_attribute(html_file, attribute, raw_value, root)
                if updated and updated != raw_value:
                    tag[attribute] = updated
                    modified = True

        if modified:
            html_file.write_text(str(soup), encoding="utf-8")
            modified_files.append(html_file)

    return modified_files


__all__ = ["rewrite_links", "find_html_files"]
