# Simple Event Speaker Finder

## What this does
Provides a single Flask API endpoint that searches public sources for events by speaker name and returns structured JSON.

## How to run
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Set env vars (optional):
   - None required for basic search.
3. Start the API:
   - `python app.py`
4. Call the endpoint:
   - `GET http://localhost:5000/events?speaker=Tony%20Robbins`

## Example output
```json
{
  "speaker": "Tony Robbins",
  "events": [
    {
      "event_name": "Unleash the Power Within",
      "date": "2026-03-12",
      "location": "Los Angeles, CA",
      "url": "https://www.eventbrite.com/e/...",
      "speakers": ["Tony Robbins"]
    }
  ]
}
```

## Env vars
- Firecrawler key
- openai key
