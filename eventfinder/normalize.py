from typing import Dict, List


def dedupe_events(events: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """De-duplicate events by URL, then name+date."""
    raise NotImplementedError


def sort_events(events: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Sort events by date (unknown dates last)."""
    raise NotImplementedError
