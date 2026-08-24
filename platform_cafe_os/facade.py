"""Cafe OS library — Sprint 31.0 thin domain for F&B pilot.

Delegates commerce (payments/loyalty/POS) to Enterprise Commerce Core.
Does not fork Beauty or Automotive stacks.
"""

from __future__ import annotations

from typing import Any

INDUSTRY = "cafe"
ORDER_STATUSES = ("placed", "queued", "preparing", "ready", "served", "cancelled")
RESERVATION_STATUSES = ("held", "seated", "completed", "cancelled", "no_show")


class CafeOSLibrary:
    def bootstrap(self) -> dict[str, Any]:
        restaurant = {
            "name": "Pilot Cafe",
            "timezone": "Europe/Moscow",
            "currency": "USD",
            "industry": INDUSTRY,
        }
        tables = [
            {"name": "T1", "seats": 2, "zone": "window"},
            {"name": "T2", "seats": 4, "zone": "main"},
            {"name": "T3", "seats": 6, "zone": "patio"},
        ]
        menu = [
            {"name": "Espresso", "category": "drinks", "price": 3.5, "prep_min": 3},
            {"name": "Cappuccino", "category": "drinks", "price": 4.5, "prep_min": 5},
            {"name": "Club Sandwich", "category": "food", "price": 9.0, "prep_min": 12},
        ]
        staff = {"name": "Alex Waiter", "role": "waiter", "station": "floor"}
        customer = {"name": "Pilot Guest", "preferences": ["window"]}
        return {
            "bootstrap": True,
            "principles": [
                "reuse_enterprise_commerce",
                "reuse_platform_ai_team",
                "no_fork_beauty_or_auto",
            ],
            "full": {
                "restaurant": restaurant,
                "tables": tables,
                "menu": menu,
                "staff": staff,
                "customer": customer,
                "dashboard": {
                    "kpis": {"covers": 0, "orders": 0, "revenue": 0},
                    "kitchen_open": True,
                },
            },
        }

    def create_table(self, *, name: str, seats: int = 2, zone: str = "main") -> dict[str, Any]:
        if not name:
            raise ValueError("table name is required")
        return {"name": name, "seats": int(seats), "zone": zone, "available": True}

    def create_menu_item(
        self, *, name: str, category: str = "food", price: float = 0, prep_min: int = 5
    ) -> dict[str, Any]:
        if not name:
            raise ValueError("menu item name is required")
        return {
            "name": name,
            "category": category,
            "price": float(price),
            "prep_min": int(prep_min),
            "qr_eligible": True,
        }

    def create_staff(self, *, name: str, role: str = "waiter", station: str = "floor") -> dict[str, Any]:
        if not name or not role:
            raise ValueError("staff name and role are required")
        return {"name": name, "role": role, "station": station, "active": True}

    def create_customer(self, *, name: str, preferences: list[str] | None = None) -> dict[str, Any]:
        if not name:
            raise ValueError("customer name is required")
        return {"name": name, "preferences": list(preferences or []), "loyalty_tier": "new"}

    def reserve_table(
        self,
        *,
        table_id: str,
        customer_id: str,
        party_size: int,
        start: str,
        covers: int | None = None,
    ) -> dict[str, Any]:
        if not all([table_id, customer_id, start]):
            raise ValueError("reservation fields incomplete")
        return {
            "table_id": table_id,
            "customer_id": customer_id,
            "party_size": int(party_size or covers or 2),
            "start": start,
            "status": "held",
            "calendar_ref": "enterprise_calendar",
        }

    def place_order(
        self,
        *,
        customer_id: str,
        table_id: str,
        items: list[dict[str, Any]],
        reservation_id: str = "",
        channel: str = "dine_in",
        order_type: str = "Обычный заказ",
        guests: int = 0,
        comment: str = "",
        responsible: str = "",
    ) -> dict[str, Any]:
        if not customer_id or not items:
            raise ValueError("order requires customer and items")
        total = sum(float(i.get("price", 0) or 0) * float(i.get("qty", 1) or 1) for i in items)
        return {
            "customer_id": customer_id,
            "table_id": table_id,
            "reservation_id": reservation_id,
            "items": items,
            "channel": channel,
            "order_type": order_type or "Обычный заказ",
            "guests": int(guests or 0),
            "comment": comment or "",
            "responsible": responsible or "",
            "status": "Новый",
            "total": total,
            "kitchen_ref": "kitchen_queue",
        }

    def enqueue_kitchen(self, *, order_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        if not order_id:
            raise ValueError("order_id required")
        return {
            "order_id": order_id,
            "items": items,
            "status": "queued",
            "station": "hot",
        }

    def transition_kitchen(self, ticket: dict[str, Any], *, status: str) -> dict[str, Any]:
        if status not in ORDER_STATUSES:
            raise ValueError(f"unknown kitchen status: {status}")
        return {**ticket, "status": status}

    def transition_reservation(self, reservation: dict[str, Any], *, status: str) -> dict[str, Any]:
        if status not in RESERVATION_STATUSES:
            raise ValueError(f"unknown reservation status: {status}")
        return {**reservation, "status": status}

    def qr_menu(self, *, menu_items: list[dict[str, Any]], restaurant_id: str) -> dict[str, Any]:
        return {
            "restaurant_id": restaurant_id,
            "url_path": f"/qr/menu/{restaurant_id}",
            "item_count": len(menu_items),
            "channel": "qr",
        }

    def create_delivery(
        self, *, order_id: str, customer_id: str, address: str = "Pilot Ave 1"
    ) -> dict[str, Any]:
        if not order_id or not customer_id:
            raise ValueError("delivery requires order and customer")
        return {
            "order_id": order_id,
            "customer_id": customer_id,
            "address": address,
            "status": "dispatched",
            "provider": "in_house",
        }

    def dashboard(
        self,
        *,
        reservations: list[dict[str, Any]],
        orders: list[dict[str, Any]],
        kitchen: list[dict[str, Any]],
    ) -> dict[str, Any]:
        revenue = sum(float(o.get("total", 0) or 0) for o in orders)
        return {
            "kpis": {
                "reservations": len(reservations),
                "orders": len(orders),
                "kitchen_open": len([k for k in kitchen if k.get("status") in ("queued", "preparing")]),
                "revenue": revenue,
            },
            "industry": INDUSTRY,
        }

    def status(self) -> dict[str, Any]:
        return {"industry": INDUSTRY, "library": "platform_cafe_os", "ready": True}
