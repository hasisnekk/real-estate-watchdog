"""
Scoring engine — assigns a numeric score to each listing.

Score = sum of individual components (see scoring.yaml for weights).

Components:
  price_penalty  = -floor((price - baseline_nis) / 50)  [only above baseline]
  rooms_bonus    = from by_effective_rooms table
  mamad          = +10 if has_mamad
  elevator       = +10 if has_elevator
  parking        = +10 if has_parking
  balcony        = +10 if has_balcony
  garden         = +10 if has_garden
  roof           = +10 if has_roof
  long_term      = +10 if is_long_term
  building_age   = +20 (verified new) / +12 (estimated new) / 0 (unknown) / -5 (old)
  neighborhood   = +10 if young-family-oriented neighborhood

Score thresholds (from scoring.yaml):
  >= 60 → send immediately to #urgent-deals
  >= 30 → batch to #apartment-listings
  < 30  → do not notify (still stored in DB)

Full implementation in Milestone 2 with unit tests.
"""

from __future__ import annotations

from src.core.config import ScoringConfig
from src.core.models import Listing, ScoreBreakdown


def compute_price_penalty(price: int, cfg: ScoringConfig) -> int:
    """
    Deduct exactly 1 point for every 50 NIS above the baseline.

    Examples (baseline = 8,000 NIS):
      8,050 NIS → floor(50/50)  = 1 → penalty -1
      8,100 NIS → floor(100/50) = 2 → penalty -2
      8,300 NIS → floor(300/50) = 6 → penalty -6
      8,500 NIS → floor(500/50) = 10 → penalty -10
    """
    if price <= cfg.price.baseline_nis:
        return 0
    excess = price - cfg.price.baseline_nis
    return -(excess // 50)


def compute_room_score(rooms: float, has_storage: bool, cfg: ScoringConfig) -> int:
    """
    Score based on effective_rooms = rooms + (0.5 if has_storage else 0).

    A 4-room apartment WITHOUT storage scores exactly 0 (not penalized, not rewarded).
    """
    effective = rooms + (0.5 if has_storage else 0.0)
    return cfg.rooms.score_for(effective)


def score_listing(listing: Listing, cfg: ScoringConfig) -> tuple[int, ScoreBreakdown]:
    """
    Compute the total score and breakdown for a listing.

    Full implementation in Milestone 2 (with unit tests).
    """
    raise NotImplementedError(
        "scoring.score_listing() is implemented in Milestone 2."
    )
