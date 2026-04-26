"""
Nadlan.gov.il Enrichment — Phase 2 (M7).

Queries Nadlan's transaction history API to estimate building construction year.
The earliest recorded sale for a building proxy for its completion date.

Endpoints discovered via nitzpo/nadlan-mcp community research:
  GovMap autocomplete: address → gush/helka (parcel identifier)
  Nadlan transactions:  gush/helka → historical sales data

Both are public unauthenticated endpoints used by nadlan.gov.il internally.

Full implementation in Milestone 7.
"""

from __future__ import annotations

import structlog

from src.core.enrichment.base import BaseEnricher
from src.core.models import Listing

logger = structlog.get_logger(__name__)


class NadlanEnricher(BaseEnricher):
    """Estimates building age via Nadlan/GovMap API calls — implemented in M7."""

    name = "nadlan"

    async def enrich(self, listing: Listing) -> Listing:
        raise NotImplementedError("NadlanEnricher is implemented in Milestone 7.")
