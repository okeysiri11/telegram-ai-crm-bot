"""Vehicle history records — Sprint 13.1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

HISTORY_TYPES = [
    "import",
    "registration",
    "inspection",
    "auction",
    "police",
    "service",
    "recall",
    "open_campaign",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class VehicleHistory:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def add(
        self,
        *,
        vin: str,
        history_type: str,
        detail: dict[str, Any] | None = None,
        source: str = "manual",
    ) -> dict[str, Any]:
        if history_type not in HISTORY_TYPES:
            raise ValidationError(f"history_type must be one of {HISTORY_TYPES}")
        vin = (vin or "").strip().upper()
        if not vin:
            raise ValidationError("vin required")
        hid = _id("vihist")
        record = {
            "history_id": hid,
            "vin": vin,
            "history_type": history_type,
            "detail": detail or {},
            "source": source,
            "recorded_at": _now(),
        }
        return self.store.vi_history.save(hid, record)

    def list_for_vin(self, vin: str, history_type: str | None = None) -> list[dict[str, Any]]:
        vin = (vin or "").strip().upper()
        items = [h for h in self.store.vi_history.list_all() if h.get("vin") == vin]
        if history_type:
            return [h for h in items if h.get("history_type") == history_type]
        return items

    def status(self) -> dict[str, Any]:
        return {"records": self.store.vi_history.count(), "history_types": HISTORY_TYPES}
