"""
Normalizer: RawListing → Listing (canonical model).

Responsibilities:
- Compute canonical_id: sha256(f"{source_name}:{source_id}") for Level-1 dedup
- Normalize city and neighborhood names (Hebrew-aware, canonical map)
- Normalize street names and strip apartment numbers
- Parse rooms from strings ("4.5 חד'" → 4.5)
- Parse price from strings ("8,000 ₪" → 8000)
- Detect outdoor space presence (balcony OR garden OR roof)
- Hash contact phone for privacy
- Strip and normalize whitespace from all text fields

Full implementation in Milestone 2.
"""

from __future__ import annotations

import hashlib

from src.core.models import Listing, RawListing


def compute_canonical_id(source_name: str, source_id: str | None, source_url: str | None) -> str:
    """
    Level-1 dedup key: sha256 of source identity.

    Priority:
    1. sha256(f"{source_name}:{source_id}")  — when source_id is available
    2. sha256(normalized_url)                — when only URL is available
    """
    if source_id:
        raw = f"{source_name}:{source_id}"
    elif source_url:
        # URL normalization: strip UTM params, trailing slashes
        normalized = _normalize_url(source_url)
        raw = f"{source_name}:url:{normalized}"
    else:
        raise ValueError(
            f"Cannot compute canonical_id for source '{source_name}': "
            "both source_id and source_url are None."
        )
    return hashlib.sha256(raw.encode()).hexdigest()


def _normalize_url(url: str) -> str:
    """Strip UTM params, trailing slashes, and tracking tokens."""
    from urllib.parse import urlparse, urlencode, urlunparse, parse_qs

    parsed = urlparse(url)
    # Remove UTM and other tracking params
    _TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}
    qs = {k: v for k, v in parse_qs(parsed.query).items() if k not in _TRACKING_PARAMS}
    normalized = urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))
    return normalized.rstrip("/")


def normalize(raw: RawListing) -> Listing:
    """
    Convert a RawListing to a canonical Listing.

    Full implementation in Milestone 2 (handles Hebrew parsing, city normalization,
    room string parsing, price string parsing, etc.).
    """
    raise NotImplementedError(
        "normalizer.normalize() is implemented in Milestone 2."
    )
