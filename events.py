# Unified Event Bus — centralized event registry and pub/sub for BIDEX platform.

from __future__ import annotations

import json
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Callable

EVENT_STATUSES = (
    "PUBLISHED",
    "DELIVERING",
    "DELIVERED",
    "PARTIAL",
    "FAILED",
    "REPLAYED",
)

# ---------------------------------------------------------------------------
# Event type registry
# ---------------------------------------------------------------------------

EVENT_REGISTRY: dict[str, dict[str, str]] = {
    "AGRO_REQUEST_CREATED": {
        "module": "agro_trading",
        "entity_type": "request",
        "description": "Новая Agro заявка создана",
    },
    "AGRO_REQUEST_ASSIGNED": {
        "module": "agro_trading",
        "entity_type": "request",
        "description": "Agro заявка назначена менеджеру",
    },
    "AGRO_REQUEST_STATUS_CHANGED": {
        "module": "agro_trading",
        "entity_type": "request",
        "description": "Статус Agro заявки изменён",
    },
    "AUTO_LEAD_CREATED": {
        "module": "automotive",
        "entity_type": "lead",
        "description": "Новый автомобильный лид",
    },
    "AUTO_PAYMENT_RECEIVED": {
        "module": "automotive",
        "entity_type": "payment",
        "description": "Авто: оплата получена",
    },
    "AUTO_TRADEIN_STARTED": {
        "module": "automotive",
        "entity_type": "tradein",
        "description": "Авто: trade-in запущен",
    },
    "FINANCE_PAYMENT_CONFIRMED": {
        "module": "finance",
        "entity_type": "transaction",
        "description": "Финансовый платёж подтверждён",
    },
    "FINANCE_COMMISSION_PAID": {
        "module": "finance",
        "entity_type": "transaction",
        "description": "Комиссия выплачена",
    },
    "LEGAL_CASE_CREATED": {
        "module": "law",
        "entity_type": "case",
        "description": "Юридическое дело создано",
    },
    "DRONE_PROJECT_CREATED": {
        "module": "drone",
        "entity_type": "project",
        "description": "Drone проект создан",
    },
    "TASK_CREATED": {
        "module": "system",
        "entity_type": "task",
        "description": "Задача создана",
    },
    "CALENDAR_EVENT_CREATED": {
        "module": "calendar",
        "entity_type": "event",
        "description": "Событие календаря создано",
    },
    "USER_CREATED": {
        "module": "users",
        "entity_type": "user",
        "description": "Пользователь зарегистрирован",
    },
    "DEAL_CREATED": {
        "module": "deals",
        "entity_type": "deal",
        "description": "Универсальная сделка создана",
    },
    "DEAL_STATUS_CHANGED": {
        "module": "deals",
        "entity_type": "deal",
        "description": "Статус сделки изменён",
    },
    "DEAL_COMPLETED": {
        "module": "deals",
        "entity_type": "deal",
        "description": "Сделка завершена",
    },
}

SubscriberHandler = Callable[["PlatformEvent"], None]

_subscribers: dict[str, list[tuple[str, SubscriberHandler]]] = {}
_registered = False


@dataclass
class PlatformEvent:
    event_type: str
    module: str
    entity_type: str
    entity_id: int | str | None
    user_id: int
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: int | None = None
    created_at: str | None = None
    status: str = "PUBLISHED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: tuple) -> PlatformEvent:
        (
            event_id, event_type, module, entity_type, entity_id,
            user_id, payload_json, created_at, status,
        ) = row
        payload = json.loads(payload_json) if payload_json else {}
        return cls(
            event_id=event_id,
            event_type=event_type,
            module=module,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            payload=payload,
            created_at=created_at,
            status=status or "PUBLISHED",
        )


class EventBus:
    """Internal publish/subscribe bus with persistence and replay."""

    @staticmethod
    def register_event_type(
        event_type: str,
        module: str,
        entity_type: str,
        description: str = "",
    ) -> None:
        EVENT_REGISTRY[event_type] = {
            "module": module,
            "entity_type": entity_type,
            "description": description,
        }

    @staticmethod
    def subscribe(
        event_type: str,
        handler: SubscriberHandler,
        subscriber_id: str | None = None,
    ) -> None:
        event_type = event_type.strip().upper()
        sid = subscriber_id or handler.__name__
        _subscribers.setdefault(event_type, [])
        for existing_id, _ in _subscribers[event_type]:
            if existing_id == sid:
                return
        _subscribers[event_type].append((sid, handler))

    @staticmethod
    def unsubscribe(event_type: str, subscriber_id: str) -> bool:
        event_type = event_type.strip().upper()
        handlers = _subscribers.get(event_type, [])
        before = len(handlers)
        _subscribers[event_type] = [
            (sid, fn) for sid, fn in handlers if sid != subscriber_id
        ]
        return len(_subscribers.get(event_type, [])) < before

    @staticmethod
    def list_subscribers(event_type: str | None = None) -> dict[str, list[str]]:
        if event_type:
            key = event_type.strip().upper()
            return {key: [sid for sid, _ in _subscribers.get(key, [])]}
        return {
            et: [sid for sid, _ in handlers]
            for et, handlers in _subscribers.items()
        }

    @staticmethod
    def publish(
        event_type: str,
        user_id: int,
        entity_type: str | None = None,
        entity_id: int | str | None = None,
        payload: dict | None = None,
        module: str | None = None,
        *,
        replay: bool = False,
        source_event_id: int | None = None,
    ) -> int:
        EventBus._ensure_subscribers()

        event_type = event_type.strip().upper()
        meta = EVENT_REGISTRY.get(event_type)
        if not meta:
            raise ValueError(f"Unknown event type: {event_type}")

        payload = payload or {}
        module = module or meta["module"]
        entity_type = entity_type or meta["entity_type"]
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        status = "REPLAYED" if replay else "PUBLISHED"

        event = PlatformEvent(
            event_type=event_type,
            module=module,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            payload=payload,
            created_at=now,
            status=status,
        )

        from database import insert_platform_event, update_platform_event_status, log_audit

        event.event_id = insert_platform_event(event, replay_of=source_event_id)
        update_platform_event_status(event.event_id, "DELIVERING")

        handlers = _subscribers.get(event_type, [])
        delivered = 0
        errors: list[str] = []

        for sid, handler in handlers:
            try:
                handler(event)
                delivered += 1
            except Exception as exc:
                errors.append(f"{sid}: {exc}")

        if not handlers:
            final_status = "DELIVERED"
        elif errors and delivered == 0:
            final_status = "FAILED"
        elif errors:
            final_status = "PARTIAL"
        else:
            final_status = "DELIVERED"

        update_platform_event_status(
            event.event_id,
            final_status,
            delivery_errors="; ".join(errors) if errors else None,
        )
        event.status = final_status

        action = "event_replay" if replay else "event_publish"
        log_audit(
            user_id,
            action,
            "event_bus",
            f"{event_type}|id={event.event_id}|status={final_status}|subs={delivered}/{len(handlers)}",
        )
        return event.event_id

    @staticmethod
    def replay(event_id: int, user_id: int | None = None) -> int | None:
        from database import get_platform_event

        row = get_platform_event(event_id)
        if not row:
            return None
        original = PlatformEvent.from_row(row)
        return EventBus.publish(
            original.event_type,
            user_id or original.user_id,
            entity_type=original.entity_type,
            entity_id=original.entity_id,
            payload={**original.payload, "_replay_of": event_id},
            module=original.module,
            replay=True,
            source_event_id=event_id,
        )

    @staticmethod
    def get_event(event_id: int) -> PlatformEvent | None:
        from database import get_platform_event
        row = get_platform_event(event_id)
        return PlatformEvent.from_row(row) if row else None

    @staticmethod
    def list_events(
        event_type: str | None = None,
        module: str | None = None,
        limit: int = 50,
    ) -> list[PlatformEvent]:
        from database import list_platform_events
        rows = list_platform_events(event_type=event_type, module=module, limit=limit)
        return [PlatformEvent.from_row(r) for r in rows]

    @staticmethod
    def _ensure_subscribers() -> None:
        global _registered
        if _registered:
            return
        import importlib.util
        from pathlib import Path
        bridge_path = Path(__file__).resolve().parent / "services" / "event_bus_bridge.py"
        spec = importlib.util.spec_from_file_location("event_bus_bridge", bridge_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register_default_subscribers()
        _registered = True


def reset_event_bus_for_tests() -> None:
    """Clear subscribers and registration flag (tests only)."""
    global _registered
    _subscribers.clear()
    _registered = False
