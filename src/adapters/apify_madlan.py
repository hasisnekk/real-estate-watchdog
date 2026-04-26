"""
Apify Madlan Adapter — Phase 2 (after Decision Gate in M4).

Triggers the swerve/madlan-scraper Actor on Apify cloud.

Actor cost: ~$2 per 1,000 results (cheapest Apify source).
Schedule: every 2 hours, offset 30 minutes from Yad2.
"""

from __future__ import annotations

from typing import AsyncIterator

import structlog

from src.adapters.base import BaseAdapter
from src.core.models import RawListing

logger = structlog.get_logger(__name__)

ACTOR_ID = "swerve/madlan-scraper"


class ApifyMadlanAdapter(BaseAdapter):
    """Apify-based Madlan scraper — implemented in Milestone 5."""

    name = "madlan"

    def __init__(self, apify_token: str) -> None:
        self.apify_token = apify_token

    async def fetch(self, search_config: dict) -> AsyncIterator[RawListing]:
        """Implemented in Milestone 5 after Decision Gate validation."""
        raise NotImplementedError(
            "ApifyMadlanAdapter is implemented in Milestone 5. "
            "Complete the Decision Gate (M4) before enabling this adapter."
        )
        yield

    async def health_check(self) -> bool:
        raise NotImplementedError("Implemented in Milestone 5.")
