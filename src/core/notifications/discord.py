"""
Discord Webhook Notifier — Phase 1 (M3).

Sends structured embeds to three Discord channels:
  #urgent-deals       (score >= 60, sent immediately)
  #apartment-listings (score >= 30, batched every 5 minutes)
  #errors-alerts      (source failures, circuit breaker events)

Embed format:
  Title:  "4.5 rooms | 8,100 NIS | Petah Tikva - Em HaMoshavot"
  Color:  green (new), orange (price drop), blue (returned to market)
  Fields: floor, area, parking, mamad, elevator, balcony, building age, score
  Image:  first image URL (max 3 in footer)
  Footer: "Source: Komo | First seen: 2 minutes ago"
  URL:    link to original listing

Full implementation in Milestone 3 after Discord webhooks are created.
"""

from __future__ import annotations

import structlog

from src.core.notifications.base import BaseNotifier
from src.core.models import Listing, ListingEvent

logger = structlog.get_logger(__name__)

# Discord embed colors
COLOR_GREEN = 0x2ECC71   # new listing
COLOR_ORANGE = 0xE67E22  # price dropped
COLOR_BLUE = 0x3498DB    # returned to market
COLOR_PURPLE = 0x9B59B6  # enrichment updated
COLOR_RED = 0xE74C3C     # error


class DiscordNotifier(BaseNotifier):
    """Discord webhook notifier — implemented in Milestone 3."""

    def __init__(
        self,
        urgent_webhook_url: str | None,
        normal_webhook_url: str | None,
        error_webhook_url: str | None,
        batch_delay_seconds: int = 300,
        max_images: int = 3,
    ) -> None:
        self.urgent_url = urgent_webhook_url
        self.normal_url = normal_webhook_url
        self.error_url = error_webhook_url
        self.batch_delay_seconds = batch_delay_seconds
        self.max_images = max_images

    async def send_listing(self, listing: Listing, event: ListingEvent) -> bool:
        """Build and POST a Discord embed for the listing. Implemented in M3."""
        raise NotImplementedError("DiscordNotifier.send_listing() is implemented in Milestone 3.")

    async def send_error(self, source_name: str, error_message: str) -> bool:
        """POST an error embed to #errors-alerts. Implemented in M3."""
        raise NotImplementedError("DiscordNotifier.send_error() is implemented in Milestone 3.")

    async def flush_batch(self) -> int:
        """Flush pending normal-priority notifications from the DB queue. Implemented in M3."""
        raise NotImplementedError("DiscordNotifier.flush_batch() is implemented in Milestone 3.")
