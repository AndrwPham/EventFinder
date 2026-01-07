from typing import Optional

import requests

USER_AGENT = "Mozilla/5.0 (compatible; EventFinder/1.0)"


def fetch_html(url: str) -> Optional[str]:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        return None
    return response.text
