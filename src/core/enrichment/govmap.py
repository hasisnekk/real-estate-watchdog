"""
GovMap Address → Parcel Lookup — Phase 2 (M7).

Converts a normalized Hebrew address into a gush/helka (parcel identifier)
which is then used by the Nadlan enricher to fetch transaction history.

Full implementation in Milestone 7.
"""

from __future__ import annotations

import structlog

from src.core.enrichment.base import BaseEnricher
from src.core.models import Listing

logger = structlog.get_logger(__name__)


class GovMapLookup(BaseEnricher):
    """Address-to-parcel resolution via GovMap API — implemented in M7."""

    name = "govmap"

    async def enrich(self, listing: Listing) -> Listing:
        raise NotImplementedError("GovMapLookup is implemented in Milestone 7.")
