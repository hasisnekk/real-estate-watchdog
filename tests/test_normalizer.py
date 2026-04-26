"""
Unit tests for the normalizer.

Full implementation in Milestone 2 alongside normalizer.py.
"""

import pytest


class TestCanonicalId:
    """compute_canonical_id is available in M1 — test it now."""

    def test_canonical_id_with_source_id(self):
        from src.core.normalizer import compute_canonical_id
        cid = compute_canonical_id("komo", "listing-123", None)
        assert len(cid) == 64  # sha256 hex digest
        assert cid == compute_canonical_id("komo", "listing-123", None)

    def test_canonical_id_with_url_only(self):
        from src.core.normalizer import compute_canonical_id
        url = "https://www.komo.co.il/listing/456?utm_source=google"
        cid = compute_canonical_id("komo", None, url)
        assert len(cid) == 64

    def test_canonical_id_strips_utm_params(self):
        from src.core.normalizer import compute_canonical_id
        url_clean = "https://www.komo.co.il/listing/456"
        url_with_utm = "https://www.komo.co.il/listing/456?utm_source=google&utm_campaign=x"
        cid_clean = compute_canonical_id("komo", None, url_clean)
        cid_utm = compute_canonical_id("komo", None, url_with_utm)
        assert cid_clean == cid_utm

    def test_raises_without_id_or_url(self):
        from src.core.normalizer import compute_canonical_id
        with pytest.raises(ValueError):
            compute_canonical_id("komo", None, None)


class TestNormalize:
    """Full normalize() tests — implemented in Milestone 2."""

    def test_raw_to_listing_basic(self):
        pytest.skip("Implemented in Milestone 2.")

    def test_hebrew_city_normalization(self):
        pytest.skip("Implemented in Milestone 2.")

    def test_price_string_parsing(self):
        pytest.skip("Implemented in Milestone 2.")
