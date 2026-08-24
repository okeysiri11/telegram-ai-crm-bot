"""AGRO 1.1 — warehouses, lots, receipt/issue/transfer."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from services.agro_ops.rbac import require

TWO = Decimal("0.01")

WAREHOUSE_TYPES = [
    ("warehouse", "Склад"),
    ("elevator", "Элеватор"),
    ("silo", "Силос"),
    ("terminal", "Терминал"),
    ("temporary", "Временное хранение"),
    ("other", "Другое"),
]

OPERATION_TYPES = [
    ("RECEIPT", "Приход"),
    ("ISSUE", "Расход"),
    ("TRANSFER", "Перемещение"),
    ("ADJUSTMENT", "Корректировка"),
    ("INVENTORY_CORRECTION", "Инвентаризация"),
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


def _qty(value: Any) -> float:
    return float(_dec(value))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgroOpsWarehouseMixin:
    """Mixed into AgroOpsService."""

    def normalize_warehouse_item(self, kind: str, item: dict[str, Any]) -> dict[str, Any]:
        if kind == "warehouse":
            item.setdefault("warehouse_type", item.get("type") or "warehouse")
            item.setdefault("capacity_unit", "т")
            item.setdefault("status", "active")
            if item.get("capacity_total") not in (None, ""):
                item["capacity_total"] = _qty(item.get("capacity_total"))
        if kind == "storage_unit":
            item.setdefault("status", "active")
            if not item.get("name"):
                item["name"] = item.get("title") or "Секция"
        if kind == "inventory_lot":
            item.setdefault("unit", "т")
            item["quantity"] = _qty(item.get("quantity"))
            item.setdefault("status", "active")
            if not item.get("name"):
                item["name"] = item.get("lot_number") or item.get("commodity") or "Партия"
        return item

    def _lot_qty(self, lot: dict[str, Any]) -> Decimal:
        return _dec(lot.get("quantity"))

    async def warehouse_dashboard(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        warehouses = active_only(bag.get("warehouse") or [])
        lots = active_only(bag.get("inventory_lot") or [])
        prices = active_only(bag.get("market_price") or [])
        by_crop: dict[str, dict[str, Any]] = {}
        occupied = Decimal("0")
        value = Decimal("0")
        for lot in lots:
            crop = str(lot.get("commodity") or lot.get("crop") or "Прочее")
            qty = self._lot_qty(lot)
            occupied += qty
            cost = _dec(lot.get("purchase_price")) * qty
            value += cost
            bucket = by_crop.setdefault(crop, {"commodity": crop, "quantity": 0.0, "purchase_value": 0.0, "market_value": None, "unrealized": None})
            bucket["quantity"] = _money(_dec(bucket["quantity"]) + qty)
            bucket["purchase_value"] = _money(_dec(bucket["purchase_value"]) + cost)
        capacity = sum(_dec(w.get("capacity_total")) for w in warehouses)
        free = capacity - occupied if capacity else Decimal("0")
        fill = float((occupied / capacity * 100).quantize(TWO)) if capacity else None
        latest_price = {}
        for p in sorted(prices, key=lambda x: str(x.get("valid_from") or x.get("created_at") or ""), reverse=True):
            key = str(p.get("commodity") or p.get("crop") or "")
            if key and key not in latest_price:
                latest_price[key] = p
        for crop, bucket in by_crop.items():
            ref = latest_price.get(crop)
            if ref:
                mkt = _dec(ref.get("price")) * _dec(bucket["quantity"])
                bucket["market_value"] = _money(mkt)
                bucket["reference_source"] = ref.get("source_type")
                bucket["unrealized"] = _money(mkt - _dec(bucket["purchase_value"]))
        return {
            "ok": True,
            "cards": {
                "capacity_total": _money(capacity),
                "occupied": _money(occupied),
                "free": _money(free) if capacity else 0,
                "fill_pct": fill,
                "inventory_value": _money(value),
                "warehouses": len(warehouses),
                "lots": len(lots),
            },
            "by_crop": list(by_crop.values()),
            "warehouses": warehouses,
        }

    async def warehouse_operation(
        self, organization_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        op_type = str(body.get("type") or body.get("operation_type") or "RECEIPT").upper()
        if op_type not in {t for t, _ in OPERATION_TYPES}:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип складской операции"}
        qty = _dec(body.get("quantity"))
        if qty <= 0:
            return {"ok": False, "error": "validation", "message_ru": "Укажите количество больше нуля"}
        warehouse_id = str(body.get("warehouse_id") or "")
        if not warehouse_id:
            return {"ok": False, "error": "validation", "message_ru": "Укажите склад"}
        bag = self._bag(org)  # type: ignore[attr-defined]
        warehouse = next((w for w in active_only(bag.get("warehouse") or []) if str(w.get("id")) == warehouse_id), None)
        if not warehouse:
            return {"ok": False, "error": "not_found", "message_ru": "Склад не найден"}

        if op_type == "TRANSFER":
            return await self._transfer_stock(org, body, qty, role)

        lot = None
        lot_id = str(body.get("lot_id") or "")
        if lot_id:
            lot = next((x for x in bag.get("inventory_lot") or [] if str(x.get("id")) == lot_id and not x.get("archived_at")), None)
            if not lot:
                return {"ok": False, "error": "not_found", "message_ru": "Партия не найдена"}

        if op_type == "RECEIPT":
            if lot:
                new_qty = self._lot_qty(lot) + qty
                await self.update_entity(org, "inventory_lot", str(lot["id"]), {"quantity": float(new_qty)}, role)  # type: ignore[attr-defined]
                lot_id = str(lot["id"])
            else:
                created = await self.create_entity(  # type: ignore[attr-defined]
                    org,
                    "inventory_lot",
                    {
                        "lot_number": body.get("lot_number") or f"LOT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                        "warehouse_id": warehouse_id,
                        "storage_unit_id": body.get("storage_unit_id"),
                        "commodity": body.get("commodity") or body.get("crop"),
                        "crop_year": body.get("crop_year"),
                        "owner": body.get("owner"),
                        "supplier": body.get("counterparty_id"),
                        "counterparty_id": body.get("counterparty_id"),
                        "deal_id": body.get("deal_id"),
                        "contract_id": body.get("contract_id"),
                        "quantity": float(qty),
                        "unit": body.get("unit") or "т",
                        "quality": body.get("quality") or {},
                        "arrival_date": body.get("date") or _now()[:10],
                        "purchase_price": body.get("purchase_price") or body.get("price"),
                        "notes": body.get("notes"),
                    },
                    role,
                )
                if not created.get("ok"):
                    return created
                lot_id = str(created["item"]["id"])
        else:
            if not lot:
                return {"ok": False, "error": "validation", "message_ru": "Для расхода укажите партию"}
            new_qty = self._lot_qty(lot) - qty
            if new_qty < 0:
                if not body.get("allow_negative"):
                    return {"ok": False, "error": "validation", "message_ru": "Недостаточно остатка на складе"}
                denied_admin = require(role, "admin")
                if denied_admin:
                    return {"ok": False, "error": "forbidden", "message_ru": "Отрицательный остаток может подтвердить только директор"}
            await self.update_entity(org, "inventory_lot", str(lot["id"]), {"quantity": float(new_qty)}, role)  # type: ignore[attr-defined]
            lot_id = str(lot["id"])

        op = await self.create_entity(  # type: ignore[attr-defined]
            org,
            "warehouse_operation",
            {
                "title": body.get("title") or f"{op_type} {qty}",
                "date": body.get("date") or _now()[:10],
                "warehouse_id": warehouse_id,
                "storage_unit_id": body.get("storage_unit_id"),
                "type": op_type,
                "lot_id": lot_id,
                "commodity": body.get("commodity") or body.get("crop") or (lot or {}).get("commodity"),
                "quantity": float(qty),
                "counterparty_id": body.get("counterparty_id"),
                "deal_id": body.get("deal_id"),
                "shipment_id": body.get("shipment_id"),
                "trip_id": body.get("trip_id"),
                "vehicle_id": body.get("vehicle_id"),
                "driver_id": body.get("driver_id"),
                "document": body.get("document"),
                "responsible": body.get("responsible") or role,
                "notes": body.get("notes"),
            },
            role,
        )
        return op

    async def _transfer_stock(self, org: str, body: dict[str, Any], qty: Decimal, role: str | None) -> dict[str, Any]:
        dest = str(body.get("to_warehouse_id") or body.get("destination_warehouse_id") or "")
        if not dest:
            return {"ok": False, "error": "validation", "message_ru": "Укажите склад назначения"}
        issue = await self.warehouse_operation(
            org,
            {
                **body,
                "type": "ISSUE",
                "quantity": float(qty),
                "title": body.get("title") or "Перемещение (расход)",
            },
            role,
        )
        if not issue.get("ok"):
            return issue
        src_lot_id = (issue.get("item") or {}).get("lot_id")
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        src_lot = next((x for x in active_only(bag.get("inventory_lot") or []) if str(x.get("id")) == str(src_lot_id)), None)
        receipt = await self.warehouse_operation(
            org,
            {
                "type": "RECEIPT",
                "warehouse_id": dest,
                "storage_unit_id": body.get("to_storage_unit_id"),
                "quantity": float(qty),
                "commodity": body.get("commodity") or (src_lot or {}).get("commodity"),
                "unit": body.get("unit") or (src_lot or {}).get("unit") or "т",
                "counterparty_id": body.get("counterparty_id"),
                "deal_id": body.get("deal_id"),
                "purchase_price": (src_lot or {}).get("purchase_price"),
                "quality": (src_lot or {}).get("quality"),
                "title": body.get("title") or "Перемещение (приход)",
                "notes": f"transfer_from={body.get('warehouse_id')};op={issue['item']['id']}",
            },
            role,
        )
        if not receipt.get("ok"):
            return receipt
        return {
            "ok": True,
            "item": {
                "type": "TRANSFER",
                "issue": issue["item"],
                "receipt": receipt["item"],
                "linked": True,
            },
        }

    async def receive_from_trip(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        """Explicit warehouse receipt from a delivered trip — never silent."""
        payload = {**body, "type": "RECEIPT"}
        return await self.warehouse_operation(organization_id, payload, role)

    async def issue_to_trip(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        payload = {**body, "type": "ISSUE"}
        return await self.warehouse_operation(organization_id, payload, role)
