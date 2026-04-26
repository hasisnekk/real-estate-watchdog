-- ============================================================
-- Migration 001: Initial schema
-- Tables: listings, listing_snapshots, listing_events,
--         source_runs, dedup_matches, notification_queue
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Core listings table ────────────────────────────────────────────────────

CREATE TABLE listings (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_id            VARCHAR(64) NOT NULL UNIQUE,

    -- Source
    source_name             VARCHAR(64) NOT NULL,
    source_id               VARCHAR(256),
    source_url              TEXT,

    -- Content
    title                   TEXT,
    description             TEXT,

    -- Location
    city                    VARCHAR(128),
    neighborhood            VARCHAR(128),
    street                  VARCHAR(256),
    street_number           VARCHAR(32),

    -- Physical
    floor                   INTEGER,
    total_floors            INTEGER,
    rooms                   DECIMAL(4,1),
    has_storage             BOOLEAN,
    -- Computed column: effective_rooms for scoring queries
    effective_rooms         DECIMAL(4,1) GENERATED ALWAYS AS (
        CASE WHEN has_storage = TRUE THEN rooms + 0.5 ELSE rooms END
    ) STORED,
    area_sqm                INTEGER,

    -- Price
    price                   INTEGER NOT NULL,
    price_currency          CHAR(3) DEFAULT 'ILS',

    -- Amenities
    has_mamad               BOOLEAN,
    has_elevator            BOOLEAN,
    has_parking             BOOLEAN,
    parking_type            VARCHAR(64),
    has_balcony             BOOLEAN,
    has_garden              BOOLEAN,
    has_roof                BOOLEAN,
    is_long_term            BOOLEAN,

    -- Images
    image_urls              JSONB DEFAULT '[]',
    image_count             INTEGER DEFAULT 0,

    -- Contact (stored but never logged or sent to Discord)
    contact_phone_raw       TEXT,
    contact_phone_hash      VARCHAR(64),

    is_agency               BOOLEAN,
    raw_payload             JSONB,

    -- Scoring
    score                   INTEGER,
    score_breakdown         JSONB,

    -- Status
    status                  VARCHAR(16) DEFAULT 'active'
                            CHECK (status IN ('active', 'removed', 'stale')),

    -- Building enrichment
    building_year_built     INTEGER,
    building_age_estimate   INTEGER,
    building_age_confidence VARCHAR(16) DEFAULT 'unknown'
                            CHECK (building_age_confidence IN
                                   ('unknown', 'estimated', 'verified')),
    enrichment_data         JSONB DEFAULT '{}',

    -- Timestamps
    first_seen_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated_at         TIMESTAMPTZ,
    notified_at             TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_listings_status_score ON listings(score DESC) WHERE status = 'active';
CREATE INDEX idx_listings_city         ON listings(city);
CREATE INDEX idx_listings_source       ON listings(source_name, source_id);
CREATE INDEX idx_listings_first_seen   ON listings(first_seen_at DESC);
CREATE INDEX idx_listings_price        ON listings(price) WHERE status = 'active';
CREATE INDEX idx_listings_phone_hash   ON listings(contact_phone_hash)
                                       WHERE contact_phone_hash IS NOT NULL;

-- ── One previous snapshot per listing ─────────────────────────────────────

CREATE TABLE listing_snapshots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id      UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    price           INTEGER,
    image_count     INTEGER,
    image_urls      JSONB,
    score           INTEGER,
    score_breakdown JSONB,
    has_mamad       BOOLEAN,
    has_elevator    BOOLEAN,
    has_parking     BOOLEAN,
    has_balcony     BOOLEAN,
    has_garden      BOOLEAN,
    has_roof        BOOLEAN,
    status          VARCHAR(16),
    snapshotted_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- UNIQUE enforced: only one previous snapshot stored per listing
    UNIQUE(listing_id)
);

-- ── Full event log ─────────────────────────────────────────────────────────

CREATE TABLE listing_events (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id   UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    event_type   VARCHAR(64) NOT NULL,
    -- Valid event_type values:
    --   first_seen | updated | price_dropped | price_increased |
    --   images_added | returned_to_market | removed |
    --   notified | source_failed | enrichment_updated_score
    old_value    JSONB,
    new_value    JSONB,
    source_name  VARCHAR(64),
    occurred_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_events_listing_id ON listing_events(listing_id);
CREATE INDEX idx_events_type       ON listing_events(event_type);
CREATE INDEX idx_events_occurred   ON listing_events(occurred_at DESC);

-- ── Source run tracking (circuit breaker input, ops visibility) ────────────

CREATE TABLE source_runs (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name      VARCHAR(64) NOT NULL,
    started_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at     TIMESTAMPTZ,
    status           VARCHAR(16) DEFAULT 'running'
                     CHECK (status IN ('running', 'success', 'failed', 'partial')),
    listings_fetched INTEGER DEFAULT 0,
    listings_new     INTEGER DEFAULT 0,
    listings_updated INTEGER DEFAULT 0,
    error_message    TEXT,
    apify_run_id     VARCHAR(256)
);

CREATE INDEX idx_source_runs_name    ON source_runs(source_name);
CREATE INDEX idx_source_runs_started ON source_runs(started_at DESC);

-- ── Cross-source dedup link table ─────────────────────────────────────────

CREATE TABLE dedup_matches (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id_a UUID NOT NULL REFERENCES listings(id),
    listing_id_b UUID NOT NULL REFERENCES listings(id),
    confidence   VARCHAR(16) CHECK (confidence IN ('exact','high','medium','low')),
    match_reason TEXT,
    resolved_at  TIMESTAMPTZ,
    resolution   VARCHAR(16) CHECK (resolution IN ('same','different','pending')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(listing_id_a, listing_id_b)
);

-- ── Notification queue (batching normal-priority messages) ────────────────

CREATE TABLE notification_queue (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID NOT NULL REFERENCES listings(id),
    event_type VARCHAR(64) NOT NULL,
    channel    VARCHAR(16) NOT NULL CHECK (channel IN ('urgent','normal','error')),
    payload    JSONB NOT NULL,
    queued_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at    TIMESTAMPTZ,
    status     VARCHAR(16) DEFAULT 'pending'
               CHECK (status IN ('pending','sent','failed'))
);

CREATE INDEX idx_notif_pending ON notification_queue(queued_at) WHERE status = 'pending';
