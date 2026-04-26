"""
Unit tests for the deduplication engine.

Full implementation in Milestone 3 alongside dedup.py.
Tests validate all 4 dedup levels with fixture listings.
"""

import pytest


class TestDedupLevel1:
    """Level 1: same source, same source_id → exact duplicate."""

    def test_same_source_id_is_duplicate(self):
        pytest.skip("Implemented in Milestone 3.")


class TestDedupLevel2:
    """Level 2: same normalized URL → duplicate."""

    def test_same_url_is_duplicate(self):
        pytest.skip("Implemented in Milestone 3.")


class TestDedupLevel3:
    """Level 3: cross-source address+attributes match."""

    def test_same_address_floor_rooms_price_is_high_confidence(self):
        pytest.skip("Implemented in Milestone 3.")


class TestDedupLevel4:
    """Level 4: cross-source phone+city+area match."""

    def test_same_phone_city_area_is_medium_confidence(self):
        pytest.skip("Implemented in Milestone 3.")

    def test_missing_area_skips_level4(self):
        pytest.skip("Implemented in Milestone 3.")
