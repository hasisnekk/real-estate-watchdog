"""
Abstract base class for enrichment sources.

Enrichment adds building age information to listings using government data:
  Step 0: Text heuristics (year regex + Hebrew keywords) — no network I/O
  Step 1: Normalize address
  Step 2: GovMap autocomplete → parcel ID
  Step 3: Nadlan transaction history → earliest sale year
  Step 4: Estimate construction year
  Step 5: Cache result (1-week TTL)

Full implementation in Milestone 7.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.models import Listing


class BaseEnricher(ABC):
    """Abstract base for enrichment sources."""

    name: str

    @abstractmethod
    async def enrich(self, listing: Listing) -> Listing:
        """
        Enrich a listing with additional data (e.g., building age).
        Returns the modified listing.
        """
        ...
