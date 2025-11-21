import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, List

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

HTML_EXTENSIONS = (".html", ".php")
SKIP_PREFIXES = ("http://", "https://", "//", "#", "tel:", "mailto:", "javascript:", "data:")


def find_html_files(root: Path) -> List[Path]:
    html_files: List[Path] = []
    for current_root, _, files in os.walk(root):
        for file_name in files:
            if file_name.lower().endswith(HTML_EXTENSIONS):
                html_files.append(Path(current_root, file_name))
    return html_files


def _should_skip(link: str) -> bool:
    if not link:
        return True
    if link == "%url%" or "external.html" in link:
        return True
    return link.startswith(SKIP_PREFIXES)


def check_links(html_files: Iterable[Path], root: Path):
    broken_links = {}
    for html_file in html_files:
        try:
            content = html_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"Warning: Could not decode file {html_file} as UTF-8. Skipping.")
            continue

        soup = BeautifulSoup(content, "html.parser")

        for a in soup.find_all("a", href=True):
            link = a["href"]
            if _should_skip(link):
                continue

            link_without_query = link.split("?")[0]
            if link_without_query.startswith("/"):
                resolved_link = root / link_without_query.lstrip("/")
            else:
                resolved_link = html_file.parent / link_without_query

            if not resolved_link.exists():
                broken_links.setdefault(str(html_file), []).append(link)

        for img in soup.find_all("img", src=True):
            src = img["src"]
            if _should_skip(src) or "\\\"" in src:
                continue

            if src.startswith("/"):
                resolved_src = root / src.lstrip("/")
            else:
                resolved_src = html_file.parent / src

            if not resolved_src.exists():
                broken_links.setdefault(str(html_file), []).append(src)

    return broken_links


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Check HTML files for broken links.")
    parser.add_argument(
        "--root",
        default="docs",
        help="Root directory containing the rendered site (default: docs)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    root = Path(args.root)

    if not root.exists():
        print(f"Error: root directory '{root}' does not exist.", file=sys.stderr)
        return 2

    html_files = find_html_files(root)
    broken_links = check_links(html_files, root)

    if broken_links:
        print("Broken links found:")
        for file, links in broken_links.items():
            print(f"  In file: {file}")
            for link in links:
                print(f"    - {link}")
        return 1

    print("All links are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
