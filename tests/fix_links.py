import argparse
import sys
from pathlib import Path

import comprehensive_link_checker
from link_rewriter import rewrite_links


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Rewrite HTML links relative to a common root and verify the result."
    )
    parser.add_argument(
        "--root",
        default="docs",
        help="Root directory containing the rendered site (default: docs)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    root = Path(args.root)

    try:
        modified_files = rewrite_links(root)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if modified_files:
        print("Updated links in:")
        for file_path in modified_files:
            print(f"  - {file_path}")
    else:
        print("No link rewrites were necessary.")

    print("Running comprehensive link checker...")
    return comprehensive_link_checker.main(["--root", args.root])


if __name__ == "__main__":
    sys.exit(main())
