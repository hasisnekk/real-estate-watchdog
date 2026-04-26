"""
Multi-level deduplication engine.

Level 1 — EXACT (same source):
  Key: sha256(f"{source_name}:{source_id}") == canonical_id
  → O(1) Redis lookup; if hit → update existing listing

Level 2 — URL:
  Key: sha256(normalized_url)
  → Used when source_id absent but URL is stable

Level 3 — ADDRESS+ATTRIBUTES (cross-source):
  city + normalized_street + floor + rooms + price (±500 NIS)
  → Creates dedup_matches record with confidence=high

Level 4 — WEAK DUPLICATE (cross-source, same agent):
  contact_phone_hash + city + area_sqm (±5 m²)
  → Creates dedup_matches record with confidence=medium
  → Skipped if area_sqm is missing on either listing

Level 5 — IMAGE URL OVERLAP (future):
  > 50% overlapping image URLs → confidence=low (not in MVP)

Full implementation in Milestone 3.
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


class DedupEngine:
    """Multi-level deduplication engine. Implemented in Milestone 3."""

    def __init__(self, db_pool, redis_pool) -> None:
        self.db_pool = db_pool
        self.redis_pool = redis_pool

    async def check(self, listing) -> tuple[str, str | None]:
        """
        Check if a listing is a duplicate.

        Returns:
            ("new", None)              — never seen before
            ("existing", listing_uuid) — exact match (update existing)
            ("cross_source", listing_uuid) — cross-source match (flag but keep)

        Implemented in Milestone 3.
        """
        raise NotImplementedError("DedupEngine.check() is implemented in Milestone 3.")
