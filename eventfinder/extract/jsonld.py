import json
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup


def extract_jsonld_fields(soup: BeautifulSoup) -> Tuple[str, str, str, str]:
    event = _find_event_json_ld(soup)
    if not event:
        return "", "", "", ""
    name = event.get("name") or ""
    date = event.get("startDate") or event.get("start_date") or ""
    location = _extract_location_from_json_ld(event.get("location"))
    if not location:
        location = _extract_attendance_location(event)
    url = _extract_url_from_json_ld(event.get("url"))
    name_value = str(name) if name else ""
    date_value = str(date) if date else ""
    return name_value, date_value, location, url


def extract_jsonld_speakers(soup: BeautifulSoup) -> List[str]:
    event = _find_event_json_ld(soup)
    if not event:
        return []
    return _extract_speakers_from_json_ld(event)


def _find_event_json_ld(soup: BeautifulSoup) -> Optional[Dict[str, object]]:
    for tag in soup.find_all("script", type="application/ld+json"):
        raw = tag.string or tag.get_text()
        if not raw:
            continue
        try:
            payload = json.loads(raw.strip())
        except json.JSONDecodeError:
            continue
        event = _find_event_in_payload(payload)
        if event:
            return event
    return None


def _find_event_in_payload(payload: object) -> Optional[Dict[str, object]]:
    if isinstance(payload, list):
        for item in payload:
            event = _find_event_in_payload(item)
            if event:
                return event
        return None
    if not isinstance(payload, dict):
        return None

    if "@graph" in payload:
        graph = payload.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                event = _find_event_in_payload(item)
                if event:
                    return event

    types = payload.get("@type") or payload.get("type")
    if isinstance(types, list):
        if any(str(t).lower().endswith("event") for t in types):
            return payload
    elif isinstance(types, str) and types.lower().endswith("event"):
        return payload

    return None


def _extract_location_from_json_ld(location: object) -> str:
    if isinstance(location, str):
        return location
    if isinstance(location, list) and location:
        for item in location:
            value = _extract_location_from_json_ld(item)
            if value:
                return value
        return ""
    if not isinstance(location, dict):
        return ""

    location_type = str(location.get("@type") or location.get("type") or "").lower()
    if location_type.endswith("virtuallocation"):
        name = location.get("name")
        if isinstance(name, str) and name.strip():
            return name
        return "Online event"

    name = location.get("name")
    if isinstance(name, str) and name.strip():
        return name

    address = location.get("address")
    if isinstance(address, str) and address.strip():
        return address
    if isinstance(address, dict):
        parts = [
            address.get("streetAddress"),
            address.get("addressLocality"),
            address.get("addressRegion"),
            address.get("postalCode"),
            address.get("addressCountry"),
        ]
        joined = ", ".join([part for part in parts if isinstance(part, str) and part])
        return joined

    return ""


def _extract_attendance_location(event: Dict[str, object]) -> str:
    mode = event.get("eventAttendanceMode") or event.get("attendanceMode") or ""
    if isinstance(mode, list) and mode:
        mode = mode[0]
    if isinstance(mode, str) and "OnlineEventAttendanceMode" in mode:
        return "Online event"
    return ""


def _extract_url_from_json_ld(url: object) -> str:
    if isinstance(url, str) and url.strip():
        return url
    if isinstance(url, list) and url:
        return _extract_url_from_json_ld(url[0])
    return ""


def _extract_speakers_from_json_ld(event: Dict[str, object]) -> List[str]:
    speakers = _extract_people_or_org_names(event.get("performer"))
    if not speakers:
        speakers = _extract_people_or_org_names(event.get("speaker"))
    if not speakers:
        speakers = _extract_people_or_org_names(event.get("organizer"))
    return speakers


def _extract_people_or_org_names(value: object) -> List[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, dict):
        name = value.get("name") or value.get("legalName") or value.get("alternateName")
        if isinstance(name, str) and name.strip():
            return [name.strip()]
        return []
    if isinstance(value, list):
        names: List[str] = []
        for item in value:
            names.extend(_extract_people_or_org_names(item))
        return names
    return []
