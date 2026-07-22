"""Production planning, orders, work centers, calendar (Sprint 11.6)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProductionManager:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create_work_center(self, *, name: str, center_type: str = "assembly", capacity: int = 1) -> dict[str, Any]:
        wid = f"wc_{uuid.uuid4().hex[:12]}"
        item = {
            "work_center_id": wid,
            "name": name,
            "center_type": center_type,
            "capacity": capacity,
            "status": "available",
            "created_at": _now(),
        }
        self.store.work_centers.save(wid, item)
        return item

    def list_work_centers(self) -> list[dict[str, Any]]:
        return self.store.work_centers.list_all()

    def create_order(
        self,
        *,
        product_name: str,
        quantity: int = 1,
        project_id: str = "",
        due_date: str = "",
        bom_id: str = "",
        revision: str = "A",
    ) -> dict[str, Any]:
        if quantity < 1:
            raise ValidationError("quantity must be >= 1")
        oid = f"po_{uuid.uuid4().hex[:12]}"
        order = {
            "order_id": oid,
            "product_name": product_name,
            "quantity": quantity,
            "project_id": project_id,
            "bom_id": bom_id,
            "revision": revision,
            "due_date": due_date,
            "status": "planned",
            "progress": 0,
            "history": [{"event": "created", "at": _now()}],
            "created_at": _now(),
        }
        self.store.production_orders.save(oid, order)
        return order

    def get_order(self, order_id: str) -> dict[str, Any]:
        item = self.store.production_orders.get(order_id)
        if item is None:
            raise NotFoundError("production_order", order_id)
        return item

    def list_orders(self) -> list[dict[str, Any]]:
        return self.store.production_orders.list_all()

    def update_order_status(self, order_id: str, status: str, *, progress: int | None = None) -> dict[str, Any]:
        order = self.get_order(order_id)
        order["status"] = status
        if progress is not None:
            order["progress"] = max(0, min(100, progress))
        order["history"].append({"event": "status", "status": status, "at": _now()})
        self.store.production_orders.save(order_id, order)
        return order

    def plan(self, *, order_id: str, work_center_id: str, start: str = "", end: str = "") -> dict[str, Any]:
        order = self.get_order(order_id)
        if self.store.work_centers.get(work_center_id) is None:
            raise NotFoundError("work_center", work_center_id)
        plan = {
            "order_id": order_id,
            "work_center_id": work_center_id,
            "start": start or _now(),
            "end": end,
            "planned_qty": order["quantity"],
            "status": "scheduled",
        }
        order["plan"] = plan
        order["status"] = "scheduled"
        order["history"].append({"event": "planned", "at": _now()})
        self.store.production_orders.save(order_id, order)
        return plan

    def revision_control(self, order_id: str, *, revision: str, notes: str = "") -> dict[str, Any]:
        order = self.get_order(order_id)
        order["revision"] = revision
        order.setdefault("revisions", []).append({"revision": revision, "notes": notes, "at": _now()})
        self.store.production_orders.save(order_id, order)
        return order

    def calendar_event(self, *, title: str, date: str, order_id: str = "", work_center_id: str = "") -> dict[str, Any]:
        cid = f"cal_{uuid.uuid4().hex[:12]}"
        event = {
            "event_id": cid,
            "title": title,
            "date": date,
            "order_id": order_id,
            "work_center_id": work_center_id,
            "created_at": _now(),
        }
        self.store.production_calendar.save(cid, event)
        return event

    def list_calendar(self) -> list[dict[str, Any]]:
        return self.store.production_calendar.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "production_manager": "1.0",
            "orders": self.store.production_orders.count(),
            "work_centers": self.store.work_centers.count(),
            "calendar_events": self.store.production_calendar.count(),
            "capabilities": [
                "production_manager",
                "production_planner",
                "manufacturing_orders",
                "work_centers",
                "revision_control",
                "production_calendar",
            ],
        }


production_manager = ProductionManager()
