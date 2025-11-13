import os
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup


def _find_broken_links(html_path: Path) -> List[str]:
    """Return a list of href targets that are missing on disk."""

    broken_links: List[str] = []
    with html_path.open("r", encoding="utf-8") as handle:
        soup = BeautifulSoup(handle, "html.parser")
        for anchor in soup.find_all("a", href=True):
            link_target = anchor["href"]

            if link_target.startswith(("http://", "https://", "mailto:", "tel:")):
                # External and protocol links are not validated locally.
                continue

            if not os.path.exists(link_target):
                broken_links.append(link_target)

    return broken_links


def test_links() -> None:
    broken_links = _find_broken_links(Path("index.html"))

    assert (
        not broken_links
    ), f"Broken links found in index.html: {', '.join(broken_links)}"


if __name__ == "__main__":
    missing = _find_broken_links(Path("index.html"))
    if missing:
        print("Broken links found:")
        for item in missing:
            print(item)
    else:
        print("All links are valid.")
