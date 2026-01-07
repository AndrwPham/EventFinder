import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Iterable, List, Optional

from bs4 import BeautifulSoup

from .fetch import fetch_html
from .jsonld import extract_jsonld_fields, extract_jsonld_speakers
from .overview import extract_overview_text
from .server_data import extract_server_fields, is_expired_listing
from .speakers import infer_speakers_with_llm
from .utils import (
    clean_text,
    dedupe_speakers,
    extract_date_fallback,
    extract_event_name,
    extract_location_fallback,
    normalize_url,
)

DEFAULT_EXTRACT_WORKERS = 4


def fetch_and_extract(urls: Iterable[str]) -> List[Dict[str, object]]:
    """Fetch pages and extract event fields."""
    events: List[Dict[str, object]] = []
    url_list = list(urls)
    if not url_list:
        return events

    workers = max(1, DEFAULT_EXTRACT_WORKERS)
    if workers <= 1 or len(url_list) == 1:
        for url in url_list:
            event = _process_url(url)
            if event:
                events.append(event)
        return events

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for event in executor.map(_process_url, url_list):
            if event:
                events.append(event)
    return events


def _process_url(url: str) -> Optional[Dict[str, object]]:
    try:
        html = fetch_html(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        expired_listing = is_expired_listing(soup, html)

        name, date, location, url_from_ld = extract_jsonld_fields(soup)
        if expired_listing or not (name and date and location):
            server_name, server_date, server_location, server_url = extract_server_fields(
                html
            )
            if not name:
                name = server_name
            if not date:
                date = server_date
            if not location:
                location = server_location
            if not url_from_ld:
                url_from_ld = server_url

        if not name:
            name = extract_event_name(soup)
        if not date and not expired_listing:
            date = extract_date_fallback(soup)
        if not location and not expired_listing:
            location = extract_location_fallback(soup)

        name = clean_text(name)
        date = clean_text(date)
        location = clean_text(location)
        final_url = normalize_url(url_from_ld or url)

        if not (name and date and location):
            return None

        speakers: List[str] = []
        speakers = dedupe_speakers(speakers)
        if not speakers:
            overview = extract_overview_text(soup)
            if overview:
                llm_speakers = infer_speakers_with_llm(overview)
                if llm_speakers:
                    speakers = dedupe_speakers(llm_speakers)
        if not speakers:
            speakers = dedupe_speakers(extract_jsonld_speakers(soup))

        return {
            "event_name": name,
            "date": date,
            "location": location,
            "url": final_url,
            "speakers": speakers,
        }
    except Exception:
        return None
