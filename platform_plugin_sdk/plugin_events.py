# Plugin SDK event types — publish-only public events.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from events.base_event import BaseEvent


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PluginEvent:
    """Domain event published by a plugin."""

    plugin_id: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=_now)


@dataclass(kw_only=True)
class SdkPluginBusEvent(BaseEvent):
    """Platform EventBus envelope for plugin events."""

    plugin_id: str
    plugin_event_type: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginMetric:
    plugin_id: str
    name: str
    value: float
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now)


@dataclass
class PluginNotification:
    plugin_id: str
    title: str
    message: str
    severity: str = "info"
    timestamp: str = field(default_factory=_now)


@dataclass
class PluginHealth:
    plugin_id: str
    status: str
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now)
