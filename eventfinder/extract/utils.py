import re
from typing import List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

DATE_REGEXES = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\s+\d{1,2},\s+\d{4}\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
        r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
        r"Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b",
        re.IGNORECASE,
    ),
]
LOCATION_LABELS = ("location", "venue", "where")


def extract_event_name(soup: BeautifulSoup) -> str:
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        return str(og["content"])
    h1 = soup.find("h1")
    if h1:
        text = h1.get_text(" ", strip=True)
        if text:
            return text
    title = soup.find("title")
    if title:
        return title.get_text(" ", strip=True)
    return ""


def extract_date_fallback(soup: BeautifulSoup) -> str:
    text = soup.get_text(" ", strip=True)
    for pattern in DATE_REGEXES:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return ""


def extract_location_fallback(soup: BeautifulSoup) -> str:
    text_nodes = [text.strip() for text in soup.stripped_strings if text.strip()]
    for idx, text in enumerate(text_nodes):
        lowered = text.lower()
        for label in LOCATION_LABELS:
            label_prefix = f"{label}:"
            if lowered.startswith(label_prefix):
                value = text.split(":", 1)[1].strip()
                if value:
                    return value
            if lowered == label and idx + 1 < len(text_nodes):
                value = text_nodes[idx + 1].strip()
                if value:
                    return value
    return ""


def clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def normalize_url(url: str) -> str:
    try:
        parsed = urlparse(url)
    except ValueError:
        return url
    if parsed.scheme and parsed.netloc:
        return parsed.geturl()
    return url


def dedupe_speakers(speakers: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for speaker in speakers:
        cleaned = clean_text(speaker)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(cleaned)
    return ordered
