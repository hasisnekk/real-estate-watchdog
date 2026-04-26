"""
Configuration loader: dynaconf reads YAML files, pydantic v2 validates the schema.

Load order (highest priority wins):
  1. Environment variables (DATABASE_URL, DISCORD_*_WEBHOOK_URL, etc.)
  2. .secrets.yaml  (not committed to git)
  3. config/scoring.yaml
  4. config/default.yaml

Usage:
    from src.core.config import load_config
    app_cfg, scoring_cfg = load_config()
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from dynaconf import Dynaconf
from pydantic import BaseModel, Field, model_validator

# ---------------------------------------------------------------------------
# dynaconf instance — reads YAML + env vars
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).parent.parent.parent  # repo root

_settings = Dynaconf(
    root_path=str(_ROOT),
    settings_files=["config/default.yaml", "config/scoring.yaml"],
    secrets=".secrets.yaml",
    environments=False,
    load_dotenv=True,
    dotenv_path=str(_ROOT / ".env"),
)


# ---------------------------------------------------------------------------
# Pydantic models — AppConfig
# ---------------------------------------------------------------------------


class BudgetConfig(BaseModel):
    preferred_nis: int = 7500
    target_nis: int = 8000
    soft_max_nis: int = 8500
    hard_max_nis: Optional[int] = None


class RoomsConfig(BaseModel):
    min: float = 4.0
    max: float = 5.5
    storage_room_counts_as_half: bool = True


class MustHaveConfig(BaseModel):
    mamad: bool = True
    elevator: bool = True
    images_required: bool = True
    outdoor_space: bool = True


class ParkingConfig(BaseModel):
    required: bool = False
    scoring_weight: bool = True


class BuildingConfig(BaseModel):
    prefer_new: bool = True
    max_age_years: int = 3
    reject_if_unknown: bool = False


class CityConfig(BaseModel):
    name: str
    neighborhoods: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class YoungNeighborhoodConfig(BaseModel):
    city: str
    neighborhood: str


class SourceConfig(BaseModel):
    name: str
    enabled: bool = False
    adapter: str
    schedule: Optional[str] = None
    jitter_seconds: int = 0
    batch_limit: int = 15
    seed_file: Optional[str] = None
    row_delay_seconds: float = 0.1
    actor_id: Optional[str] = None


class SearchConfig(BaseModel):
    transaction_type: str = "rent"
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    rooms: RoomsConfig = Field(default_factory=RoomsConfig)
    must_have: MustHaveConfig = Field(default_factory=MustHaveConfig)
    parking: ParkingConfig = Field(default_factory=ParkingConfig)
    building: BuildingConfig = Field(default_factory=BuildingConfig)
    include_agency_listings: bool = True
    include_private_listings: bool = True
    cities: list[CityConfig] = Field(default_factory=list)
    young_neighborhoods: list[YoungNeighborhoodConfig] = Field(default_factory=list)
    sources: list[SourceConfig] = Field(default_factory=list)
    known_new_projects: list[str] = Field(default_factory=list)


class EnrichmentSourceConfig(BaseModel):
    enabled: bool = True
    cache_ttl_hours: int = 168


class EnrichmentConfig(BaseModel):
    enabled: bool = True
    nadlan_gov_il: EnrichmentSourceConfig = Field(default_factory=EnrichmentSourceConfig)
    govmap: EnrichmentSourceConfig = Field(default_factory=EnrichmentSourceConfig)


class DiscordConfig(BaseModel):
    enabled: bool = True
    urgent_webhook_url: Optional[str] = None
    normal_webhook_url: Optional[str] = None
    error_webhook_url: Optional[str] = None
    batch_delay_seconds: int = 300
    max_images_in_embed: int = 3

    @model_validator(mode="after")
    def _inject_env_urls(self) -> "DiscordConfig":
        """Override null webhook URLs with values from environment variables."""
        if not self.urgent_webhook_url:
            self.urgent_webhook_url = os.environ.get("DISCORD_URGENT_WEBHOOK_URL") or None
        if not self.normal_webhook_url:
            self.normal_webhook_url = os.environ.get("DISCORD_NORMAL_WEBHOOK_URL") or None
        if not self.error_webhook_url:
            self.error_webhook_url = os.environ.get("DISCORD_ERROR_WEBHOOK_URL") or None
        return self


class NotificationsConfig(BaseModel):
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    notify_on_events: list[str] = Field(
        default_factory=lambda: [
            "first_seen",
            "price_dropped",
            "images_added",
            "returned_to_market",
            "enrichment_updated_score",
        ]
    )


class PersistenceConfig(BaseModel):
    save_raw_payload: bool = True
    store_image_urls: bool = True
    download_images: bool = False


class AppConfig(BaseModel):
    search: SearchConfig = Field(default_factory=SearchConfig)
    enrichment: EnrichmentConfig = Field(default_factory=EnrichmentConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)

    @property
    def enabled_sources(self) -> list[SourceConfig]:
        return [s for s in self.search.sources if s.enabled]


# ---------------------------------------------------------------------------
# Pydantic models — ScoringConfig
# ---------------------------------------------------------------------------


class PriceScoringConfig(BaseModel):
    baseline_nis: int = 8000
    penalty_per_50_above_baseline: int = 1
    soft_reject_above_nis: int = 8500
    hard_reject_above_nis: Optional[int] = None


class RoomsScoringConfig(BaseModel):
    by_effective_rooms: dict[str, int] = Field(
        default_factory=lambda: {"4.0": 0, "4.5": 20, "5.0": 20, "5.5": 15}
    )
    below_4_score: int = -20
    above_5_5_score: int = 10

    def score_for(self, effective_rooms: float) -> int:
        key = f"{round(effective_rooms * 2) / 2:.1f}"
        if effective_rooms < 4.0:
            return self.below_4_score
        if effective_rooms > 5.5:
            return self.above_5_5_score
        return self.by_effective_rooms.get(key, 0)


class AmenitiesScoringConfig(BaseModel):
    mamad: int = 10
    elevator: int = 10
    parking: int = 10
    balcony: int = 10
    garden: int = 10
    roof: int = 10
    long_term_rental: int = 10


class BuildingAgeScoringConfig(BaseModel):
    new_threshold_years: int = 3
    score_new_verified: int = 20
    score_new_estimated: int = 12
    score_unknown: int = 0
    score_old_verified: int = -5


class NeighborhoodScoringConfig(BaseModel):
    young_family_oriented: int = 10


class NotificationThresholdsConfig(BaseModel):
    urgent_score_threshold: int = 60
    normal_score_threshold: int = 30


class ScoringConfig(BaseModel):
    price: PriceScoringConfig = Field(default_factory=PriceScoringConfig)
    rooms: RoomsScoringConfig = Field(default_factory=RoomsScoringConfig)
    amenities: AmenitiesScoringConfig = Field(default_factory=AmenitiesScoringConfig)
    building_age: BuildingAgeScoringConfig = Field(default_factory=BuildingAgeScoringConfig)
    neighborhood: NeighborhoodScoringConfig = Field(default_factory=NeighborhoodScoringConfig)
    must_have: list[str] = Field(
        default_factory=lambda: ["mamad", "elevator", "has_images", "outdoor_space"]
    )
    notification: NotificationThresholdsConfig = Field(
        default_factory=NotificationThresholdsConfig
    )


# ---------------------------------------------------------------------------
# Infra config (env-only, not from YAML)
# ---------------------------------------------------------------------------


class InfraConfig(BaseModel):
    database_url: str
    redis_url: str
    apify_api_token: Optional[str] = None
    log_level: str = "info"


# ---------------------------------------------------------------------------
# Public loader
# ---------------------------------------------------------------------------


def _dynaconf_to_plain(obj: Any) -> Any:
    """Recursively convert dynaconf DynaBox / LazySettings to plain Python types."""
    if hasattr(obj, "to_dict"):
        return _dynaconf_to_plain(obj.to_dict())
    if isinstance(obj, dict):
        # Keys may be floats (e.g. by_effective_rooms: {4.0: 0, 4.5: 20, ...})
        # — only lowercase string keys, leave numeric keys as-is.
        return {
            (k.lower() if isinstance(k, str) else str(k)): _dynaconf_to_plain(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_dynaconf_to_plain(i) for i in obj]
    return obj


def load_config() -> tuple[AppConfig, ScoringConfig, InfraConfig]:
    """
    Load and validate all configuration.

    Returns:
        app_cfg:     search, enrichment, notifications, persistence settings
        scoring_cfg: all scoring weights and thresholds
        infra_cfg:   DB URL, Redis URL, API tokens (from env vars only)
    """
    raw = _dynaconf_to_plain(_settings.as_dict())

    # Separate scoring from the main config dict
    scoring_raw = raw.pop("scoring", {})

    app_cfg = AppConfig.model_validate(raw)
    scoring_cfg = ScoringConfig.model_validate(scoring_raw)
    infra_cfg = InfraConfig(
        database_url=os.environ.get(
            "DATABASE_URL",
            "postgresql://watchdog:watchdog@localhost:5432/watchdog",
        ),
        redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        apify_api_token=os.environ.get("APIFY_API_TOKEN") or None,
        log_level=os.environ.get("LOG_LEVEL", "info").lower(),
    )

    return app_cfg, scoring_cfg, infra_cfg
