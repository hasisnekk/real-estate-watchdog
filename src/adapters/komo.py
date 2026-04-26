"""
Komo Direct HTTP Adapter — Phase 1 live adapter.

Komo (komo.co.il) is reachable via direct HTTP from the deployment server.
Uses httpx.AsyncClient + BeautifulSoup4 to scrape listing pages.

Full implementation in Milestone 3 after reverse-engineering the Komo HTML/JSON
structure via browser DevTools.
"""

from __future__ import annotations

from typing import AsyncIterator

import httpx
import structlog

from src.adapters.base import BaseAdapter
from src.core.models import RawListing

logger = structlog.get_logger(__name__)

KOMO_BASE_URL = "https://www.komo.co.il"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class KomoAdapter(BaseAdapter):
    """Direct HTTP scraper for komo.co.il (M3 implementation)."""

    name = "komo"

    def __init__(self) -> None:
        # Shared async HTTP client (one per adapter instance, not per request)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=HEADERS,
                follow_redirects=True,
                timeout=httpx.Timeout(30.0),
            )
        return self._client

    async def fetch(self, search_config: dict) -> AsyncIterator[RawListing]:
        """
        Scrape Komo for listings matching the search config.
        Full implementation in Milestone 3 after DevTools analysis.
        """
        raise NotImplementedError(
            "KomoAdapter.fetch() is implemented in Milestone 3. "
            "First reverse-engineer Komo's API structure via browser DevTools."
        )
        yield  # make this an async generator

    async def health_check(self) -> bool:
        """Return True if komo.co.il returns HTTP 200."""
        try:
            client = await self._get_client()
            resp = await client.head(KOMO_BASE_URL, timeout=10.0)
            return resp.status_code < 400
        except Exception as exc:
            logger.warning("komo_health_check_failed", error=str(exc))
            return False
