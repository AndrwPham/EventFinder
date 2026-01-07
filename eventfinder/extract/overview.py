import re
from typing import List

from bs4 import BeautifulSoup

from .utils import clean_text


def extract_overview_text(soup: BeautifulSoup) -> str:
    candidates: List[str] = []

    for attr, value in (("name", "description"), ("property", "og:description")):
        meta = soup.find("meta", attrs={attr: value})
        if meta and meta.get("content"):
            candidates.append(str(meta["content"]))

    patterns = [
        ("data-testid", re.compile(r"(description|summary|overview|event-details)", re.I)),
        ("id", re.compile(r"(description|summary|overview|event-details)", re.I)),
        ("class", re.compile(r"(description|summary|overview|event-details)", re.I)),
    ]
    for attr, pattern in patterns:
        for node in soup.find_all(attrs={attr: pattern}):
            text = node.get_text(" ", strip=True)
            if text:
                candidates.append(text)

    if not candidates:
        return ""

    best = max(candidates, key=len)
    return clean_text(best)
