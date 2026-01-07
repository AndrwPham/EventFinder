import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, List
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .constants import (
    BLOCKED_DOMAINS,
    FIRECRAWL_PER_QUERY_LIMIT,
    FIRECRAWL_QUERY_TEMPLATES,
    FIRECRAWL_TOTAL_CAP,
)

FIRECRAWL_SEARCH_URL = "https://api.firecrawl.dev/v1/search"
EVENTBRITE_BASE_URL = "https://www.eventbrite.com"
USER_AGENT = "Mozilla/5.0 (compatible; EventFinder/1.0)"
DEBUG_SEARCH = os.getenv("EVENTFINDER_DEBUG", "").lower() in {"1", "true", "yes"}


def _debug(message: str) -> None:
    if DEBUG_SEARCH:
        print(message)


def search_event_urls(speaker: str) -> List[str]:
    """Return candidate event detail URLs for a speaker."""
    sources = search_event_urls_with_sources(speaker)
    combined = sources["firecrawl"] + sources["eventbrite"]
    return _dedupe_keep_order(combined)


def search_event_urls_with_sources(speaker: str) -> dict[str, List[str]]:
    """Return candidate URLs grouped by source."""
    speaker = speaker.strip()
    if not speaker:
        return {"firecrawl": [], "eventbrite": []}

    with ThreadPoolExecutor(max_workers=2) as executor:
        firecrawl_future = executor.submit(_search_firecrawl, speaker)
        eventbrite_future = executor.submit(_search_eventbrite, speaker)
        firecrawl_urls = firecrawl_future.result()
        eventbrite_urls = eventbrite_future.result()

    firecrawl_urls = _dedupe_keep_order(firecrawl_urls)
    eventbrite_urls = _dedupe_keep_order(eventbrite_urls)
    if firecrawl_urls and eventbrite_urls:
        seen = {url.lower() for url in firecrawl_urls}
        eventbrite_urls = [url for url in eventbrite_urls if url.lower() not in seen]

    return {
        "firecrawl": firecrawl_urls,
        "eventbrite": eventbrite_urls,
    }


def _search_eventbrite(speaker: str, limit: int = 20) -> List[str]:
    url = _build_eventbrite_search_url(speaker)
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    speaker_tokens = _tokenize(speaker)
    urls: List[str] = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(url, anchor["href"])
        if _is_eventbrite_event_url(href):
            title = _extract_anchor_title(anchor)
            if not _matches_speaker(title, speaker_tokens):
                continue
            urls.append(href)

    return _dedupe_keep_order(urls)[:limit]


def _build_eventbrite_search_url(speaker: str) -> str:
    slug = _slugify_query(speaker)
    return f"{EVENTBRITE_BASE_URL}/d/online/{slug}/"


def _slugify_query(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return quote(value)


def _extract_anchor_title(anchor: BeautifulSoup) -> str:
    for attr in ("aria-label", "title"):
        value = anchor.get(attr)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return anchor.get_text(" ", strip=True)


def _matches_speaker(title: str, speaker_tokens: List[str]) -> bool:
    if not title or not speaker_tokens:
        return False
    title_tokens = set(_tokenize(title))
    return all(token in title_tokens for token in speaker_tokens)


def _tokenize(value: str) -> List[str]:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return [token for token in value.split() if token]


def _is_eventbrite_event_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    if not host.endswith("eventbrite.com"):
        return False
    return "/e/" in (parsed.path or "")


def _search_firecrawl(speaker: str) -> List[str]:
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        _debug("Firecrawl: FIRECRAWL_API_KEY is not set.")
        return []

    urls: List[str] = []
    for query in _build_firecrawl_queries(speaker):
        payload = {"query": query, "limit": FIRECRAWL_PER_QUERY_LIMIT}
        _debug(f"Firecrawl query: {payload['query']}")
        try:
            response = requests.post(
                FIRECRAWL_SEARCH_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            payload_data = response.json()
        except (requests.RequestException, ValueError):
            continue

        urls.extend(_extract_urls(payload_data))

    filtered = [
        url for url in urls if not _is_blocked_url(url) and _is_firecrawl_event_url(url)
    ]
    deduped = _dedupe_keep_order(filtered)
    return deduped[:FIRECRAWL_TOTAL_CAP]


def _build_firecrawl_queries(speaker: str) -> List[str]:
    return [template.format(speaker=speaker) for template in FIRECRAWL_QUERY_TEMPLATES]


def _extract_urls(payload: object) -> List[str]:
    if not isinstance(payload, dict):
        return []

    candidates = payload.get("data") or payload.get("results") or payload.get("links")
    if isinstance(candidates, dict):
        candidates = (
            candidates.get("results")
            or candidates.get("data")
            or candidates.get("links")
        )
    if not isinstance(candidates, list):
        return []

    urls: List[str] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        url = item.get("url") or item.get("link") or item.get("source")
        if isinstance(url, str) and _is_http_url(url):
            urls.append(url.strip())
    return urls


def _is_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"}


def _is_blocked_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return True
    host = (parsed.hostname or "").lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in BLOCKED_DOMAINS)


def _is_firecrawl_event_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    path = (parsed.path or "").lower()
    if host.endswith("eventbrite.com"):
        return "/e/" in path
    if host.endswith("meetup.com"):
        return "/e/" in path or "/events/" in path
    if host.endswith("eventful.com"):
        return "/event/" in path or "/events/" in path
    if host.endswith("allevents.in"):
        return "/event/" in path or "/events/" in path
    return False


def _dedupe_keep_order(items: Iterable[str]) -> List[str]:
    seen = set()
    ordered = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered
