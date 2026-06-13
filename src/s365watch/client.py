"""HTTP client for the Standoff 365 Bug Bounty public UI API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from s365watch.config import API_BASE_URL, SITE_ORIGIN
from s365watch.models import Program

logger = logging.getLogger(__name__)

PROGRAMS_PATH = "/bug-bounty/ui/program"
# The API caps an unpaginated response well below this; one page covers the
# full catalogue (~200 entries) without needing to walk pages.
PAGE_SIZE = 500

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Origin": SITE_ORIGIN,
    "Referer": f"{SITE_ORIGIN}/",
    "Accept": "application/json",
}


class Standoff365Client:
    """Reads bug bounty programs from the Standoff 365 UI API.

    The endpoint is the same one the public website calls; it requires the
    browser-like Origin/Referer headers above or the WAF returns 403.
    """

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    @classmethod
    def create(cls, timeout: float = 30.0) -> Standoff365Client:
        """Construct a client with a configured httpx session."""
        session = httpx.Client(
            base_url=API_BASE_URL,
            headers=_HEADERS,
            timeout=timeout,
        )
        return cls(session)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Standoff365Client:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def fetch_programs(self) -> list[Program]:
        """Fetch all programs known to the platform.

        Returns:
            Every program entry, regardless of status. Filter with
            :meth:`fetch_published_programs` for publicly visible ones.

        Raises:
            httpx.HTTPError: On network failure or non-2xx response.
        """
        response = self._client.get(PROGRAMS_PATH, params={"page": 1, "pagesize": PAGE_SIZE})
        response.raise_for_status()
        payload = response.json()
        items = _extract_items(payload)
        programs = [Program.from_api(item) for item in items]
        logger.debug("fetched %d programs", len(programs))
        return programs

    def fetch_published_programs(self) -> list[Program]:
        """Fetch only programs that are publicly published on the platform."""
        return [p for p in self.fetch_programs() if p.is_published]


def _extract_items(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValueError(f"unexpected API response type: {type(payload).__name__}")
    items = payload.get("items")
    if not isinstance(items, list):
        raise ValueError("API response missing 'items' list")
    return [item for item in items if isinstance(item, dict)]
