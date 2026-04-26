"""
Abstract base class for notification channels.

The only notification channel in MVP is Discord webhooks.
This base exists to allow future channels (email, Telegram) without
changing the pipeline code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.models import Listing, ListingEvent


class BaseNotifier(ABC):
    """Abstract base for notification channels."""

    @abstractmethod
    async def send_listing(self, listing: Listing, event: ListingEvent) -> bool:
        """Send a notification for a listing event. Returns True on success."""
        ...

    @abstractmethod
    async def send_error(self, source_name: str, error_message: str) -> bool:
        """Send a source failure alert. Returns True on success."""
        ...

    @abstractmethod
    async def flush_batch(self) -> int:
        """
        Flush any batched (normal-priority) notifications.
        Returns the number of notifications sent.
        """
        ...
