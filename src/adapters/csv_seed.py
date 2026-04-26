"""
CSV Seed Adapter — Phase 1 pipeline validation only.

Reads a CSV file from a configured path and yields RawListing objects.
Purpose: validate the entire pipeline (normalizer → filter → dedup → scoring → DB → Discord)
with zero external cost and zero network dependency.

Full implementation in Milestone 2.
Disabled in production (enabled: false in config).
"""

from __future__ import annotations

from typing import AsyncIterator

import structlog

from src.adapters.base import BaseAdapter
from src.core.models import RawListing

logger = structlog.get_logger(__name__)


class CsvSeedAdapter(BaseAdapter):
    """Reads listings.csv and yields RawListing objects (M2 implementation)."""

    name = "csv_seed"

    def __init__(self, seed_file: str, row_delay_seconds: float = 0.1) -> None:
        self.seed_file = seed_file
        self.row_delay_seconds = row_delay_seconds

    async def fetch(self, search_config: dict) -> AsyncIterator[RawListing]:
        """Implemented in Milestone 2."""
        raise NotImplementedError("CsvSeedAdapter.fetch() is implemented in Milestone 2.")
        yield  # make this an async generator

    async def health_check(self) -> bool:
        """Returns True if the seed file exists."""
        import os
        return os.path.exists(self.seed_file)
