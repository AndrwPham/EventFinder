import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eventfinder.extract import fetch_and_extract
from eventfinder.search import search_event_urls


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the extract layer.")
    parser.add_argument(
        "--speaker",
        default="",
        help="Optional speaker name to search for event URLs.",
    )
    parser.add_argument(
        "urls",
        nargs="*",
        help="Event URLs to fetch and extract.",
    )
    args = parser.parse_args()

    load_dotenv()

    urls = list(args.urls)
    if not urls and args.speaker:
        urls = search_event_urls(args.speaker)
    if not urls:
        print("Provide URLs or --speaker to search.")
        return 2

    print(f"Processing {len(urls)} URLs")
    for url in urls:
        print(f"- {url}")
    events = fetch_and_extract(urls)
    print(json.dumps({"count": len(events), "events": events}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
