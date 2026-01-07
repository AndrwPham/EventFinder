# Plan (KISS Phases)

## Phase 0 — Scope Lock
- Confirm: simplify in place vs. rebuild minimal modules.
- Confirm: response shape is `{ "speaker": "...", "events": [...] }`.
- LLM fallback is disabled by default. If enabled, it only fills missing fields and never overwrites deterministic extraction.

## Phase 1 — Minimal Structure
- Keep only: `app.py`, `eventfinder/search.py`, `eventfinder/extract.py` (fetch + parse), `eventfinder/normalize.py`.
- Remove or ignore legacy code paths that add complexity.
- Keep `requirements.txt` minimal.

## Phase 2 — Search Layer
- Firecrawler searches for event URLs using speaker queries.
- Eventbrite listing search runs in parallel for speaker-specific event URLs.
- Cap results and de-duplicate; filter blocked domains and non-event paths.

## Phase 3 — Fetch + Extract
- Fetch with `requests` (timeout 10s, single User-Agent).
- Extraction rules only:
  - `event_name`: `og:title` → `<h1>`.
  - `date`: JSON-LD `startDate` → regex fallback.
  - `location`: JSON-LD `location.name` → regex fallback.
  - `speakers`: JSON-LD `performer` or `speaker`.
- LLM fallback (if enabled): only when 300+ chars of text exist and 2+ fields are missing; never overwrites.

## Phase 4 — Normalize + API
- Normalize to `event_name`, `date`, `location`, `url`, `speakers`.
- Deduplicate by `url`, then `(event_name + date)`.
- Sort by date; missing dates last.
- `/events?speaker=...` returns `{ "speaker": "...", "events": [...] }`.

## Phase 5 — Verification & Docs
- Smoke script is optional.
- README contains:
  - What this does
  - How to run
  - Example output
  - Env vars
