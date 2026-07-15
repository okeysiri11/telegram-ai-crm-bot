# Domain domain event types + in-process dispatcher (scaffold).
# Does NOT replace legacy events.py or services/crm_event_bus.py.

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Protocol
import logging
import uuid

logger = logging.getLogger(__name__)

EventHandler = Callable[["DomainEvent"], Awaitable[None] | None]


@dataclass
class DomainEvent:
    """Base domain event."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return self.__class__.__name__

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["event_type"] = self.event_type
        return data


@dataclass
class LeadCreated(DomainEvent):
    lead_id: str = ""
    request_number: str = ""
    request_type: str = ""
    client_telegram_id: int | None = None


@dataclass
class LeadAssigned(DomainEvent):
    lead_id: str = ""
    request_number: str = ""
    manager_id: str = ""


@dataclass
class LeadClosed(DomainEvent):
    lead_id: str = ""
    request_number: str = ""
    status: str = ""


@dataclass
class ClientCreated(DomainEvent):
    client_telegram_id: int | None = None
    username: str | None = None


@dataclass
class ManagerAssigned(DomainEvent):
    request_number: str = ""
    manager_id: str = ""
    manager_telegram_id: int | None = None


@dataclass
class PhotoUploaded(DomainEvent):
    request_number: str = ""
    file_ids: list[str] = field(default_factory=list)
    count: int = 0


class EventDispatcher:
    """In-process async/sync dispatcher — scaffold, not wired to production paths."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def subscribe_type(self, event_cls: type[DomainEvent], handler: EventHandler) -> None:
        self.subscribe(event_cls.__name__, handler)

    async def dispatch(self, event: DomainEvent) -> dict[str, Any]:
        handlers = list(self._handlers.get(event.event_type, []))
        # Also notify wildcard subscribers
        handlers.extend(self._handlers.get("*", []))
        errors: list[str] = []
        for handler in handlers:
            try:
                result = handler(event)
                if hasattr(result, "__await__"):
                    await result  # type: ignore[misc]
            except Exception as exc:
                logger.warning("Event handler failed type=%s err=%s", event.event_type, exc)
                errors.append(str(exc))
        return {
            "event_type": event.event_type,
            "handlers": len(handlers),
            "errors": errors,
            "ok": not errors,
        }

    def list_subscriptions(self) -> dict[str, int]:
        return {k: len(v) for k, v in self._handlers.items()}


_DISPATCHER: EventDispatcher | None = None


def get_dispatcher() -> EventDispatcher:
    global _DISPATCHER
    if _DISPATCHER is None:
        _DISPATCHER = EventDispatcher()
    return _DISPATCHER


# Re-export convenience
__all__ = [
    "DomainEvent",
    "LeadCreated",
    "LeadAssigned",
    "LeadClosed",
    "ClientCreated",
    "ManagerAssigned",
    "PhotoUploaded",
    "EventDispatcher",
    "get_dispatcher",
]
