# Generic platform events — string-typed events from legacy/CRM/outbox sources.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class GenericPlatformEvent(BaseEvent):
    """String-typed event routed through PlatformEventBus."""

    name: str
    source: str = "platform"
    user_id: int | None = None
    module: str | None = None
    entity_type: str | None = None
    entity_id: int | str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    aggregate_type: str | None = None
    aggregate_id: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None

    @property
    def event_type(self) -> str:
        return self.name

    @classmethod
    def from_legacy(
        cls,
        *,
        event_type: str,
        user_id: int,
        module: str | None,
        entity_type: str | None,
        entity_id: int | str | None,
        payload: dict[str, Any] | None,
        legacy_event_id: int | None = None,
    ) -> GenericPlatformEvent:
        data = dict(payload or {})
        if legacy_event_id is not None:
            data["legacy_event_id"] = legacy_event_id
        return cls(
            name=event_type.strip().upper(),
            source="legacy",
            user_id=user_id,
            module=module,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=data,
        )

    @classmethod
    def from_crm(
        cls,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: UUID,
        payload: dict[str, Any] | None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
        crm_event_id: UUID | None = None,
    ) -> GenericPlatformEvent:
        data = dict(payload or {})
        if crm_event_id is not None:
            data["crm_event_id"] = str(crm_event_id)
        return cls(
            name=event_type,
            source="crm",
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            payload=data,
            correlation_id=str(correlation_id) if correlation_id else None,
            causation_id=str(causation_id) if causation_id else None,
        )
