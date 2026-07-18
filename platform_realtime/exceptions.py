# Realtime core exceptions.

from __future__ import annotations


class RealtimeError(Exception):
    """Base realtime error."""


class RealtimePermissionError(RealtimeError):
    """Actor lacks permission for channel or action."""


class ChannelNotFoundError(RealtimeError):
    """Unknown channel name."""


class ConnectionNotFoundError(RealtimeError):
    """WebSocket connection not registered."""


class SubscriptionError(RealtimeError):
    """Invalid subscribe/unsubscribe request."""
