import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eventfinder.search import search_event_urls_with_sources


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the search layer.")
    parser.add_argument("speaker", nargs="?", default="Tony Robbins")
    args = parser.parse_args()

    load_dotenv()
    sources = search_event_urls_with_sources(args.speaker)
    urls = sources["firecrawl"] + sources["eventbrite"]
    print(
        json.dumps(
            {
                "speaker": args.speaker,
                "count": len(urls),
                "firecrawl": sources["firecrawl"],
                "eventbrite": sources["eventbrite"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
