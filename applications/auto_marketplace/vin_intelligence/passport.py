"""Vehicle Digital Passport — Sprint 13.1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

TIMELINE_TYPES = [
    "ownership",
    "mileage",
    "accident",
    "insurance",
    "maintenance",
    "modification",
    "recall",
    "warranty",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DigitalPassport:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def create(self, *, vin: str, decode_id: str = "", title: str = "") -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        if len(vin) < 11:
            raise ValidationError("VIN required for passport")
        existing = next((p for p in self.store.vi_passports.list_all() if p.get("vin") == vin), None)
        if existing:
            return existing
        pid = _id("vipass")
        passport = {
            "passport_id": pid,
            "vin": vin,
            "decode_id": decode_id,
            "title": title or f"Passport {vin[-6:]}",
            "timelines": {t: [] for t in TIMELINE_TYPES},
            "status": "active",
            "created_at": _now(),
            "updated_at": _now(),
        }
        return self.store.vi_passports.save(pid, passport)

    def get(self, passport_id: str) -> dict[str, Any]:
        item = self.store.vi_passports.get(passport_id)
        if item is None:
            raise NotFoundError("passport", passport_id)
        return item

    def get_by_vin(self, vin: str) -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        for p in self.store.vi_passports.list_all():
            if p.get("vin") == vin:
                return p
        raise NotFoundError("passport", vin)

    def add_timeline_event(
        self,
        *,
        passport_id: str,
        timeline: str,
        event: dict[str, Any],
        at: str | None = None,
    ) -> dict[str, Any]:
        if timeline not in TIMELINE_TYPES:
            raise ValidationError(f"timeline must be one of {TIMELINE_TYPES}")
        passport = self.get(passport_id)
        entry = {
            "event_id": _id("vievt"),
            "timeline": timeline,
            "at": at or _now(),
            **event,
        }
        passport["timelines"].setdefault(timeline, []).append(entry)
        passport["updated_at"] = _now()
        self.store.vi_passports.save(passport_id, passport)
        return entry

    def status(self) -> dict[str, Any]:
        return {
            "passports": self.store.vi_passports.count(),
            "timeline_types": TIMELINE_TYPES,
        }
