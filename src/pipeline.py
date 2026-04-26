"""
Pipeline orchestrator — runs one full source cycle.

Full flow (implemented in M2 and M3):
  adapter.fetch(config)
    → normalizer.normalize(raw)
    → filter.must_have_filter(listing)
    → dedup.check(listing)
    → enrichment.enrich(listing)       [M7]
    → scoring.score(listing)
    → repository.upsert_listing(listing)
    → notifications.notify(listing)

M1 stub: this module exists so imports don't fail.
M2 will implement the CSV seed pipeline (console output only, no DB).
M3 will wire DB persistence, dedup, and Discord notifications.
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


async def run_source_once(source_name: str) -> None:
    """
    Manually trigger one full pipeline run for the given source.

    Used by: make run-source source=csv_seed
    Implemented in M2 (csv_seed) and M3 (komo + DB).
    """
    logger.warning(
        "pipeline_not_implemented",
        source=source_name,
        note="Pipeline will be implemented in Milestone 2 (csv_seed) and Milestone 3 (komo + DB)",
    )
    raise NotImplementedError(
        f"Pipeline for source '{source_name}' is not yet implemented. "
        "It will be built in Milestones 2 and 3."
    )
