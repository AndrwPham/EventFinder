# EventFinder Docs

**Note:** This is a work that I KISS. There are still many gaps like:
- The output from the firecrawl search is not consistent
- The output from the eventbrite listing search is empty
- The works is tightly coupled with Eventbrite as I only extract data from their domain

## Overview
EventFinder is a minimal Flask API that searches public event sources by speaker name, fetches event pages, and extracts structured event data. The extraction pipeline prefers JSON-LD and Eventbrite server data, with an optional LLM fallback for speakers only.

## High-Level Architecture
Flow:
1. Client calls `/events?speaker=...` in `app.py`.
2. Search layer (`eventfinder/search.py`) returns candidate event URLs.
3. Extract layer (`eventfinder/extract/`) fetches pages and extracts fields.
4. (Planned) Normalize layer (`eventfinder/normalize.py`) de-dupes and sorts.
5. API returns `{ speaker, events[] }`.

Key components:
- `app.py`: Flask API entrypoint.
- `eventfinder/search.py`: Firecrawl + Eventbrite search, URL filters, de-dupe.
- `eventfinder/extract/`: HTML fetch, JSON-LD, server data, fallbacks, LLM speakers.
- `scripts/`: smoke tests and helper utilities.


## Quick Start
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Create `.env` (optional for basic search):
   - `OPENAI_API_KEY=...` (only required if using LLM speaker extraction)
3. Run the API:
   - `python app.py`
4. Call the endpoint:
   - `GET http://localhost:5000/events?speaker=Tony%20Robbins`

## API
### `GET /events?speaker=...`
Returns event data for the provided speaker name.

Response shape:
```json
{
  "speaker": "Tony Robbins",
  "events": [
    {
      "event_name": "Event Title",
      "date": "2026-01-13T10:00:00-08:00",
      "location": "Online event",
      "url": "https://www.eventbrite.com/e/...",
      "speakers": ["Tony Robbins"]
    }
  ]
}
```

Errors:
- `400` when `speaker` is missing.

## Search Layer
Implementation: `eventfinder/search.py`

### Sources
- Firecrawl search queries for Eventbrite domain.
- Eventbrite listing search in parallel with Firecrawl.
**Note:** The reason I choose Firecrawl on Eventbrite and search on Eventbrite.com, is because I think there will be duplicate results from the listing search. But the search from eventbrite return nothing.

### Filters
- Blocked domains filtered (social media).
- Firecrawl results keep only event-detail paths:
  - Eventbrite: `/e/`
- URLs are de-duplicated across sources

### Concurrency
Firecrawl and Eventbrite searches run concurrently via `ThreadPoolExecutor`.

## Extract Layer
Package: `eventfinder/extract/`

### Flow
1. Fetch HTML (`fetch.py`)
2. Parse JSON-LD (`jsonld.py`)
3. If fields missing or expired listing, parse `window.__SERVER_DATA__` (`server_data.py`)
4. Fallback parse for name/date/location from visible HTML (`utils.py`)
5. Speakers: LLM from overview text (`overview.py` + `speakers.py`), then JSON-LD fallback

URLs that return missing fields mean that they are expired.

### LLM Speakers (Optional)
Speakers can be inferred from the event overview using GPT.

Env vars:
- `OPENAI_API_KEY` (required)
- `EVENTFINDER_LLM_SPEAKERS=1` to enable
- `EVENTFINDER_LLM_SPEAKERS_LOG=1` to log overview + response
- `EVENTFINDER_LLM_MODEL` (default `gpt-4o`)

Behavior:
- Only runs after required fields are present.
- Requires overview length >= 300 characters.
- Never overwrites existing speakers.
- If LLM returns nothing, JSON-LD speakers are used as fallback.

### Parallel URL Processing
URL fetching/extraction can run in parallel:
- `EVENTFINDER_EXTRACT_WORKERS` (default `4`)

## Normalize Layer
File: `eventfinder/normalize.py`

Status: currently stubbed. Planned behavior:
- De-duplicate by URL, then `(event_name + date)`
- Sort by date (unknown dates last)

## Scripts
### Search Smoke Test
`python scripts/smoke_search.py "Tony Robbins"`

Outputs search sources and URLs.

### Extract Smoke Test
`python scripts/smoke_extract.py --speaker "Tony Robbins"`

Runs search + extraction and prints events JSON.

### Fetch HTML
`python scripts/fetch_html.py https://example.com --out page.html`

Fetches raw HTML and saves to disk.

## Directory Layout
```
app.py
eventfinder/
  search.py
  constants.py
  normalize.py
  extract/
    __init__.py
    pipeline.py
    fetch.py
    jsonld.py
    server_data.py
    overview.py
    speakers.py
    utils.py
scripts/
  smoke_search.py
  smoke_extract.py
  fetch_html.py
```

## Notes / Gaps
- `eventfinder/normalize.py` is not implemented.
