"""
Database repository — all DB read/write operations for listings.

Implemented in Milestone 3.

Operations:
  upsert_listing()   — INSERT or UPDATE listings, save snapshot, create event
  save_snapshot()    — write/replace listing_snapshots row (one per listing)
  create_event()     — append to listing_events
  get_listing()      — fetch by canonical_id
  mark_stale()       — set status=stale for listings not seen in 48h
  mark_removed()     — set status=removed for listings not seen in 96h
  create_source_run() — record a source_runs row at job start
  complete_source_run() — update source_runs row at job end
  queue_notification() — insert into notification_queue
  flush_notification_queue() — read pending rows, mark sent
"""

from __future__ import annotations

import structlog
from asyncpg import Pool

from src.core.models import Listing, ListingEvent

logger = structlog.get_logger(__name__)


class Repository:
    """All database operations. Implemented in Milestone 3."""

    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    async def upsert_listing(self, listing: Listing) -> tuple[str, Listing]:
        """
        Insert a new listing or update an existing one.

        Returns:
            ("new", listing)      — first time this canonical_id was seen
            ("updated", listing)  — existing listing was updated
            ("unchanged", listing)— no fields changed

        Saves a snapshot before updating (for change detection).
        Creates listing_events for first_seen, price_dropped, images_added, etc.

        Implemented in Milestone 3.
        """
        raise NotImplementedError("Repository.upsert_listing() is implemented in Milestone 3.")

    async def get_listing_by_canonical_id(self, canonical_id: str) -> Listing | None:
        """Fetch a listing by its canonical_id. Implemented in Milestone 3."""
        raise NotImplementedError("Implemented in Milestone 3.")

    async def create_source_run(self, source_name: str) -> str:
        """Insert a source_runs row with status=running. Returns the UUID."""
        raise NotImplementedError("Implemented in Milestone 3.")

    async def complete_source_run(
        self,
        run_id: str,
        status: str,
        listings_fetched: int,
        listings_new: int,
        listings_updated: int,
        error_message: str | None = None,
        apify_run_id: str | None = None,
    ) -> None:
        """Update a source_runs row on completion. Implemented in Milestone 3."""
        raise NotImplementedError("Implemented in Milestone 3.")
