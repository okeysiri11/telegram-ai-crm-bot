"""Cross-application communication bus (Sprint 12.0)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.ecosystem.shared.exceptions import ValidationError
from applications.ecosystem.shared.store import UnifiedEcosystemStore, unified_ecosystem_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


EXCHANGE_TYPES = (
    "tasks",
    "documents",
    "events",
    "notifications",
    "analytics",
    "reports",
    "files",
    "knowledge",
    "workflows",
    "ai_decisions",
)


class CrossAppCommunication:
    def __init__(self, store: UnifiedEcosystemStore | None = None) -> None:
        self.store = store or unified_ecosystem_store

    def exchange(
        self,
        *,
        source_app: str,
        target_app: str,
        exchange_type: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if exchange_type not in EXCHANGE_TYPES:
            raise ValidationError(f"exchange_type must be one of {EXCHANGE_TYPES}")
        if not source_app or not target_app:
            raise ValidationError("source_app and target_app required")
        eid = f"xchg_{uuid.uuid4().hex[:12]}"
        item = {
            "exchange_id": eid,
            "source_app": source_app,
            "target_app": target_app,
            "exchange_type": exchange_type,
            "payload": dict(payload or {}),
            "status": "delivered",
            "at": _now(),
        }
        self.store.exchanges.save(eid, item)
        # Mirror into event center
        self.store.events.save(
            f"evt_{eid}",
            {"event_id": f"evt_{eid}", "topic": f"exchange.{exchange_type}", "source": source_app, "payload": item, "at": _now()},
        )
        return item

    def list_exchanges(self, *, exchange_type: str | None = None) -> list[dict[str, Any]]:
        items = self.store.exchanges.list_all()
        if exchange_type:
            items = [i for i in items if i.get("exchange_type") == exchange_type]
        return items

    def status(self) -> dict[str, Any]:
        return {
            "cross_app_communication": "1.0",
            "types": list(EXCHANGE_TYPES),
            "exchanges": len(self.list_exchanges()),
            "ready": True,
        }


cross_app_communication = CrossAppCommunication()
