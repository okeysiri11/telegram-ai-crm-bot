"""AGRO 2.2 — grain operation lifecycle (purchase → warehouse → sale → actual P&L).

Extends agro_ops. Inventory is ledger-based. No invented costs. No fake GPS/scales.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from services.agro_ops.finance import _dec, _money
from services.agro_ops.rbac import can, normalize_role, require
from services.agro_ops.warehouses import _qty

OPS_VERSION = "AGRO_2_2"

OPERATION_STATUSES = [
    ("draft", "Черновик"),
    ("purchase_agreed", "Закупка согласована"),
    ("awaiting_load", "Ожидает загрузку"),
    ("loading", "Загрузка"),
    ("in_transit", "В пути"),
    ("receiving", "Приёмка"),
    ("quality", "Контроль качества"),
    ("warehoused", "Принято на склад"),
    ("partly_sold", "Частично продано"),
    ("sold", "Продано"),
    ("closed", "Закрыто"),
    ("problem", "Проблема"),
    ("blocked", "Заблокировано"),
    ("cancelled", "Отменено"),
]

OP_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"purchase_agreed", "cancelled", "problem"},
    "purchase_agreed": {"awaiting_load", "loading", "cancelled", "problem"},
    "awaiting_load": {"loading", "problem", "cancelled"},
    "loading": {"in_transit", "awaiting_load", "problem"},
    "in_transit": {"receiving", "problem"},
    "receiving": {"quality", "warehoused", "problem"},
    "quality": {"warehoused", "problem", "receiving"},
    "warehoused": {"partly_sold", "sold", "closed", "problem"},
    "partly_sold": {"sold", "warehoused", "closed", "problem"},
    "sold": {"closed", "partly_sold"},
    "closed": set(),
    "problem": {"draft", "purchase_agreed", "awaiting_load", "loading", "in_transit", "receiving", "quality", "warehoused", "cancelled"},
    "blocked": {"problem", "cancelled"},
    "cancelled": set(),
}

TRUCK_STATUSES = [
    ("assigned", "Назначена"),
    ("loading", "На загрузке"),
    ("loaded", "Загружена"),
    ("in_transit", "В пути"),
    ("unloading", "На выгрузке"),
    ("unloaded", "Выгружена"),
    ("closed", "Закрыта"),
    ("problem", "Проблема"),
]

TRUCK_TRANSITIONS: dict[str, set[str]] = {
    "assigned": {"loading", "problem"},
    "loading": {"loaded", "assigned", "problem"},
    "loaded": {"in_transit", "problem"},
    "in_transit": {"unloading", "problem"},
    "unloading": {"unloaded", "problem"},
    "unloaded": {"closed", "problem"},
    "closed": set(),
    "problem": {"assigned", "loading", "in_transit"},
}

MOVEMENT_TYPES = ("RECEIPT", "TRANSFER", "SALE", "WRITE_OFF", "ADJUSTMENT", "RETURN", "PROCESSING")

EXPENSE_CATEGORIES = [
    ("transport", "Транспорт"),
    ("loading", "Погрузка"),
    ("unloading", "Разгрузка"),
    ("storage", "Хранение"),
    ("drying", "Сушка"),
    ("cleaning", "Очистка"),
    ("lab", "Лаборатория"),
    ("broker", "Брокер"),
    ("commission", "Комиссия"),
    ("customs", "Таможня"),
    ("documents", "Документы"),
    ("insurance", "Страхование"),
    ("other", "Прочее"),
]

TRANSPORT_MODES = [
    ("own_truck", "Свой транспорт"),
    ("carrier", "Внешний перевозчик"),
    ("rail", "Железная дорога"),
    ("container", "Контейнер"),
    ("vessel", "Судно"),
    ("other", "Другое"),
]

LOSS_KINDS = [
    ("transport", "Transport discrepancy"),
    ("drying", "Drying loss"),
    ("cleaning", "Cleaning loss"),
    ("warehouse", "Warehouse adjustment"),
    ("write_off", "Write-off"),
]

QUALITY_METRICS = {
    "moisture": {"label_ru": "Влажность", "unit": "%"},
    "foreign_matter": {"label_ru": "Сорная примесь", "unit": "%"},
    "grain_admix": {"label_ru": "Зерновая примесь", "unit": "%"},
    "protein": {"label_ru": "Белок", "unit": "%"},
    "gluten": {"label_ru": "Клейковина", "unit": "%"},
    "test_weight": {"label_ru": "Натура", "unit": "г/л"},
    "oil_content": {"label_ru": "Масличность", "unit": "%"},
    "acid_value": {"label_ru": "Кислотное число", "unit": ""},
}

QUALITY_PROFILES: dict[str, dict[str, dict[str, float]]] = {
    "Пшеница": {"moisture": {"max": 14}, "foreign_matter": {"max": 2}, "protein": {"min": 11.5}},
    "Кукуруза": {"moisture": {"max": 15}, "foreign_matter": {"max": 2}},
    "Ячмень": {"moisture": {"max": 14.5}, "foreign_matter": {"max": 2}},
    "Подсолнечник": {"moisture": {"max": 8}, "oil_content": {"min": 40}},
    "Соя": {"moisture": {"max": 12}, "protein": {"min": 30}},
    "Рапс": {"moisture": {"max": 8}, "oil_content": {"min": 40}},
}

QUALITY_DECISIONS = [
    ("accept", "Принять"),
    ("discount", "Принять со скидкой"),
    ("clean", "На очистку/сушку"),
    ("reject", "Отклонить"),
    ("review", "Ручная проверка"),
]

EXCEPTION_STATUSES = ("OPEN", "IN_PROGRESS", "RESOLVED", "DISMISSED")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _s(value: Any) -> str:
    return str(value or "").strip()


def _num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round4(value: float) -> float:
    return round(value, 4)


class AgroOpsLifecycleMixin:
    """Mixed into AgroOpsService."""

    def _ops_find(self, org: str, kind: str, item_id: str) -> dict[str, Any] | None:
        bag = self._bag(org)  # type: ignore[attr-defined]
        return next((x for x in bag.get(kind) or [] if str(x.get("id")) == str(item_id)), None)

    def _idempotent(self, org: str, kind: str, key: str | None) -> dict[str, Any] | None:
        if not key:
            return None
        bag = self._bag(org)  # type: ignore[attr-defined]
        return next((x for x in bag.get(kind) or [] if str(x.get("idempotency_key") or "") == str(key)), None)

    def _next_op_number(self, org: str) -> str:
        from services.agro_ops.service import active_only

        year = _now().year
        bag = self._bag(org)  # type: ignore[attr-defined]
        n = 1 + len([o for o in active_only(bag.get("agro_operation") or []) if str(o.get("number") or "").startswith(f"AG-{year}-")])
        return f"AG-{year}-{n:06d}"

    def _lot_available(self, org: str, lot_id: str) -> float:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        total = Decimal("0")
        reserved = Decimal("0")
        for m in active_only(bag.get("stock_movement") or []):
            if str(m.get("lot_id")) != str(lot_id):
                continue
            qty = _dec(m.get("quantity"))
            mt = str(m.get("movement_type") or m.get("type") or "")
            if mt in {"RECEIPT", "RETURN", "ADJUSTMENT"} and qty >= 0:
                total += qty
            elif mt == "ADJUSTMENT":
                total += qty
            else:
                total -= abs(qty)
        for a in active_only(bag.get("deal") or []):
            if str(a.get("status")) in {"cancelled", "closed"}:
                continue
            for row in a.get("allocations") or []:
                if str(row.get("lot_id")) == str(lot_id) and str(a.get("shipped") or "").lower() not in {"1", "true", "yes"}:
                    reserved += _dec(row.get("quantity"))
        return _round4(float(total - reserved))

    def _lot_physical(self, org: str, lot_id: str) -> float:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        total = Decimal("0")
        found = False
        for m in active_only(bag.get("stock_movement") or []):
            if str(m.get("lot_id")) != str(lot_id):
                continue
            found = True
            qty = _dec(m.get("quantity"))
            mt = str(m.get("movement_type") or m.get("type") or "")
            if mt in {"RECEIPT", "RETURN"} or (mt == "ADJUSTMENT" and qty >= 0):
                total += abs(qty)
            else:
                total -= abs(qty)
        if found:
            return _round4(float(total))
        lot = self._ops_find(org, "inventory_lot", lot_id)
        return _round4(_qty((lot or {}).get("quantity")))

    async def _add_movement(
        self,
        org: str,
        *,
        movement_type: str,
        quantity: float,
        lot_id: str,
        operation_id: str | None,
        role: str | None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        extra = extra or {}
        key = extra.get("idempotency_key")
        hit = self._idempotent(org, "stock_movement", key)
        if hit:
            return {"ok": True, "item": hit, "idempotent": True}
        if movement_type not in MOVEMENT_TYPES:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип движения"}
        if quantity <= 0 and movement_type not in {"ADJUSTMENT"}:
            return {"ok": False, "error": "validation", "message_ru": "Количество должно быть больше нуля"}
        if movement_type in {"SALE", "WRITE_OFF", "PROCESSING", "TRANSFER"}:
            avail = self._lot_physical(org, lot_id)
            if quantity - avail > 1e-6:
                return {"ok": False, "error": "validation", "message_ru": "Недостаточно остатка на складе"}
        payload = {
            "title": extra.get("title") or f"{movement_type} {quantity}",
            "movement_type": movement_type,
            "type": movement_type,
            "quantity": quantity,
            "lot_id": lot_id,
            "operation_id": operation_id,
            "warehouse_id": extra.get("warehouse_id"),
            "deal_id": extra.get("deal_id"),
            "counterparty_id": extra.get("counterparty_id"),
            "loss_kind": extra.get("loss_kind"),
            "idempotency_key": key,
            "notes": extra.get("notes"),
        }
        saved = await self.create_entity(org, "stock_movement", payload, role)  # type: ignore[attr-defined]
        if saved.get("ok"):
            phys = self._lot_physical(org, lot_id)
            await self.update_entity(org, "inventory_lot", lot_id, {"quantity": phys}, role)  # type: ignore[attr-defined]
        return saved

    def _op_totals(self, org: str, op: dict[str, Any]) -> dict[str, Any]:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        oid = str(op.get("id"))
        deals = [d for d in active_only(bag.get("deal") or []) if str(d.get("operation_id")) == oid]
        purchases = [d for d in deals if str(d.get("side") or "buy") == "buy"]
        sales = [d for d in deals if str(d.get("side")) == "sell" and str(d.get("status")) not in {"cancelled"}]
        lots = [l for l in active_only(bag.get("inventory_lot") or []) if str(l.get("operation_id")) == oid]
        moves = [m for m in active_only(bag.get("stock_movement") or []) if str(m.get("operation_id")) == oid]
        expenses = [e for e in active_only(bag.get("expense") or []) if str(e.get("operation_id")) == oid]
        planned = _num(op.get("planned_qty")) or sum(_num(d.get("quantity")) or 0 for d in purchases)
        received = sum(_qty(m.get("quantity")) for m in moves if str(m.get("movement_type")) == "RECEIPT")
        process_loss = sum(
            _qty(m.get("quantity"))
            for m in moves
            if str(m.get("movement_type")) in {"PROCESSING", "WRITE_OFF"} and str(m.get("loss_kind") or "") in {"drying", "cleaning", "write_off", "warehouse"}
        )
        sold = sum(_qty(m.get("quantity")) for m in moves if str(m.get("movement_type")) == "SALE")
        usable = _round4(received - process_loss)
        remaining = _round4(sum(self._lot_physical(org, str(l.get("id"))) for l in lots))
        purchase_planned = None
        for d in purchases:
            qty, price = _num(d.get("quantity")), _num(d.get("price"))
            if qty is not None and price is not None:
                purchase_planned = round((purchase_planned or 0) + qty * price, 2)
        sales_value = None
        for d in sales:
            amt = _num(d.get("amount"))
            if amt is None:
                q, p = _num(d.get("quantity")), _num(d.get("price"))
                amt = round(q * p, 2) if q is not None and p is not None else None
            if amt is not None:
                sales_value = round((sales_value or 0) + amt, 2)
        exp_total = None
        for e in expenses:
            if str(e.get("status")) in {"cancelled"}:
                continue
            amt = _num(e.get("amount"))
            if amt is not None:
                exp_total = round((exp_total or 0) + amt, 2)
        return {
            "planned_qty": planned or None,
            "received_qty": received or None,
            "process_loss_qty": process_loss or None,
            "usable_qty": usable if received else None,
            "sold_qty": sold or None,
            "remaining_qty": remaining if lots else (None if not received else remaining),
            "purchase_planned_value": purchase_planned,
            "sales_value": sales_value,
            "expenses_total": exp_total,
        }

    def _cost_basis(self, org: str, op: dict[str, Any], totals: dict[str, Any], role: str | None) -> dict[str, Any]:
        from services.agro_ops.service import active_only

        if not can(role, "finance") and not can(role, "margins"):
            return {"masked": True, "message_ru": "Нет доступа к себестоимости"}
        bag = self._bag(org)  # type: ignore[attr-defined]
        oid = str(op.get("id"))
        components: list[dict[str, Any]] = []
        purchases = [d for d in active_only(bag.get("deal") or []) if str(d.get("operation_id")) == oid and str(d.get("side") or "buy") == "buy"]
        received = totals.get("received_qty")
        purchase_actual = None
        if received:
            for d in purchases:
                price = _num(d.get("accepted_price")) or _num(d.get("price"))
                if price is not None:
                    purchase_actual = round((purchase_actual or 0) + received * price, 2)
                    components.append({"id": "purchase", "label_ru": "Закупка", "amount": round(received * price, 2), "source": "deal", "source_id": d.get("id")})
        for e in active_only(bag.get("expense") or []):
            if str(e.get("operation_id")) != oid or str(e.get("status")) == "cancelled":
                continue
            amt = _num(e.get("amount"))
            if amt is None:
                continue
            components.append({"id": e.get("category") or "other", "label_ru": dict(EXPENSE_CATEGORIES).get(str(e.get("category") or "other"), "Прочее"), "amount": amt, "source": "expense", "source_id": e.get("id")})
        total = round(sum(c["amount"] for c in components), 2) if components else None
        usable = totals.get("usable_qty")
        per_t = round(total / usable, 4) if total is not None and usable else None
        by_id: dict[str, float] = {}
        for c in components:
            by_id[c["id"]] = round(by_id.get(c["id"], 0) + c["amount"], 2)
        per = {}
        if usable and total is not None:
            per = {
                "purchase_per_t": round((by_id.get("purchase") or 0) / usable, 4),
                "inbound_logistics_per_t": round(((by_id.get("transport") or 0) + (by_id.get("loading") or 0) + (by_id.get("unloading") or 0)) / usable, 4),
                "processing_per_t": round(((by_id.get("drying") or 0) + (by_id.get("cleaning") or 0)) / usable, 4),
                "storage_per_t": round((by_id.get("storage") or 0) / usable, 4),
                "other_per_t": round((total - (by_id.get("purchase") or 0)) / usable, 4) if total else None,
                "actual_cost_per_t": per_t,
            }
        return {"components": components, "total_cost": total, "per_ton": per, "cost_missing": total is None}

    def _pnl(self, totals: dict[str, Any], cost: dict[str, Any], role: str | None) -> dict[str, Any]:
        if not can(role, "margins"):
            return {"masked": True}
        sold = totals.get("sold_qty")
        revenue = totals.get("sales_value")
        per_t = (cost.get("per_ton") or {}).get("actual_cost_per_t")
        if not sold or revenue is None or per_t is None:
            return {"message_ru": "Недостаточно данных для расчёта фактической прибыли", "calculable": False}
        cogs = round(sold * per_t, 2)
        expenses = totals.get("expenses_total") or 0
        # expenses already in cost basis; direct expenses shown separately but COGS uses full actual cost/t
        profit = round(revenue - cogs, 2)
        margin = round(profit / revenue * 100, 2) if revenue else None
        return {
            "calculable": True,
            "revenue": revenue,
            "cogs": cogs,
            "direct_expenses": expenses,
            "gross_profit": profit,
            "margin_pct": margin,
        }

    async def create_operation(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        crop = _s(body.get("crop") or body.get("commodity") or "Пшеница")
        planned = _num(body.get("planned_qty") or body.get("quantity"))
        item = {
            "title": body.get("title") or crop,
            "crop": crop,
            "commodity": crop,
            "quality_class": body.get("quality_class") or body.get("grade"),
            "harvest_year": body.get("harvest_year"),
            "origin": body.get("origin"),
            "purpose": body.get("purpose"),
            "unit": body.get("unit") or "т",
            "planned_qty": planned,
            "currency": body.get("currency") or "UAH",
            "supplier_id": body.get("supplier_id") or body.get("counterparty_id"),
            "purchase_deal_id": body.get("purchase_deal_id") or body.get("deal_id"),
            "contract_id": body.get("contract_id"),
            "warehouse_id": body.get("warehouse_id"),
            "weight_tolerance_pct": _num(body.get("weight_tolerance_pct")) if body.get("weight_tolerance_pct") not in (None, "") else 0.5,
            "weight_tolerance_kg": _num(body.get("weight_tolerance_kg")),
            "transport_mode": body.get("transport_mode") or "carrier",
            "load_place": body.get("load_place"),
            "dest_place": body.get("dest_place"),
            "planned_trucks": body.get("planned_trucks"),
            "planned_logistics_cost": _num(body.get("planned_logistics_cost")),
            "planned_price": _num(body.get("price") or body.get("planned_price")),
            "responsible": body.get("responsible"),
            "quality_spec": body.get("quality_spec") or QUALITY_PROFILES.get(crop, {}),
            "status": "draft",
            "number": self._next_op_number(org),
        }
        saved = await self.create_entity(org, "agro_operation", item, role)  # type: ignore[attr-defined]
        if not saved.get("ok"):
            return saved
        op = saved["item"]
        if body.get("create_purchase") or not item.get("purchase_deal_id"):
            if planned is not None and body.get("price") not in (None, ""):
                deal = await self.create_entity(  # type: ignore[attr-defined]
                    org,
                    "deal",
                    {
                        "title": f"{op['number']} закупка {crop}",
                        "side": "buy",
                        "crop": crop,
                        "quantity": planned,
                        "price": body.get("price"),
                        "currency": item["currency"],
                        "unit": item["unit"],
                        "counterparty_id": item["supplier_id"],
                        "contract_id": item["contract_id"],
                        "operation_id": op["id"],
                        "operation_number": op["number"],
                        "vat": body.get("vat"),
                        "schedule_kind": body.get("schedule_kind"),
                        "load_place": body.get("load_place"),
                        "planned_at": body.get("planned_loading_at") or body.get("planned_at"),
                    },
                    role,
                )
                if deal.get("ok"):
                    await self.update_entity(org, "agro_operation", op["id"], {"purchase_deal_id": deal["item"]["id"]}, role)  # type: ignore[attr-defined]
                    op["purchase_deal_id"] = deal["item"]["id"]
        return {"ok": True, "item": op}

    async def operation_360(self, organization_id: str, item_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        op = self._ops_find(org, "agro_operation", item_id)
        if not op:
            return {"ok": False, "error": "not_found", "message_ru": "Операция не найдена"}
        if self._manager_scope_ops(role, query) and _s(op.get("responsible") or op.get("created_by")) not in {_s((query or {}).get("actor")), "", _s(op.get("responsible"))}:
            pass
        bag = self._bag(org)  # type: ignore[attr-defined]
        oid = str(op["id"])
        tab = (query or {}).get("tab") or "overview"
        totals = self._op_totals(org, op)
        cost = self._cost_basis(org, op, totals, role)
        pnl = self._pnl(totals, cost, role)
        linked = {
            "deals": [d for d in active_only(bag.get("deal") or []) if str(d.get("operation_id")) == oid],
            "trucks": [t for t in active_only(bag.get("truck_run") or []) if str(t.get("operation_id")) == oid],
            "weighings": [w for w in active_only(bag.get("weighing") or []) if str(w.get("operation_id")) == oid],
            "quality": [q for q in active_only(bag.get("quality_test") or []) if str(q.get("operation_id")) == oid],
            "lots": [l for l in active_only(bag.get("inventory_lot") or []) if str(l.get("operation_id")) == oid],
            "movements": [m for m in active_only(bag.get("stock_movement") or []) if str(m.get("operation_id")) == oid],
            "expenses": [e for e in active_only(bag.get("expense") or []) if str(e.get("operation_id")) == oid] if can(role, "finance") else [],
            "payments": [p for p in active_only(bag.get("payment") or []) if str(p.get("operation_id")) == oid or str(p.get("deal_id") or "") in {str(d.get("id")) for d in active_only(bag.get("deal") or []) if str(d.get("operation_id")) == oid}],
            "documents": [f for f in active_only(bag.get("file") or []) if str(f.get("operation_id")) == oid or str(f.get("entity_id")) == oid],
            "tasks": [t for t in active_only(bag.get("task") or []) if str(t.get("operation_id")) == oid],
            "exceptions": [e for e in active_only(bag.get("ops_exception") or []) if str(e.get("operation_id")) == oid],
            "activity": [a for a in bag.get("activity") or [] if str(a.get("entity_id")) == oid],
        }
        if not can(role, "finance"):
            linked["payments"] = []
        supplier = self._ops_find(org, "counterparty", str(op.get("supplier_id") or ""))
        header = {
            **{k: op.get(k) for k in ("id", "number", "crop", "status", "unit", "is_demo")},
            "status_ru": dict(OPERATION_STATUSES).get(str(op.get("status") or "draft"), op.get("status")),
            "supplier": (supplier or {}).get("name"),
            "supplier_id": op.get("supplier_id"),
            **totals,
            "purchase_value": totals.get("purchase_planned_value") if can(role, "finance") else None,
            "sales_value": totals.get("sales_value") if can(role, "finance") else None,
            "actual_expenses": totals.get("expenses_total") if can(role, "finance") else None,
            "pnl": pnl if can(role, "margins") else None,
            "allowed_statuses": sorted(OP_TRANSITIONS.get(str(op.get("status") or "draft"), set())),
        }
        rows = linked.get(tab) or []
        if tab == "overview":
            rows = []
        try:
            limit = max(1, min(100, int((query or {}).get("limit") or 50)))
            offset = max(0, int((query or {}).get("offset") or 0))
        except (TypeError, ValueError):
            limit, offset = 50, 0
        plan_vs = {
            "quantity": {"plan": totals.get("planned_qty"), "actual": totals.get("received_qty")},
            "purchase_price": {"plan": _num(op.get("planned_price")), "actual": None},
            "logistics": {"plan": _num(op.get("planned_logistics_cost")), "actual": None},
            "profit": {"plan": None, "actual": (pnl or {}).get("gross_profit") if isinstance(pnl, dict) else None},
        }
        return {
            "ok": True,
            "item": header,
            "operation": op,
            "cost_basis": cost,
            "pnl": pnl,
            "plan_vs_actual": plan_vs,
            "tab": tab,
            "items": rows[offset : offset + limit],
            "total": len(rows),
            "trace_forward": self._trace(org, oid, "forward"),
            "trace_back": self._trace(org, oid, "back"),
            "can_finance": can(role, "finance"),
            "can_margins": can(role, "margins"),
            **{f"counts_{k}": len(v) for k, v in linked.items()},
        }

    def _manager_scope_ops(self, role: str | None, query: dict[str, str] | None) -> bool:
        return normalize_role(role) == "agro_manager"

    def _trace(self, org: str, oid: str, direction: str) -> list[dict[str, str]]:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        op = self._ops_find(org, "agro_operation", oid)
        if not op:
            return []
        steps = []
        if direction == "back":
            steps = [
                {"kind": "agro_operation", "id": oid, "label": op.get("number") or oid},
                {"kind": "counterparty", "id": str(op.get("supplier_id") or ""), "label": "supplier"},
                {"kind": "deal", "id": str(op.get("purchase_deal_id") or ""), "label": "purchase"},
                {"kind": "contract", "id": str(op.get("contract_id") or ""), "label": "contract"},
            ]
        else:
            lots = [l for l in active_only(bag.get("inventory_lot") or []) if str(l.get("operation_id")) == oid]
            sales = [d for d in active_only(bag.get("deal") or []) if str(d.get("operation_id")) == oid and str(d.get("side")) == "sell"]
            steps = [{"kind": "inventory_lot", "id": str(l.get("id")), "label": str(l.get("lot_number") or l.get("id"))} for l in lots]
            steps += [{"kind": "deal", "id": str(d.get("id")), "label": str(d.get("title") or d.get("id"))} for d in sales]
        return [s for s in steps if s.get("id")]

    async def list_operations(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        q = query or {}
        rows = active_only(self._bag(org).get("agro_operation") or [])  # type: ignore[attr-defined]
        if q.get("status"):
            rows = [r for r in rows if str(r.get("status")) == q["status"]]
        if q.get("crop"):
            rows = [r for r in rows if q["crop"].lower() in _s(r.get("crop")).lower()]
        search = (q.get("q") or "").strip().lower()
        if search:
            rows = [r for r in rows if search in _s(r.get("number")).lower() or search in _s(r.get("crop")).lower() or search in _s(r.get("title")).lower()]
        items = []
        for r in rows:
            tot = self._op_totals(org, r)
            items.append({"id": r.get("id"), "number": r.get("number"), "crop": r.get("crop"), "status": r.get("status"), "status_ru": dict(OPERATION_STATUSES).get(str(r.get("status") or ""), r.get("status")), **tot, "is_demo": bool(r.get("is_demo"))})
        try:
            limit = max(1, min(100, int(q.get("limit") or 40)))
            offset = max(0, int(q.get("offset") or 0))
        except (TypeError, ValueError):
            limit, offset = 40, 0
        return {"ok": True, "items": items[offset : offset + limit], "total": len(items)}

    async def set_operation_status(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        op = self._ops_find(org, "agro_operation", item_id)
        if not op:
            return {"ok": False, "error": "not_found", "message_ru": "Операция не найдена"}
        nxt = str(body.get("status") or "")
        cur = str(op.get("status") or "draft")
        if nxt == cur:
            return {"ok": True, "item": op}
        if nxt not in OP_TRANSITIONS.get(cur, set()):
            return {"ok": False, "error": "validation", "message_ru": f"Нельзя перейти из «{dict(OPERATION_STATUSES).get(cur, cur)}» в «{dict(OPERATION_STATUSES).get(nxt, nxt)}»"}
        result = await self.update_entity(org, "agro_operation", item_id, {"status": nxt}, role)  # type: ignore[attr-defined]
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org, entity_type="agro_operation", entity_id=item_id, action="status_changed",
            summary=f"Статус операции {cur} → {nxt}", role=role, payload={"from": cur, "to": nxt, "source": body.get("source") or "USER"},
        )
        return result

    async def add_truck_run(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        key = body.get("idempotency_key")
        hit = self._idempotent(org, "truck_run", key)
        if hit:
            return {"ok": True, "item": hit, "idempotent": True}
        op_id = str(body.get("operation_id") or "")
        op = self._ops_find(org, "agro_operation", op_id)
        if not op:
            return {"ok": False, "error": "not_found", "message_ru": "Операция не найдена"}
        vehicle_id = body.get("vehicle_id")
        plate = _s(body.get("plate") or body.get("truck"))
        if not vehicle_id and plate:
            from services.agro_ops.service import active_only

            existing = next((v for v in active_only(self._bag(org).get("vehicle") or []) if _s(v.get("plate") or v.get("name")).lower() == plate.lower()), None)  # type: ignore[attr-defined]
            if existing:
                vehicle_id = existing.get("id")
        payload = {
            "title": body.get("title") or plate or "Рейс",
            "operation_id": op_id,
            "operation_number": op.get("number"),
            "vehicle_id": vehicle_id,
            "trailer_id": body.get("trailer_id"),
            "driver_id": body.get("driver_id"),
            "driver_name": body.get("driver_name") or body.get("driver"),
            "driver_phone": body.get("driver_phone") or body.get("phone"),
            "carrier_id": body.get("carrier_id"),
            "plate": plate,
            "trailer_plate": body.get("trailer_plate"),
            "load_place": body.get("load_place") or op.get("load_place"),
            "dest_place": body.get("dest_place") or op.get("dest_place"),
            "planned_weight": _num(body.get("planned_weight") or body.get("planned_qty")),
            "planned_at": body.get("planned_at") or body.get("loading_at"),
            "crop": op.get("crop"),
            "status": "assigned",
            "idempotency_key": key,
        }
        return await self.create_entity(org, "truck_run", payload, role)  # type: ignore[attr-defined]

    async def set_truck_status(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        run = self._ops_find(org, "truck_run", item_id)
        if not run:
            return {"ok": False, "error": "not_found", "message_ru": "Рейс не найден"}
        nxt = str(body.get("status") or "")
        cur = str(run.get("status") or "assigned")
        key = body.get("idempotency_key") or f"truck-{item_id}-{nxt}"
        if str(run.get("last_status_key") or "") == key:
            return {"ok": True, "item": run, "idempotent": True}
        if nxt not in TRUCK_TRANSITIONS.get(cur, set()):
            return {"ok": False, "error": "validation", "message_ru": f"Нельзя сменить статус рейса {cur} → {nxt}"}
        return await self.update_entity(org, "truck_run", item_id, {"status": nxt, "last_status_key": key, "status_at": datetime.now(timezone.utc).isoformat()}, role)  # type: ignore[attr-defined]

    async def add_weighing(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        key = body.get("idempotency_key")
        hit = self._idempotent(org, "weighing", key)
        if hit:
            return {"ok": True, "item": hit, "idempotent": True}
        gross = _num(body.get("gross"))
        tare = _num(body.get("tare"))
        if gross is None or tare is None:
            return {"ok": False, "error": "validation", "message_ru": "Укажите брутто и тару"}
        net = _round4(gross - tare)
        given = _num(body.get("net"))
        if given is not None and abs(given - net) > 0.001:
            return {"ok": False, "error": "validation", "message_ru": "Нетто не совпадает с брутто − тара"}
        scale = str(body.get("scale") or body.get("scale_type") or "receiving")
        op_id = str(body.get("operation_id") or "")
        op = self._ops_find(org, "agro_operation", op_id)
        payload = {
            "title": body.get("title") or f"Взвешивание {scale}",
            "operation_id": op_id,
            "operation_number": (op or {}).get("number"),
            "truck_run_id": body.get("truck_run_id"),
            "vehicle_id": body.get("vehicle_id"),
            "scale": scale,
            "gross": gross,
            "tare": tare,
            "net": net,
            "unit": body.get("unit") or "кг",
            "weighed_at": body.get("weighed_at") or datetime.now(timezone.utc).isoformat(),
            "idempotency_key": key,
        }
        saved = await self.create_entity(org, "weighing", payload, role)  # type: ignore[attr-defined]
        if saved.get("ok") and op:
            await self._check_weight_diff(org, op, role)
        return saved

    async def _check_weight_diff(self, org: str, op: dict[str, Any], role: str | None) -> None:
        from services.agro_ops.service import active_only

        oid = str(op.get("id"))
        rows = [w for w in active_only(self._bag(org).get("weighing") or []) if str(w.get("operation_id")) == oid]  # type: ignore[attr-defined]
        load = sum(_num(w.get("net")) or 0 for w in rows if str(w.get("scale")) == "loading")
        recv = sum(_num(w.get("net")) or 0 for w in rows if str(w.get("scale")) == "receiving")
        if not load or not recv:
            return
        diff = _round4(recv - load)
        pct = round(diff / load * 100, 3) if load else None
        tol_pct = _num(op.get("weight_tolerance_pct")) or 0.5
        tol_kg = _num(op.get("weight_tolerance_kg"))
        exceeded = abs(pct or 0) > tol_pct
        if tol_kg is not None and abs(diff) > tol_kg:
            exceeded = True
        if exceeded:
            await self._open_exception(
                org,
                operation_id=oid,
                kind="weight_discrepancy",
                title="⚠ Weight discrepancy",
                detail=f"Разница {diff} ({pct}%). Не является обвинением перевозчика или поставщика.",
                role=role,
            )

    async def _open_exception(self, org: str, *, operation_id: str, kind: str, title: str, detail: str, role: str | None) -> dict[str, Any]:
        from services.agro_ops.service import active_only

        existing = next(
            (
                e
                for e in active_only(self._bag(org).get("ops_exception") or [])  # type: ignore[attr-defined]
                if str(e.get("operation_id")) == operation_id and str(e.get("kind")) == kind and str(e.get("status")) == "OPEN"
            ),
            None,
        )
        if existing:
            return {"ok": True, "item": existing}
        return await self.create_entity(  # type: ignore[attr-defined]
            org,
            "ops_exception",
            {
                "title": title,
                "kind": kind,
                "detail": detail,
                "operation_id": operation_id,
                "status": "OPEN",
                "severity": "HIGH",
            },
            role,
        )

    def compare_quality(self, spec: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
        results = []
        worst = "PASS"
        for metric, rule in (spec or {}).items():
            if not isinstance(rule, dict):
                continue
            val = _num(actual.get(metric))
            row = {"metric": metric, "label_ru": QUALITY_METRICS.get(metric, {}).get("label_ru", metric), "actual": val, "rule": rule, "result": "PASS"}
            if val is None:
                row["result"] = "WARNING"
                worst = "WARNING" if worst == "PASS" else worst
            else:
                if rule.get("max") is not None and val > float(rule["max"]):
                    row["result"] = "FAIL"
                    worst = "FAIL"
                if rule.get("min") is not None and val < float(rule["min"]):
                    row["result"] = "FAIL"
                    worst = "FAIL"
            results.append(row)
        return {"result": worst, "metrics": results}

    async def add_quality_test(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        if not (can(role, "create") or can(role, "quality")):
            return require(role, "create") or {"ok": False, "error": "forbidden", "message_ru": "Нет права на качество"}
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        op = self._ops_find(org, "agro_operation", str(body.get("operation_id") or ""))
        if not op:
            return {"ok": False, "error": "not_found", "message_ru": "Операция не найдена"}
        actual = body.get("metrics") or {k: body.get(k) for k in QUALITY_METRICS if body.get(k) not in (None, "")}
        spec = body.get("spec") or op.get("quality_spec") or QUALITY_PROFILES.get(str(op.get("crop") or ""), {})
        compared = self.compare_quality(spec, actual)
        payload = {
            "title": body.get("title") or f"Анализ {op.get('crop')}",
            "operation_id": op["id"],
            "operation_number": op.get("number"),
            "crop": op.get("crop"),
            "metrics": actual,
            "spec": spec,
            "result": compared["result"],
            "comparison": compared,
            "idempotency_key": body.get("idempotency_key"),
        }
        saved = await self.create_entity(org, "quality_test", payload, role)  # type: ignore[attr-defined]
        if saved.get("ok") and compared["result"] == "FAIL":
            await self._open_exception(org, operation_id=str(op["id"]), kind="quality_fail", title="Проблема по качеству", detail="Фактический анализ не соответствует спецификации", role=role)
        return {**saved, "comparison": compared}

    async def quality_decision(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        if not (can(role, "approve") or can(role, "quality") or can(role, "update")):
            return require(role, "approve")
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        test = self._ops_find(org, "quality_test", str(body.get("quality_test_id") or body.get("test_id") or ""))
        if not test:
            return {"ok": False, "error": "not_found", "message_ru": "Анализ не найден"}
        decision = str(body.get("decision") or "")
        if decision not in {d for d, _ in QUALITY_DECISIONS}:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестное решение по качеству"}
        reason = _s(body.get("reason"))
        if not reason:
            return {"ok": False, "error": "validation", "message_ru": "Укажите причину решения"}
        patch = {
            "decision": decision,
            "decision_reason": reason,
            "decision_by": body.get("responsible") or normalize_role(role),
            "decision_at": datetime.now(timezone.utc).isoformat(),
        }
        if decision == "discount":
            adj = _num(body.get("adjustment"))
            orig = _num(body.get("original_price"))
            if orig is None or adj is None:
                return {"ok": False, "error": "validation", "message_ru": "Для скидки укажите исходную цену и корректировку"}
            patch["original_price"] = orig
            patch["price_adjustment"] = adj
            patch["accepted_price"] = round(orig + adj, 4) if adj < 0 or True else round(orig - abs(adj), 4)
            op = self._ops_find(org, "agro_operation", str(test.get("operation_id")))
            if op and op.get("purchase_deal_id"):
                deal = self._ops_find(org, "deal", str(op["purchase_deal_id"]))
                if deal:
                    await self.update_entity(org, "deal", str(deal["id"]), {"accepted_price": patch["accepted_price"], "price_adjustment": adj, "price_adjustment_reason": reason}, role)  # type: ignore[attr-defined]
                    await self._activity(  # type: ignore[attr-defined]
                        organization_id=org, entity_type="deal", entity_id=str(deal["id"]), action="price_adjusted",
                        summary=f"Качество: {orig} → {patch['accepted_price']}", role=role,
                        before={"price": deal.get("price")}, after={"accepted_price": patch["accepted_price"]},
                    )
        return await self.update_entity(org, "quality_test", str(test["id"]), patch, role)  # type: ignore[attr-defined]

    async def receive_operation(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        op = self._ops_find(org, "agro_operation", str(body.get("operation_id") or ""))
        if not op:
            return {"ok": False, "error": "not_found", "message_ru": "Операция не найдена"}
        key = body.get("idempotency_key") or f"receipt-{op['id']}"
        hit = self._idempotent(org, "stock_movement", key)
        if hit:
            return {"ok": False, "error": "duplicate", "message_ru": "Приход по этой операции уже создан", "item": hit}
        warehouse_id = str(body.get("warehouse_id") or op.get("warehouse_id") or "")
        if not warehouse_id:
            return {"ok": False, "error": "validation", "message_ru": "Укажите склад"}
        weighings = [w for w in active_only(self._bag(org).get("weighing") or []) if str(w.get("operation_id")) == str(op["id"])]  # type: ignore[attr-defined]
        recv_net = sum((_num(w.get("net")) or 0) for w in weighings if str(w.get("scale")) == "receiving")
        if not recv_net:
            recv_net = sum((_num(w.get("net")) or 0) for w in weighings)
        qty = _num(body.get("quantity"))
        if qty is None:
            # convert kg tickets to tonnes if unit is kg
            unit = (weighings[0].get("unit") if weighings else "т") or "т"
            qty = recv_net / 1000.0 if str(unit).lower() in {"кг", "kg"} else recv_net
        if not qty:
            return {"ok": False, "error": "validation", "message_ru": "Нет фактического веса для прихода. Плановый объём не принимается."}
        tests = [t for t in active_only(self._bag(org).get("quality_test") or []) if str(t.get("operation_id")) == str(op["id"])]  # type: ignore[attr-defined]
        failed = [t for t in tests if str(t.get("result")) == "FAIL" and str(t.get("decision") or "") not in {"accept", "discount", "clean"}]
        if failed:
            return {"ok": False, "error": "validation", "message_ru": "Есть непройденный анализ качества без решения"}
        year = _now().year
        crop_code = "".join(ch for ch in str(op.get("crop") or "CROP").upper() if ch.isalpha())[:8] or "CROP"
        seq = 1 + len(active_only(self._bag(org).get("inventory_lot") or []))  # type: ignore[attr-defined]
        lot = await self.create_entity(  # type: ignore[attr-defined]
            org,
            "inventory_lot",
            {
                "lot_number": body.get("lot_number") or f"LOT-{year}-{crop_code}-{seq:04d}",
                "warehouse_id": warehouse_id,
                "commodity": op.get("crop"),
                "crop": op.get("crop"),
                "quantity": 0,
                "unit": op.get("unit") or "т",
                "operation_id": op["id"],
                "operation_number": op.get("number"),
                "supplier": op.get("supplier_id"),
                "counterparty_id": op.get("supplier_id"),
                "deal_id": op.get("purchase_deal_id"),
                "quality": (tests[-1].get("metrics") if tests else {}),
                "arrival_date": body.get("date") or _now().date().isoformat(),
            },
            role,
        )
        if not lot.get("ok"):
            return lot
        lot_id = str(lot["item"]["id"])
        mov = await self._add_movement(
            org, movement_type="RECEIPT", quantity=_round4(qty), lot_id=lot_id, operation_id=str(op["id"]), role=role,
            extra={"idempotency_key": key, "warehouse_id": warehouse_id, "title": f"Приход {op.get('number')}"},
        )
        if not mov.get("ok"):
            return mov
        await self.update_entity(org, "agro_operation", str(op["id"]), {"warehouse_id": warehouse_id, "status": "warehoused" if str(op.get("status")) in {"receiving", "quality", "in_transit"} else op.get("status")}, role)  # type: ignore[attr-defined]
        return {"ok": True, "item": lot["item"], "movement": mov.get("item"), "received_qty": qty}

    async def process_operation(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        lot_id = str(body.get("lot_id") or "")
        inp = _num(body.get("input_qty") or body.get("input"))
        out = _num(body.get("output_qty") or body.get("output"))
        if not lot_id or inp is None or out is None:
            return {"ok": False, "error": "validation", "message_ru": "Укажите партию, вход и выход"}
        loss = _round4(inp - out)
        kind = str(body.get("process_type") or "drying")
        loss_kind = "drying" if kind in {"drying", "сушка"} else ("cleaning" if kind in {"cleaning", "очистка"} else "write_off")
        if loss > 0:
            mov = await self._add_movement(
                org, movement_type="PROCESSING", quantity=loss, lot_id=lot_id,
                operation_id=str(body.get("operation_id") or ""), role=role,
                extra={"loss_kind": loss_kind, "idempotency_key": body.get("idempotency_key"), "title": f"{kind} loss {loss}"},
            )
            if not mov.get("ok"):
                return mov
        if body.get("cost") not in (None, ""):
            await self.add_expense(organization_id, {**body, "category": "drying" if loss_kind == "drying" else "cleaning", "amount": body.get("cost")}, role)
        return {"ok": True, "input": inp, "output": out, "loss": loss, "loss_kind": loss_kind}

    async def fifo_suggest(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        need = _num(body.get("quantity")) or 0
        crop = _s(body.get("crop"))
        lots = [
            l for l in active_only(self._bag(org).get("inventory_lot") or [])  # type: ignore[attr-defined]
            if (not crop or crop.lower() in _s(l.get("commodity") or l.get("crop")).lower())
        ]
        lots.sort(key=lambda x: str(x.get("arrival_date") or x.get("created_at") or ""))
        alloc = []
        left = need
        for lot in lots:
            avail = self._lot_available(org, str(lot["id"]))
            if avail <= 0:
                continue
            take = min(avail, left)
            alloc.append({"lot_id": lot["id"], "lot_number": lot.get("lot_number"), "quantity": _round4(take), "available": avail})
            left = _round4(left - take)
            if left <= 0:
                break
        return {"ok": True, "suggestion": alloc, "shortfall": left if left > 0 else 0, "auto": False, "message_ru": "FIFO — предложение. Автораспределение выключено."}

    async def allocate_sale(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        op = self._ops_find(org, "agro_operation", str(body.get("operation_id") or ""))
        if not op:
            return {"ok": False, "error": "not_found", "message_ru": "Операция не найдена"}
        allocations = body.get("allocations") or []
        if not allocations:
            return {"ok": False, "error": "validation", "message_ru": "Укажите распределение по партиям"}
        qty = 0.0
        for row in allocations:
            lot_id = str(row.get("lot_id") or "")
            take = _num(row.get("quantity")) or 0
            avail = self._lot_available(org, lot_id)
            if take - avail > 1e-6:
                return {"ok": False, "error": "validation", "message_ru": f"Нельзя отгрузить {take} т: доступно {avail} т", "available": avail}
            qty += take
        deal = await self.create_entity(  # type: ignore[attr-defined]
            org,
            "deal",
            {
                "title": body.get("title") or f"{op.get('number')} продажа",
                "side": "sell",
                "crop": op.get("crop"),
                "quantity": qty,
                "price": body.get("price"),
                "currency": body.get("currency") or op.get("currency") or "UAH",
                "counterparty_id": body.get("buyer_id") or body.get("counterparty_id"),
                "contract_id": body.get("contract_id"),
                "operation_id": op["id"],
                "operation_number": op.get("number"),
                "allocations": allocations,
                "unit": op.get("unit") or "т",
            },
            role,
        )
        if not deal.get("ok"):
            return deal
        ship = bool(body.get("ship"))
        movements = []
        if ship:
            for row in allocations:
                mov = await self._add_movement(
                    org, movement_type="SALE", quantity=_num(row.get("quantity")) or 0,
                    lot_id=str(row.get("lot_id")), operation_id=str(op["id"]), role=role,
                    extra={"deal_id": deal["item"]["id"], "idempotency_key": f"sale-{deal['item']['id']}-{row.get('lot_id')}"},
                )
                if not mov.get("ok"):
                    return mov
                movements.append(mov.get("item"))
            await self.update_entity(org, "deal", deal["item"]["id"], {"shipped": True}, role)  # type: ignore[attr-defined]
        tot = self._op_totals(org, op)
        nxt = "sold" if (tot.get("remaining_qty") or 0) <= 1e-6 else "partly_sold"
        if str(op.get("status")) in {"warehoused", "partly_sold"}:
            await self.update_entity(org, "agro_operation", str(op["id"]), {"status": nxt}, role)  # type: ignore[attr-defined]
        return {"ok": True, "item": deal["item"], "movements": movements, "shipped": ship}

    async def add_expense(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "finance")
        if denied:
            denied = require(role, "create")
            if denied:
                return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        key = body.get("idempotency_key")
        hit = self._idempotent(org, "expense", key)
        if hit:
            return {"ok": True, "item": hit, "idempotent": True}
        amt = _num(body.get("amount"))
        if amt is None:
            return {"ok": False, "error": "validation", "message_ru": "Укажите сумму расхода"}
        cat = str(body.get("category") or "other")
        payload = {
            "title": body.get("title") or dict(EXPENSE_CATEGORIES).get(cat, "Расход"),
            "category": cat,
            "amount": amt,
            "currency": body.get("currency") or "UAH",
            "date": body.get("date") or _now().date().isoformat(),
            "counterparty_id": body.get("counterparty_id"),
            "operation_id": body.get("operation_id"),
            "truck_run_id": body.get("truck_run_id"),
            "shipment_id": body.get("shipment_id"),
            "status": body.get("status") or "posted",
            "idempotency_key": key,
            "document": body.get("document"),
        }
        return await self.create_entity(org, "expense", payload, role)  # type: ignore[attr-defined]

    async def grain_today(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        trucks = active_only(bag.get("truck_run") or [])
        ops = active_only(bag.get("agro_operation") or [])
        ex = active_only(bag.get("ops_exception") or [])
        weigh = active_only(bag.get("weighing") or [])
        recv_t = 0.0
        for w in weigh:
            if str(w.get("scale")) == "receiving":
                n = _num(w.get("net")) or 0
                recv_t += n / 1000.0 if str(w.get("unit") or "").lower() in {"кг", "kg"} else n
        sold = sum((self._op_totals(org, o).get("sold_qty") or 0) for o in ops)
        planned = sum((self._op_totals(org, o).get("planned_qty") or 0) for o in ops if str(o.get("status")) not in {"closed", "cancelled"})
        metrics = [
            {"id": "loading", "label_ru": "Машин на загрузке", "value": len([t for t in trucks if str(t.get("status")) == "loading"]), "view": "operations", "filter": "loading"},
            {"id": "in_transit", "label_ru": "Машин в пути", "value": len([t for t in trucks if str(t.get("status")) == "in_transit"]), "view": "operations", "filter": "in_transit"},
            {"id": "unloading", "label_ru": "Машин на выгрузке", "value": len([t for t in trucks if str(t.get("status")) == "unloading"]), "view": "operations", "filter": "unloading"},
            {"id": "expected_t", "label_ru": "Ожидается тонн", "value": planned, "view": "operations"},
            {"id": "received_t", "label_ru": "Принято тонн", "value": round(recv_t, 3), "view": "operations"},
            {"id": "shipped_t", "label_ru": "Отгружено тонн", "value": sold, "view": "operations"},
            {"id": "weight_issues", "label_ru": "Проблем по весу", "value": len([e for e in ex if str(e.get("kind")) == "weight_discrepancy" and str(e.get("status")) == "OPEN"]), "view": "operations", "filter": "weight"},
            {"id": "quality_issues", "label_ru": "Проблем по качеству", "value": len([e for e in ex if str(e.get("kind")) == "quality_fail" and str(e.get("status")) == "OPEN"]), "view": "operations", "filter": "quality"},
            {"id": "doc_overdue", "label_ru": "Просроченных документов", "value": 0, "view": "documents"},
            {"id": "pay_overdue", "label_ru": "Просроченных оплат", "value": 0, "view": "accounting"},
        ]
        return {"ok": True, "metrics": metrics, "version": OPS_VERSION}

    async def grain_stock(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        lots = active_only(self._bag(org).get("inventory_lot") or [])  # type: ignore[attr-defined]
        by_crop: dict[str, float] = {}
        by_wh: dict[str, float] = {}
        items = []
        for lot in lots:
            phys = self._lot_physical(org, str(lot["id"]))
            crop = str(lot.get("commodity") or lot.get("crop") or "Прочее")
            by_crop[crop] = round(by_crop.get(crop, 0) + phys, 4)
            wh = str(lot.get("warehouse_id") or "—")
            by_wh[wh] = round(by_wh.get(wh, 0) + phys, 4)
            items.append({"id": lot.get("id"), "lot_number": lot.get("lot_number"), "crop": crop, "warehouse_id": wh, "physical": phys, "available": self._lot_available(org, str(lot["id"])), "operation_id": lot.get("operation_id"), "operation_number": lot.get("operation_number")})
        return {"ok": True, "by_crop": [{"crop": k, "quantity": v} for k, v in by_crop.items()], "by_warehouse": [{"warehouse_id": k, "quantity": v} for k, v in by_wh.items()], "lots": items}

    async def set_exception_status(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        st = str(body.get("status") or "")
        if st not in EXCEPTION_STATUSES:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус исключения"}
        return await self.update_entity(org, "ops_exception", item_id, {"status": st}, role)  # type: ignore[attr-defined]

    async def transfer_lot(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        key = body.get("idempotency_key")
        hit = self._idempotent(org, "stock_movement", key)
        if hit:
            return {"ok": True, "item": hit, "idempotent": True}
        lot_id = str(body.get("lot_id") or "")
        dest_wh = str(body.get("to_warehouse_id") or body.get("destination_warehouse_id") or "")
        sent = _num(body.get("quantity_sent") or body.get("quantity"))
        received = _num(body.get("quantity_received"))
        if received is None:
            received = sent
        if not lot_id or not dest_wh or not sent:
            return {"ok": False, "error": "validation", "message_ru": "Укажите партию, склад назначения и количество"}
        src = self._ops_find(org, "inventory_lot", lot_id)
        if not src:
            return {"ok": False, "error": "not_found", "message_ru": "Партия не найдена"}
        if str(src.get("warehouse_id")) == dest_wh:
            return {"ok": False, "error": "validation", "message_ru": "Склад назначения совпадает с исходным"}
        avail = self._lot_physical(org, lot_id)
        if sent - avail > 1e-6:
            return {"ok": False, "error": "validation", "message_ru": f"Недостаточно остатка: доступно {avail} т"}
        out = await self._add_movement(
            org,
            movement_type="TRANSFER",
            quantity=_round4(sent),
            lot_id=lot_id,
            operation_id=str(body.get("operation_id") or src.get("operation_id") or ""),
            role=role,
            extra={"idempotency_key": key, "warehouse_id": src.get("warehouse_id"), "title": f"TRANSFER out {sent}", "notes": body.get("notes")},
        )
        if not out.get("ok"):
            return out
        dest_lot = await self.create_entity(  # type: ignore[attr-defined]
            org,
            "inventory_lot",
            {
                "lot_number": body.get("lot_number") or f"{src.get('lot_number')}-T",
                "warehouse_id": dest_wh,
                "commodity": src.get("commodity") or src.get("crop"),
                "crop": src.get("crop") or src.get("commodity"),
                "quantity": 0,
                "unit": src.get("unit") or "т",
                "operation_id": src.get("operation_id"),
                "operation_number": src.get("operation_number"),
                "supplier": src.get("supplier") or src.get("counterparty_id"),
                "counterparty_id": src.get("counterparty_id"),
                "quality": src.get("quality") or {},
                "arrival_date": body.get("date") or _now().date().isoformat(),
            },
            role,
        )
        if not dest_lot.get("ok"):
            return dest_lot
        dest_id = str(dest_lot["item"]["id"])
        inn = await self._add_movement(
            org,
            movement_type="RECEIPT",
            quantity=_round4(received),
            lot_id=dest_id,
            operation_id=str(body.get("operation_id") or src.get("operation_id") or ""),
            role=role,
            extra={"warehouse_id": dest_wh, "title": f"TRANSFER in {received}", "notes": f"from_lot={lot_id}"},
        )
        if not inn.get("ok"):
            return inn
        diff = _round4(sent - received)
        if abs(diff) > 1e-6:
            await self._open_exception(
                org,
                operation_id=str(src.get("operation_id") or body.get("operation_id") or ""),
                kind="stock_discrepancy",
                title="Разница при перемещении",
                detail=f"Отправлено {sent}, принято {received}, разница {diff}",
                role=role,
            )
        if body.get("cost") not in (None, ""):
            await self.add_expense(
                organization_id,
                {
                    "category": "transport",
                    "amount": body.get("cost"),
                    "operation_id": src.get("operation_id") or body.get("operation_id"),
                    "title": "Перемещение",
                    "currency": body.get("currency") or "UAH",
                },
                role,
            )
        return {
            "ok": True,
            "item": {
                "from_lot_id": lot_id,
                "to_lot_id": dest_id,
                "quantity_sent": sent,
                "quantity_received": received,
                "difference": diff,
                "to_warehouse_id": dest_wh,
            },
            "out": out.get("item"),
            "inn": inn.get("item"),
        }
