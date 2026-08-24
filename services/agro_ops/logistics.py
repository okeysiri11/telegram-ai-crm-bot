"""AGRO 1.1 — operational logistics (carriers, fleet, trips)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from services.agro_ops.rbac import require

TWO = Decimal("0.01")
FOUR = Decimal("0.0001")

CARRIER_TYPES = [
    ("own", "Собственный транспорт"),
    ("contractor", "Подрядчик"),
    ("carrier", "Перевозчик"),
    ("forwarder", "Экспедитор"),
]

CARRIER_STATUSES = [
    ("active", "Активен"),
    ("inactive", "Неактивен"),
    ("risk", "Риск"),
    ("archived", "Архив"),
]

VEHICLE_STATUSES = [
    ("free", "Свободен"),
    ("assigned", "Назначен"),
    ("in_trip", "В рейсе"),
    ("repair", "Ремонт"),
    ("inactive", "Неактивен"),
]

TRIP_STATUSES = [
    ("planned", "Запланирован"),
    ("assigned", "Назначен"),
    ("loading", "Погрузка"),
    ("in_transit", "В пути"),
    ("unloading", "Разгрузка"),
    ("delivered", "Доставлен"),
    ("cancelled", "Отменён"),
]


def _dec(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _money(value: Decimal) -> float:
    return float(value.quantize(TWO, rounding=ROUND_HALF_UP))


def compute_trip_economics(item: dict[str, Any]) -> dict[str, Any]:
    qty = _dec(item.get("weight_actual") or item.get("weight_planned") or item.get("quantity"))
    distance = _dec(item.get("distance"))
    rate = _dec(item.get("rate"))
    fuel = _dec(item.get("fuel_cost"))
    toll = _dec(item.get("road_toll_cost") or item.get("toll_cost"))
    driver = _dec(item.get("driver_cost"))
    other = _dec(item.get("other_costs"))
    transport = rate if rate else Decimal("0")
    total = transport + fuel + toll + driver + other
    per_t = (total / qty) if qty else Decimal("0")
    per_km = (total / distance) if distance else Decimal("0")
    rate_per_t = (rate / qty) if qty and rate else Decimal("0")
    rate_per_km = (rate / distance) if distance and rate else Decimal("0")
    item["total_logistics_cost"] = _money(total)
    item["cost_per_tonne"] = _money(per_t)
    item["cost_per_km"] = float(per_km.quantize(FOUR, rounding=ROUND_HALF_UP))
    item["rate_per_tonne"] = _money(rate_per_t)
    item["rate_per_km"] = float(rate_per_km.quantize(FOUR, rounding=ROUND_HALF_UP))
    item["currency"] = item.get("currency") or "UAH"
    return item


class AgroOpsLogisticsMixin:
    """Mixed into AgroOpsService."""

    async def logistics_dashboard(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.engines import freight_quotes_as_trips
        from services.agro_ops.service import _org, active_only, _num

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        trips = active_only(bag.get("trip") or [])
        vehicles = active_only(bag.get("vehicle") or [])
        quotes = freight_quotes_as_trips(active_only(bag.get("market_price") or []))
        today = datetime.now(timezone.utc).date().isoformat()
        month = today[:7]
        active_statuses = {"planned", "assigned", "loading", "in_transit", "unloading"}
        active_trips = [t for t in trips if str(t.get("status")) in active_statuses]
        in_trip_ids = {str(t.get("vehicle_id") or "") for t in active_trips if t.get("vehicle_id")}
        free = [v for v in vehicles if str(v.get("status")) == "free" or (not v.get("status") and str(v.get("id")) not in in_trip_ids)]
        load_today = [t for t in trips if str(t.get("departure_planned") or t.get("departure_actual") or "")[:10] == today]
        unload_today = [t for t in trips if str(t.get("arrival_planned") or t.get("arrival_actual") or "")[:10] == today]
        overdue = [
            t for t in trips
            if str(t.get("status")) in active_statuses
            and t.get("arrival_planned")
            and str(t.get("arrival_planned"))[:10] < today
        ]
        cost_today = sum(_num(t.get("total_logistics_cost")) for t in trips if str(t.get("departure_actual") or t.get("created_at") or "")[:10] == today)
        cost_month = sum(_num(t.get("total_logistics_cost")) for t in trips if str(t.get("departure_actual") or t.get("created_at") or "")[:7] == month)
        problems = overdue + [t for t in trips if str(t.get("status")) == "risk"]
        return {
            "ok": True,
            "cards": {
                "active_trips": len(active_trips),
                "vehicles_in_trip": len([v for v in vehicles if str(v.get("id")) in in_trip_ids or str(v.get("status")) == "in_trip"]),
                "free_vehicles": len(free),
                "loadings_today": len(load_today),
                "unloadings_today": len(unload_today),
                "overdue_deliveries": len(overdue),
                "logistics_cost_today": cost_today,
                "logistics_cost_month": cost_month,
                "freight_quotes": len(quotes),
            },
            "commercial_quotes": quotes[:10],
            "upcoming": sorted(active_trips, key=lambda t: str(t.get("departure_planned") or "9999"))[:10],
            "active_fleet": [v for v in vehicles if str(v.get("status")) in {"assigned", "in_trip", "free"}][:10],
            "recent_delivered": [t for t in trips if str(t.get("status")) == "delivered"][:10],
            "problems": problems[:10],
        }

    def normalize_logistics_item(self, kind: str, item: dict[str, Any]) -> dict[str, Any]:
        if kind == "carrier":
            item.setdefault("carrier_type", item.get("type") or "carrier")
            item.setdefault("status", "active")
        if kind == "vehicle":
            item.setdefault("status", "free")
            item["plate"] = str(item.get("plate") or item.get("name") or "").upper()
            if not item.get("name"):
                item["name"] = item["plate"]
        if kind == "trailer":
            item.setdefault("status", "free")
            item["plate"] = str(item.get("plate") or item.get("name") or "").upper()
            if not item.get("name"):
                item["name"] = item["plate"]
        if kind == "driver":
            item.setdefault("status", "active")
            if not item.get("name"):
                item["name"] = item.get("full_name")
        if kind == "trip":
            item.setdefault("status", "planned")
            if not item.get("title"):
                item["title"] = item.get("trip_number") or "Рейс"
            status = str(item.get("manual_status") or "").upper()
            item["manual_status"] = status if status in {"CONFIRMED", "UNCONFIRMED"} else "CONFIRMED"
            compute_trip_economics(item)
        return item
