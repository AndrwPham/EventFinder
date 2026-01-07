import json
import re
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from bs4 import BeautifulSoup


def extract_server_fields(html: str) -> Tuple[str, str, str, str]:
    payload = _extract_server_data_payload(html)
    if not payload:
        return "", "", "", ""
    event = payload.get("event_listing_response", {}).get("event", {})
    if not isinstance(event, dict):
        return "", "", "", ""

    name = event.get("name") or event.get("basic_info", {}).get("name") or ""
    dates = event.get("dates", {})
    date = _extract_date_from_server_dates(dates)
    location = _extract_location_from_server_data(event.get("location"))
    url = event.get("url") or event.get("canonical_url") or ""

    name_value = str(name) if name else ""
    date_value = str(date) if date else ""
    url_value = str(url) if url else ""
    return name_value, date_value, location, url_value


def is_expired_listing(soup: BeautifulSoup, html: str) -> bool:
    if soup.find("button", class_=re.compile(r"\bexpired-view-details\b")):
        return True
    return "expired-view-details" in html


def _extract_server_data_payload(html: str) -> Optional[Dict[str, object]]:
    marker = "window.__SERVER_DATA__"
    start = html.find(marker)
    if start == -1:
        return None
    brace_start = html.find("{", start)
    if brace_start == -1:
        return None
    brace_end = _find_matching_brace(html, brace_start)
    if brace_end is None:
        return None
    raw = html[brace_start : brace_end + 1]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _find_matching_brace(text: str, start: int) -> Optional[int]:
    depth = 0
    in_string = False
    string_char = ""
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue
            if char == string_char:
                in_string = False
            continue
        if char in {"'", '"'}:
            in_string = True
            string_char = char
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    return None


def _extract_location_from_server_data(location: object) -> str:
    if isinstance(location, str):
        return location
    if not isinstance(location, dict):
        return ""

    for key in ("display_location", "displayLocation", "name", "venue_name"):
        value = location.get(key)
        if isinstance(value, str) and value.strip():
            return value

    address = location.get("address")
    if isinstance(address, str) and address.strip():
        return address
    if isinstance(address, dict):
        for key in (
            "localized_address_display",
            "localized_area_display",
            "localized_multi_line_address_display",
        ):
            value = address.get(key)
            if isinstance(value, str) and value.strip():
                return value
        parts = [
            address.get("address_1"),
            address.get("address_2"),
            address.get("city"),
            address.get("region"),
            address.get("postal_code"),
            address.get("country"),
        ]
        joined = ", ".join([part for part in parts if isinstance(part, str) and part])
        return joined

    return ""


def _extract_date_from_server_dates(dates: object) -> str:
    if not isinstance(dates, dict):
        return ""
    utc_value = _find_utc_value(dates, ("start", "start_date", "startDate"))
    if not utc_value:
        utc_value = _find_utc_value(dates, ("end", "end_date", "endDate"))
    if utc_value:
        return _humanize_utc(utc_value)

    display = dates.get("displayStartDateWithTz") or dates.get("displayEndDateWithTz")
    if isinstance(display, str) and display.strip():
        return display.strip()
    return ""


def _find_utc_value(container: Dict[str, object], keys: Tuple[str, ...]) -> str:
    for key in keys:
        value = container.get(key)
        if isinstance(value, str):
            if "T" in value and ("Z" in value or "+" in value):
                return value
        if isinstance(value, dict):
            utc = value.get("utc") or value.get("utc_time") or value.get("utcTime")
            if isinstance(utc, str) and utc.strip():
                return utc.strip()
    return ""


def _humanize_utc(value: str) -> str:
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return value
    return parsed.astimezone(timezone.utc).strftime("%b %d, %Y %I:%M %p UTC")
