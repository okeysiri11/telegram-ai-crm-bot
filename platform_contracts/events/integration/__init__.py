"""Integration events — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass

from platform_contracts.events.base import BaseEvent


@dataclass
class SyncStartedEvent(BaseEvent):
    event_type: str = "integration.sync.started"


@dataclass
class SyncCompletedEvent(BaseEvent):
    event_type: str = "integration.sync.completed"
