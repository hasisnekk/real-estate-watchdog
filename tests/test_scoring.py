"""
Unit tests for the scoring engine.

These tests validate the exact formulas from the spec:
  - Price penalty: -floor((price - baseline) / 50)
  - Room score: by_effective_rooms table with storage-room bonus

Full test implementations added in Milestone 2 alongside scoring.py.
The price penalty and room score helper functions ARE implemented in M1
(in scoring.py) and are testable now.
"""

import pytest
from src.core.config import ScoringConfig
from src.core.scoring import compute_price_penalty, compute_room_score


@pytest.fixture
def scoring_cfg() -> ScoringConfig:
    return ScoringConfig()


class TestPricePenalty:
    """Validate compute_price_penalty against the spec examples."""

    def test_at_baseline_no_penalty(self, scoring_cfg):
        assert compute_price_penalty(8000, scoring_cfg) == 0

    def test_below_baseline_no_penalty(self, scoring_cfg):
        assert compute_price_penalty(7500, scoring_cfg) == 0

    def test_50_above_baseline(self, scoring_cfg):
        assert compute_price_penalty(8050, scoring_cfg) == -1

    def test_100_above_baseline(self, scoring_cfg):
        assert compute_price_penalty(8100, scoring_cfg) == -2

    def test_300_above_baseline(self, scoring_cfg):
        assert compute_price_penalty(8300, scoring_cfg) == -6

    def test_500_above_baseline(self, scoring_cfg):
        assert compute_price_penalty(8500, scoring_cfg) == -10

    def test_partial_50_rounds_down(self, scoring_cfg):
        # 8,075 → excess=75 → floor(75/50) = 1 → penalty -1
        assert compute_price_penalty(8075, scoring_cfg) == -1


class TestRoomScore:
    """Validate compute_room_score against the spec examples."""

    def test_4_rooms_no_storage_is_zero(self, scoring_cfg):
        """A 4-room apartment WITHOUT storage scores exactly 0."""
        assert compute_room_score(4.0, False, scoring_cfg) == 0

    def test_4_rooms_with_storage_scores_20(self, scoring_cfg):
        """4 rooms + storage room = 4.5 effective = +20."""
        assert compute_room_score(4.0, True, scoring_cfg) == 20

    def test_4_5_rooms_no_storage_scores_20(self, scoring_cfg):
        assert compute_room_score(4.5, False, scoring_cfg) == 20

    def test_5_rooms_no_storage_scores_20(self, scoring_cfg):
        assert compute_room_score(5.0, False, scoring_cfg) == 20

    def test_5_5_rooms_scores_15(self, scoring_cfg):
        assert compute_room_score(5.5, False, scoring_cfg) == 15

    def test_below_4_scores_negative(self, scoring_cfg):
        assert compute_room_score(3.0, False, scoring_cfg) == -20

    def test_above_5_5_scores_positive(self, scoring_cfg):
        assert compute_room_score(6.0, False, scoring_cfg) == 10
