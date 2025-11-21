import pathlib
from bs4 import BeautifulSoup

ASSET_PREFIXES = ("../../media/", "../../components/", "../../plugins/")
ALLOWED_SCHEMES = ("http://", "https://", "//")


def test_index_html_assets_are_root_relative():
    index_file = pathlib.Path("veralogixgoup/index.php/en/index.html")
    soup = BeautifulSoup(index_file.read_text(encoding="utf-8"), "html.parser")

    bad_paths = []
    for tag in soup.find_all(["link", "script"]):
        attr = "href" if tag.name == "link" else "src"
        if not tag.has_attr(attr):
            continue

        url = tag[attr]
        if url.startswith(ALLOWED_SCHEMES) or url.startswith("/") or url.startswith("#"):
            continue

        if any(url.startswith(prefix) for prefix in ASSET_PREFIXES):
            continue

        if any(segment in url for segment in ("media/", "components/", "plugins/")):
            bad_paths.append(url)

    assert not bad_paths, f"Asset paths missing root-relative prefix: {bad_paths}"
