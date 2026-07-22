"""Service center management — Sprint 13.6."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

ORDER_STATUSES = ["open", "scheduled", "in_progress", "qc", "completed", "warranty"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ServiceCenter:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def register_mechanic(self, *, name: str, specialty: str = "general") -> dict[str, Any]:
        if not name:
            raise ValidationError("mechanic name required")
        mid = _id("erp_mech")
        mech = {"mechanic_id": mid, "name": name, "specialty": specialty, "status": "available", "created_at": _now()}
        return self.store.erp_mechanics.save(mid, mech)

    def create_service_order(
        self,
        *,
        vin: str,
        customer: str = "",
        description: str = "",
        warranty: bool = False,
    ) -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        if len(vin) < 11:
            raise ValidationError("vin required")
        oid = _id("erp_so")
        order = {
            "service_order_id": oid,
            "vin": vin,
            "customer": customer,
            "description": description,
            "status": "open",
            "warranty": bool(warranty),
            "mechanic_id": "",
            "scheduled_at": "",
            "qc_passed": None,
            "created_at": _now(),
        }
        return self.store.erp_service_orders.save(oid, order)

    def create_repair_order(self, *, service_order_id: str, tasks: list[str] | None = None, parts: list[str] | None = None) -> dict[str, Any]:
        so = self.store.erp_service_orders.get(service_order_id)
        if so is None:
            raise NotFoundError("service_order", service_order_id)
        rid = _id("erp_ro")
        order = {
            "repair_order_id": rid,
            "service_order_id": service_order_id,
            "vin": so["vin"],
            "tasks": tasks or [],
            "parts": parts or [],
            "status": "open",
            "created_at": _now(),
        }
        return self.store.erp_repair_orders.save(rid, order)

    def schedule(self, service_order_id: str, *, mechanic_id: str, starts_at: str) -> dict[str, Any]:
        so = self.store.erp_service_orders.get(service_order_id)
        if so is None:
            raise NotFoundError("service_order", service_order_id)
        if self.store.erp_mechanics.get(mechanic_id) is None:
            raise NotFoundError("mechanic", mechanic_id)
        so["mechanic_id"] = mechanic_id
        so["scheduled_at"] = starts_at
        so["status"] = "scheduled"
        so["updated_at"] = _now()
        self.store.erp_service_orders.save(service_order_id, so)
        cid = _id("erp_cal")
        event = {
            "event_id": cid,
            "service_order_id": service_order_id,
            "mechanic_id": mechanic_id,
            "starts_at": starts_at,
            "kind": "workshop",
        }
        return self.store.erp_workshop_calendar.save(cid, event)

    def quality_control(self, service_order_id: str, *, passed: bool, notes: str = "") -> dict[str, Any]:
        so = self.store.erp_service_orders.get(service_order_id)
        if so is None:
            raise NotFoundError("service_order", service_order_id)
        so["qc_passed"] = bool(passed)
        so["status"] = "completed" if passed else "qc"
        so["qc_notes"] = notes
        so["updated_at"] = _now()
        self.store.erp_service_orders.save(service_order_id, so)
        hid = _id("erp_hist")
        history = {
            "history_id": hid,
            "vin": so["vin"],
            "service_order_id": service_order_id,
            "warranty": so.get("warranty"),
            "result": "passed" if passed else "failed",
            "at": _now(),
        }
        return self.store.erp_service_history.save(hid, history)

    def status(self) -> dict[str, Any]:
        return {
            "mechanics": self.store.erp_mechanics.count(),
            "service_orders": self.store.erp_service_orders.count(),
            "repair_orders": self.store.erp_repair_orders.count(),
            "history": self.store.erp_service_history.count(),
        }
