-- ============================================================
-- Migration 002: Enrichment result cache
-- Caches Nadlan/GovMap results keyed by normalized address hash.
-- TTL enforced via expires_at; a background job or ON CONFLICT
-- handles eviction.
-- ============================================================

CREATE TABLE enrichment_cache (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key  VARCHAR(256) NOT NULL UNIQUE,
    source     VARCHAR(64) NOT NULL,
    result     JSONB NOT NULL,
    cached_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_enrichment_expires ON enrichment_cache(expires_at);
CREATE INDEX idx_enrichment_key     ON enrichment_cache(cache_key);
