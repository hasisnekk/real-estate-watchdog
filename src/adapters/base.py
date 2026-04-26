"""
Abstract base class for all source adapters.

Every adapter must implement:
  fetch()        — async generator yielding RawListing objects
  health_check() — returns True if the source is reachable

Usage in the pipeline:
    async for raw_listing in adapter.fetch(search_config):
        listing = normalizer.normalize(raw_listing)
        ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from src.core.models import RawListing


class BaseAdapter(ABC):
    """Abstract base for all source adapters. All methods are async."""

    name: str  # must be set as a class attribute in every subclass

    @abstractmethod
    async def fetch(self, search_config: dict) -> AsyncIterator[RawListing]:
        """
        Async generator: fetch listings from this source.

        Yields RawListing objects as they are received.
        The pipeline calls `async for listing in adapter.fetch(config)`.
        Each listing is processed (normalized, filtered, scored, persisted)
        before the next one is requested — no full buffering.

        Implementations must:
        - Respect per-source rate limits (asyncio.sleep for jitter)
        - Use realistic browser headers
        - Apply per-source normalization before yielding
        - Not raise on a single listing parse failure (log + continue)
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the source is reachable, False otherwise."""
        ...
