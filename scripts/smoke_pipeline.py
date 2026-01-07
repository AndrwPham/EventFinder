import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eventfinder.pipeline import run_pipeline
from eventfinder.search import search_event_urls


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the full pipeline.")
    parser.add_argument("speaker", nargs="?", default="Tony Robbins")
    args = parser.parse_args()

    load_dotenv()
    urls = search_event_urls(args.speaker)
    events = run_pipeline(args.speaker)
    print(json.dumps({"speaker": args.speaker, "events": events}, indent=2))
    print("Fetched URLs:")
    for url in urls:
        print(f"- {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
