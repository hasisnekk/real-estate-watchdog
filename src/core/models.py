"""
Core data models for the real-estate watchdog.

RawListing  — flexible model yielded by every source adapter.
              Fields may be None if the source doesn't provide them.

Listing     — canonical, normalized model stored in PostgreSQL.
              All fields that are "known" are populated; price is required.

ListingEvent — one row in listing_events for audit trail.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# RawListing — adapter output (loose types, many optional fields)
# ---------------------------------------------------------------------------


class RawListing(BaseModel):
    """Raw listing as returned by a source adapter — mirrors the source's schema."""

    source_name: str
    source_id: Optional[str] = None
    source_url: Optional[str] = None

    title: Optional[str] = None
    description: Optional[str] = None

    city: Optional[str] = None
    neighborhood: Optional[str] = None
    street: Optional[str] = None
    street_number: Optional[str] = None

    floor: Optional[int] = None
    total_floors: Optional[int] = None
    rooms: Optional[float] = None
    has_storage: Optional[bool] = None
    area_sqm: Optional[int] = None

    price: Optional[int] = None
    price_currency: str = "ILS"

    has_mamad: Optional[bool] = None
    has_elevator: Optional[bool] = None
    has_parking: Optional[bool] = None
    parking_type: Optional[str] = None
    has_balcony: Optional[bool] = None
    has_garden: Optional[bool] = None
    has_roof: Optional[bool] = None
    is_long_term: Optional[bool] = None

    image_urls: list[str] = Field(default_factory=list)
    contact_phone_raw: Optional[str] = None
    is_agency: Optional[bool] = None

    raw_payload: Optional[dict[str, Any]] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Listing — canonical normalized model (stored in DB)
# ---------------------------------------------------------------------------


class Listing(BaseModel):
    """Canonical listing model — fully normalized, ready for DB upsert."""

    # DB primary key (set after insert)
    id: Optional[UUID] = None

    # Dedup key: sha256(f"{source_name}:{source_id}") for Level-1 dedup
    canonical_id: str

    # Source
    source_name: str
    source_id: Optional[str] = None
    source_url: Optional[str] = None

    # Content
    title: Optional[str] = None
    description: Optional[str] = None

    # Location
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    street: Optional[str] = None
    street_number: Optional[str] = None

    # Physical
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    rooms: Optional[float] = None
    has_storage: Optional[bool] = None
    area_sqm: Optional[int] = None

    # Price
    price: int
    price_currency: str = "ILS"

    # Amenities
    has_mamad: Optional[bool] = None
    has_elevator: Optional[bool] = None
    has_parking: Optional[bool] = None
    parking_type: Optional[str] = None
    has_balcony: Optional[bool] = None
    has_garden: Optional[bool] = None
    has_roof: Optional[bool] = None
    is_long_term: Optional[bool] = None

    # Images
    image_urls: list[str] = Field(default_factory=list)
    image_count: int = 0

    # Contact (stored but never logged/sent to Discord)
    contact_phone_raw: Optional[str] = None
    contact_phone_hash: Optional[str] = None

    is_agency: Optional[bool] = None
    raw_payload: Optional[dict[str, Any]] = None

    # Scoring (populated by scoring engine)
    score: Optional[int] = None
    score_breakdown: Optional[dict[str, Any]] = None

    # Status
    status: str = "active"

    # Building enrichment (populated by enrichment pipeline)
    building_year_built: Optional[int] = None
    building_age_estimate: Optional[int] = None
    building_age_confidence: str = "unknown"
    enrichment_data: dict[str, Any] = Field(default_factory=dict)

    # Timestamps (set by DB or pipeline)
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    notified_at: Optional[datetime] = None

    @model_validator(mode="after")
    def _compute_derived_fields(self) -> "Listing":
        # Sync image_count with image_urls length
        self.image_count = len(self.image_urls)

        # Hash phone for dedup/logging (never store raw in logs)
        if self.contact_phone_raw and not self.contact_phone_hash:
            self.contact_phone_hash = hashlib.sha256(
                self.contact_phone_raw.encode()
            ).hexdigest()[:16]
        return self

    @property
    def has_outdoor_space(self) -> bool:
        return bool(self.has_balcony or self.has_garden or self.has_roof)

    @property
    def has_images(self) -> bool:
        return self.image_count > 0

    @property
    def effective_rooms(self) -> Optional[float]:
        if self.rooms is None:
            return None
        return self.rooms + (0.5 if self.has_storage else 0.0)


# ---------------------------------------------------------------------------
# ListingEvent — one row in listing_events
# ---------------------------------------------------------------------------


class ListingEvent(BaseModel):
    """An event that occurred to a listing (first_seen, price_dropped, etc.)."""

    listing_id: UUID
    event_type: str
    old_value: Optional[dict[str, Any]] = None
    new_value: Optional[dict[str, Any]] = None
    source_name: Optional[str] = None
    occurred_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# ScoreBreakdown — what scoring.py produces
# ---------------------------------------------------------------------------


class ScoreBreakdown(BaseModel):
    price_penalty: int = 0
    rooms_bonus: int = 0
    mamad: int = 0
    elevator: int = 0
    parking: int = 0
    balcony: int = 0
    garden: int = 0
    roof: int = 0
    long_term_rental: int = 0
    building_age: int = 0
    young_neighborhood: int = 0
    total: int = 0
    must_have_passed: bool = True
    reject_reason: Optional[str] = None

    def compute_total(self) -> int:
        self.total = (
            self.price_penalty
            + self.rooms_bonus
            + self.mamad
            + self.elevator
            + self.parking
            + self.balcony
            + self.garden
            + self.roof
            + self.long_term_rental
            + self.building_age
            + self.young_neighborhood
        )
        return self.total
