"""
Apify Yad2 Adapter — Phase 2 (after Decision Gate in M4).

Triggers the swerve/yad2-scraper Actor on Apify cloud, polls for completion,
then streams dataset results as RawListing objects.

Actor cost: ~$5 per 1,000 results.
Schedule: every 2 hours (conservative for free-tier budget).
"""

from __future__ import annotations

from typing import AsyncIterator

import structlog

from src.adapters.base import BaseAdapter
from src.core.models import RawListing

logger = structlog.get_logger(__name__)

ACTOR_ID = "swerve/yad2-scraper"
POLL_INTERVAL_SECONDS = 10


class ApifyYad2Adapter(BaseAdapter):
    """Apify-based Yad2 scraper — implemented in Milestone 5."""

    name = "yad2"

    def __init__(self, apify_token: str) -> None:
        self.apify_token = apify_token

    async def fetch(self, search_config: dict) -> AsyncIterator[RawListing]:
        """Implemented in Milestone 5 after Decision Gate validation."""
        raise NotImplementedError(
            "ApifyYad2Adapter is implemented in Milestone 5. "
            "Complete the Decision Gate (M4) before enabling this adapter."
        )
        yield

    async def health_check(self) -> bool:
        """Check Apify API reachability."""
        raise NotImplementedError("Implemented in Milestone 5.")
