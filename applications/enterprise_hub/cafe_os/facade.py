"""Cafe OS Suite facade — Sprint 31.0.

Thin Hub overlay for Cafe pilot. Payments/loyalty/POS delegate to Commerce Core.
Does not fork Beauty OS or Automotive CRM.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_cafe_os import CafeOSLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CafeOSSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = CafeOSLibrary()

    def bootstrap(self) -> dict[str, Any]:
        self.library = CafeOSLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("cos_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.cos_bootstraps.save(bid, record)
        rid = _id("cos_rest")
        self.store.cos_restaurants.save(rid, {"restaurant_id": rid, **full["restaurant"], "created_at": _now()})
        table_ids: list[str] = []
        for t in full["tables"]:
            tid = _id("cos_tbl")
            self.store.cos_tables.save(tid, {"table_id": tid, **t, "created_at": _now()})
            table_ids.append(tid)
        menu_ids: list[str] = []
        for m in full["menu"]:
            mid = _id("cos_menu")
            self.store.cos_menu.save(mid, {"item_id": mid, **m, "created_at": _now()})
            menu_ids.append(mid)
        sid = _id("cos_stf")
        self.store.cos_staff.save(sid, {"staff_id": sid, **full["staff"], "created_at": _now()})
        cuid = _id("cos_cu")
        self.store.cos_customers.save(cuid, {"customer_id": cuid, **full["customer"], "created_at": _now()})
        did = _id("cos_dash")
        self.store.cos_dashboards.save(did, {"dashboard_id": did, **full["dashboard"], "rendered_at": _now()})
        record.update(
            {
                "restaurant_id": rid,
                "table_ids": table_ids,
                "menu_ids": menu_ids,
                "staff_id": sid,
                "customer_id": cuid,
                "dashboard_id": did,
            }
        )
        self.store.cos_bootstraps.save(bid, record)
        return record

    def create_table(self, **kwargs: Any) -> dict[str, Any]:
        try:
            table = self.library.create_table(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        tid = _id("cos_tbl")
        record = {"table_id": tid, **table, "created_at": _now()}
        self.store.cos_tables.save(tid, record)
        return record

    def list_tables(self) -> dict[str, Any]:
        items = self.store.cos_tables.list_all()
        return {"tables": items, "count": len(items), "items": items}

    def create_menu_item(self, **kwargs: Any) -> dict[str, Any]:
        try:
            item = self.library.create_menu_item(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        mid = _id("cos_menu")
        record = {"item_id": mid, **item, "created_at": _now()}
        self.store.cos_menu.save(mid, record)
        return record

    def list_menu(self) -> dict[str, Any]:
        items = self.store.cos_menu.list_all()
        return {"menu": items, "count": len(items), "items": items}

    def list_staff(self) -> dict[str, Any]:
        items = self.store.cos_staff.list_all()
        return {"staff": items, "count": len(items), "items": items}

    def list_customers(self) -> dict[str, Any]:
        items = self.store.cos_customers.list_all()
        return {"customers": items, "count": len(items), "items": items}

    def list_reservations(self) -> dict[str, Any]:
        items = self.store.cos_reservations.list_all()
        return {"reservations": items, "count": len(items), "items": items}

    def list_orders(self) -> dict[str, Any]:
        items = self.store.cos_orders.list_all()
        return {"orders": items, "count": len(items), "items": items}

    def list_shifts(self) -> dict[str, Any]:
        items = self.store.cos_shifts.list_all()
        return {"shifts": items, "count": len(items), "items": items}

    def open_shift(self, *, staff_id: str, role: str = "", date: str = "") -> dict[str, Any]:
        staff = self.store.cos_staff.get(staff_id) if staff_id else None
        if staff_id and not staff:
            raise NotFoundError(f"staff not found: {staff_id}")
        sid = _id("cos_shf")
        record = {
            "shift_id": sid,
            "staff_id": staff_id,
            "employee": (staff or {}).get("name", staff_id or "—"),
            "role": role or (staff or {}).get("role", "waiter"),
            "date": date or _now()[:10],
            "start": _now(),
            "end": "",
            "status": "Открыта",
            "created_at": _now(),
        }
        self.store.cos_shifts.save(sid, record)
        return record

    def close_shift(self, *, shift_id: str) -> dict[str, Any]:
        item = self.store.cos_shifts.get(shift_id)
        if not item:
            raise NotFoundError(f"shift not found: {shift_id}")
        updated = {**item, "end": _now(), "status": "Закрыта", "updated_at": _now()}
        self.store.cos_shifts.save(shift_id, updated)
        return updated

    def create_staff(self, **kwargs: Any) -> dict[str, Any]:
        try:
            staff = self.library.create_staff(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        sid = _id("cos_stf")
        record = {"staff_id": sid, **staff, "created_at": _now()}
        self.store.cos_staff.save(sid, record)
        return record

    def create_customer(self, **kwargs: Any) -> dict[str, Any]:
        try:
            customer = self.library.create_customer(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        cuid = _id("cos_cu")
        record = {"customer_id": cuid, **customer, "created_at": _now()}
        self.store.cos_customers.save(cuid, record)
        return record

    def reserve_table(self, **kwargs: Any) -> dict[str, Any]:
        try:
            reservation = self.library.reserve_table(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        reid = _id("cos_rsv")
        record = {"reservation_id": reid, **reservation, "created_at": _now()}
        self.store.cos_reservations.save(reid, record)
        return record

    def transition_reservation(self, *, reservation_id: str, status: str) -> dict[str, Any]:
        item = self.store.cos_reservations.get(reservation_id)
        if not item:
            raise NotFoundError(f"reservation not found: {reservation_id}")
        try:
            updated = self.library.transition_reservation(item, status=status)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.cos_reservations.save(reservation_id, {**updated, "updated_at": _now()})
        return updated

    def place_order(self, **kwargs: Any) -> dict[str, Any]:
        try:
            order = self.library.place_order(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        oid = _id("cos_ord")
        record = {"order_id": oid, **order, "created_at": _now()}
        self.store.cos_orders.save(oid, record)
        ticket = self.library.enqueue_kitchen(order_id=oid, items=list(order.get("items") or []))
        kid = _id("cos_kit")
        self.store.cos_kitchen.save(kid, {"ticket_id": kid, **ticket, "created_at": _now()})
        record["kitchen_ticket_id"] = kid
        self.store.cos_orders.save(oid, record)
        return record

    def kitchen_queue(self) -> dict[str, Any]:
        items = self.store.cos_kitchen.list_all()
        return {"queue": items, "count": len(items)}

    def transition_kitchen(self, *, ticket_id: str, status: str) -> dict[str, Any]:
        item = self.store.cos_kitchen.get(ticket_id)
        if not item:
            raise NotFoundError(f"kitchen ticket not found: {ticket_id}")
        try:
            updated = self.library.transition_kitchen(item, status=status)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.cos_kitchen.save(ticket_id, {**updated, "updated_at": _now()})
        return updated

    def qr_menu(self, *, restaurant_id: str = "") -> dict[str, Any]:
        menu = self.store.cos_menu.list_all()
        rid = restaurant_id or (self.store.cos_restaurants.list_all() or [{}])[-1].get("restaurant_id", "cafe")
        payload = self.library.qr_menu(menu_items=menu, restaurant_id=str(rid))
        qid = _id("cos_qr")
        record = {"qr_id": qid, **payload, "created_at": _now()}
        self.store.cos_qr.save(qid, record)
        return record

    def create_delivery(self, **kwargs: Any) -> dict[str, Any]:
        try:
            delivery = self.library.create_delivery(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        did = _id("cos_del")
        record = {"delivery_id": did, **delivery, "created_at": _now()}
        self.store.cos_deliveries.save(did, record)
        return record

    def crm_update(self, *, customer_id: str, event: str = "visit", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        cust = self.store.cos_customers.get(customer_id)
        if not cust:
            raise NotFoundError(f"customer not found: {customer_id}")
        cid = _id("cos_crm")
        record = {
            "crm_event_id": cid,
            "customer_id": customer_id,
            "event": event,
            "payload": payload or {},
            "crm_ref": "enterprise_crm",
            "created_at": _now(),
        }
        self.store.cos_crm.save(cid, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        dash = self.library.dashboard(
            reservations=self.store.cos_reservations.list_all(),
            orders=self.store.cos_orders.list_all(),
            kitchen=self.store.cos_kitchen.list_all(),
        )
        did = _id("cos_dash")
        record = {"dashboard_id": did, **dash, "rendered_at": _now()}
        self.store.cos_dashboards.save(did, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.cos_bootstraps.list_all()),
            "restaurants": len(self.store.cos_restaurants.list_all()),
            "tables": len(self.store.cos_tables.list_all()),
            "menu": len(self.store.cos_menu.list_all()),
            "orders": len(self.store.cos_orders.list_all()),
            "kitchen": len(self.store.cos_kitchen.list_all()),
            "reservations": len(self.store.cos_reservations.list_all()),
        }


cafe_os = CafeOSSuite()
