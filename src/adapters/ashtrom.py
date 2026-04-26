"""
Ashtrom Direct HTTP Adapter — Phase 2 (M6).

Ashtrom (ashtrom.co.il) is a developer site (קבלן).
IMPORTANT: Before implementing, manually verify that Ashtrom lists rental
apartments (not purchase-only). If no rentals exist, this adapter is skipped.

Schedule: every 6 hours (developer inventory changes slowly).
"""

from __future__ import annotations

from typing import AsyncIterator

import structlog

from src.adapters.base import BaseAdapter
from src.core.models import RawListing

logger = structlog.get_logger(__name__)


class AshtromAdapter(BaseAdapter):
    """Direct HTTP scraper for ashtrom.co.il — implemented in Milestone 6."""

    name = "ashtrom"

    async def fetch(self, search_config: dict) -> AsyncIterator[RawListing]:
        raise NotImplementedError(
            "AshtromAdapter is implemented in Milestone 6. "
            "First verify that Ashtrom lists rental apartments (not purchase-only)."
        )
        yield

    async def health_check(self) -> bool:
        raise NotImplementedError("Implemented in Milestone 6.")
