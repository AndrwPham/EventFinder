import argparse
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

USER_AGENT = "Mozilla/5.0 (compatible; EventFinder/1.0)"


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch HTML for a URL.")
    parser.add_argument("url", help="URL to fetch.")
    parser.add_argument(
        "--out",
        help="Optional output path to write HTML instead of stdout.",
    )
    args = parser.parse_args()

    url = args.url
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Request failed: {exc}")
        return 1

    html = response.text

    if args.out:
        Path(args.out).write_text(html, encoding="utf-8")
        print(f"Wrote HTML to {args.out}")
        return 0

    print(html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
