"""
Must-have hard filter: discard listings that fail mandatory criteria.

Filters applied (from config.scoring.must_have):
  - mamad: has_mamad must be True
  - elevator: has_elevator must be True
  - has_images: image_count > 0
  - outdoor_space: has_balcony OR has_garden OR has_roof

If any must-have criterion is False or None → listing is discarded.
Returns a (passed: bool, reason: str | None) tuple.

Full implementation in Milestone 2.
"""

from __future__ import annotations

from src.core.models import Listing
from src.core.config import ScoringConfig


def must_have_filter(listing: Listing, scoring_cfg: ScoringConfig) -> tuple[bool, str | None]:
    """
    Apply must-have hard filters.

    Returns:
        (True, None)          — listing passes all must-have criteria
        (False, reason_str)   — listing fails; reason explains which criterion
    """
    raise NotImplementedError(
        "filter.must_have_filter() is implemented in Milestone 2."
    )
