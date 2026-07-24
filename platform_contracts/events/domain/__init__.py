"""Domain events — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.events.base import BaseEvent


@dataclass
class EntityCreatedEvent(BaseEvent):
    event_type: str = "domain.entity.created"


@dataclass
class EntityUpdatedEvent(BaseEvent):
    event_type: str = "domain.entity.updated"


@dataclass
class EntityDeletedEvent(BaseEvent):
    event_type: str = "domain.entity.deleted"
