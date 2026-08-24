"""AGRO finance — deal economics calculator, accounting view, export (AGRO 1.0).

Calculations use Decimal for currency precision. FX rates are entered
manually; nothing is fabricated — if no rate is entered the calculator
reports «Курс не подключён».
"""

from __future__ import annotations

import csv
import io
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import Any

from services.agro_ops.rbac import require

COST_FIELDS = [
    ("transport", "Транспорт"),
    ("loading", "Погрузка"),
    ("unloading", "Разгрузка"),
    ("storage", "Хранение"),
    ("elevator", "Элеватор"),
    ("laboratory", "Лаборатория"),
    ("certification", "Сертификация"),
    ("customs", "Таможня"),
    ("brokerage", "Брокерские"),
    ("insurance", "Страхование"),
    ("commissions", "Комиссии"),
    ("bank_fees", "Банковские комиссии"),
    ("other_costs", "Прочие расходы"),
]

TWO = Decimal("0.01")


def _dec(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _money(value: Decimal) -> float:
    return float(value.quantize(TWO, rounding=ROUND_HALF_UP))


class AgroOpsFinanceMixin:
    """Mixed into AgroOpsService."""

    # ------------------------------------------------------------------
    # calculator (pure)
    # ------------------------------------------------------------------

    def compute_calculation(self, item: dict[str, Any]) -> dict[str, Any]:
        qty = _dec(item.get("quantity"))
        purchase_price = _dec(item.get("purchase_price"))
        sale_price = _dec(item.get("sale_price"))
        vat_rate = _dec(item.get("vat_rate"))  # percent, optional

        purchase_value = qty * purchase_price
        costs: dict[str, float] = {}
        total_extra = Decimal("0")
        for key, _label in COST_FIELDS:
            val = _dec(item.get(key))
            if val:
                costs[key] = _money(val)
            total_extra += val

        total_cost = purchase_value + total_extra
        sale_value = qty * sale_price if sale_price else _dec(item.get("sale_value"))
        gross_profit = sale_value - total_cost if sale_value else Decimal("0")
        profit_per_tonne = (gross_profit / qty) if qty else Decimal("0")
        margin_pct = (gross_profit / sale_value * 100) if sale_value else Decimal("0")
        markup_pct = (gross_profit / total_cost * 100) if total_cost else Decimal("0")
        vat_amount = (sale_value * vat_rate / 100) if vat_rate and sale_value else Decimal("0")

        paid = _dec(item.get("paid_amount"))
        item["totals"] = {
            "purchase_value": _money(purchase_value),
            "costs": costs,
            "total_extra_costs": _money(total_extra),
            "total_cost": _money(total_cost),
            "sale_value": _money(sale_value),
            "gross_profit": _money(gross_profit),
            "profit_per_tonne": _money(profit_per_tonne),
            "margin_pct": _money(margin_pct),
            "markup_pct": _money(markup_pct),
            "vat_amount": _money(vat_amount),
            "payment_balance": _money(sale_value - paid) if sale_value else _money(Decimal("0") - paid),
        }
        # honest FX: never invent a rate
        fx_rate = item.get("fx_rate")
        item["fx_status"] = "manual" if fx_rate not in (None, "") else "not_connected"
        item["fx_note_ru"] = "Курс введён вручную" if item["fx_status"] == "manual" else "Курс не подключён"
        return item

    async def preview_calculation(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "finance") or require(role, "list")
        if denied:
            return denied
        computed = self.compute_calculation(dict(body or {}))
        return {"ok": True, "item": computed}

    # ------------------------------------------------------------------
    # accounting summary
    # ------------------------------------------------------------------

    def finance_summary_data(self, org: str) -> dict[str, Any]:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        today = datetime.now(timezone.utc).date().isoformat()

        def _prod(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
            out: list[dict[str, Any]] = []
            for r in rows:
                if r.get("is_demo"):
                    continue
                blob = f"{r.get('name') or ''} {r.get('title') or ''}"
                if "[DEMO]" in blob or blob.strip().upper().startswith("TEST"):
                    continue
                out.append(r)
            return out

        invoices = _prod(active_only(bag["invoice"]))
        payments = _prod(active_only(bag["payment"]))

        def by_currency(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
            buckets: dict[str, Decimal] = {}
            for r in rows:
                ccy = str(r.get("currency") or "UAH").strip() or "UAH"
                buckets[ccy] = buckets.get(ccy, Decimal("0")) + _dec(r.get("amount"))
            return [{"currency": ccy, "amount": _money(val)} for ccy, val in sorted(buckets.items())]

        def amt(rows: list[dict[str, Any]]) -> float | None:
            buckets = by_currency(rows)
            if len(buckets) > 1:
                return None
            return _money(sum((_dec(r.get("amount")) for r in rows), Decimal("0")))

        receivable_rows = [i for i in invoices if str(i.get("direction") or "in") == "in" and str(i.get("status")) not in {"paid", "cancelled"}]
        payable_rows = [i for i in invoices if str(i.get("direction")) == "out" and str(i.get("status")) not in {"paid", "cancelled"}]
        overdue = [
            i for i in invoices
            if str(i.get("status")) not in {"paid", "cancelled"} and i.get("due_at") and str(i.get("due_at"))[:10] < today
        ]
        rec_ccy = by_currency(receivable_rows)
        pay_ccy = by_currency(payable_rows)
        ov_ccy = by_currency(overdue)
        mixed = len({*(r["currency"] for r in rec_ccy + pay_ccy + ov_ccy)}) > 1
        return {
            "receivables_total": amt(receivable_rows),
            "payables_total": amt(payable_rows),
            "overdue_total": amt(overdue),
            "receivables": receivable_rows,
            "payables": payable_rows,
            "overdue": overdue,
            "payments_actual": amt([p for p in payments if str(p.get("status")) == "paid"]),
            "payments_expected": amt([p for p in payments if str(p.get("status")) in {"planned", "expected"}]),
            "mixed_currencies": mixed,
            "receivables_by_currency": rec_ccy,
            "payables_by_currency": pay_ccy,
            "overdue_by_currency": ov_ccy,
            "by_currency": pay_ccy,
            "fx": {"available": False, "message_ru": "Курс не подключён"},
        }

    async def finance_summary(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "finance") or require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        data = self.finance_summary_data(org)
        return {"ok": True, **data}

    # ------------------------------------------------------------------
    # export
    # ------------------------------------------------------------------

    async def export_accounting_csv(self, organization_id: str, section: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "export")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        fmt = "csv"
        raw_section = (section or "invoices").strip().lower()
        if raw_section.endswith(".xlsx"):
            fmt = "xlsx"
            raw_section = raw_section[:-5]
        if raw_section.endswith(".csv"):
            raw_section = raw_section[:-4]
        aliases = {
            "invoices": "invoices",
            "payments": "payments",
            "calculations": "calculations",
            "pnl": "pnl",
            "p&l": "pnl",
            "receivables": "receivables",
            "payables": "payables",
            "inventory": "inventory",
            "crop-economics": "crop_economics",
            "crop_economics": "crop_economics",
            "field-economics": "field_economics",
            "field_economics": "field_economics",
            "management-report": "management",
            "management": "management",
        }
        kind = aliases.get(raw_section)
        if not kind:
            return {
                "ok": False,
                "error": "validation",
                "message_ru": "Доступен экспорт: invoices, payments, calculations, pnl, receivables, payables, inventory, crop-economics, field-economics",
            }
        buf = io.StringIO()
        writer = csv.writer(buf)

        def write_money_rows(title: str, rows: list[dict[str, Any]]) -> None:
            writer.writerow(["id", "title", "direction", "amount", "currency", "status", "counterparty_id", "deal_id", "contract_id", "due_at", "paid_at"])
            for r in rows:
                writer.writerow([
                    r.get("id"), r.get("title") or r.get("name") or title, r.get("direction"), r.get("amount"), r.get("currency"),
                    r.get("status"), r.get("counterparty_id"), r.get("deal_id"), r.get("contract_id"),
                    r.get("due_at"), r.get("paid_at"),
                ])

        if kind == "management":
            brief = await self.management_brief(org, role)  # type: ignore[attr-defined]
            if not brief.get("ok"):
                return brief
            writer.writerow(["section", "value"])
            for line in str(brief.get("text") or "").splitlines():
                writer.writerow([line])
            filename = "agro_management_brief.csv"
        elif kind == "calculations":
            rows = active_only(bag["calculation"])
            writer.writerow(["id", "title", "quantity", "purchase_price", "total_cost", "sale_value", "gross_profit", "margin_pct", "currency"])
            for r in rows:
                t = r.get("totals") or {}
                writer.writerow([
                    r.get("id"), r.get("title"), r.get("quantity"), r.get("purchase_price"),
                    t.get("total_cost"), t.get("sale_value"), t.get("gross_profit"), t.get("margin_pct"),
                    r.get("currency"),
                ])
            filename = "agro_calculations.csv"
        elif kind == "pnl":
            writer.writerow(["metric", "amount", "currency", "note"])
            fin = self.finance_summary_data(org)
            if fin.get("mixed_currencies"):
                writer.writerow(["mixed_currencies", "", "", "валюты не суммируются"])
                for row in fin.get("receivables_by_currency") or []:
                    writer.writerow(["receivables", row.get("amount"), row.get("currency"), ""])
                for row in fin.get("payables_by_currency") or []:
                    writer.writerow(["payables", row.get("amount"), row.get("currency"), ""])
            else:
                writer.writerow(["receivables_total", fin.get("receivables_total"), "", ""])
                writer.writerow(["payables_total", fin.get("payables_total"), "", ""])
                writer.writerow(["overdue_total", fin.get("overdue_total"), "", ""])
            filename = "agro_pnl.csv"
        elif kind == "receivables":
            write_money_rows("receivable", list(self.finance_summary_data(org).get("receivables") or []))
            filename = "agro_receivables.csv"
        elif kind == "payables":
            write_money_rows("payable", list(self.finance_summary_data(org).get("payables") or []))
            filename = "agro_payables.csv"
        elif kind == "inventory":
            lots = active_only(bag.get("inventory_lot") or [])
            writer.writerow(["id", "warehouse_id", "commodity", "quantity", "unit", "lot_number", "status"])
            for r in lots:
                writer.writerow([r.get("id"), r.get("warehouse_id"), r.get("commodity") or r.get("crop"), r.get("quantity"), r.get("unit"), r.get("lot_number"), r.get("status")])
            filename = "agro_inventory.csv"
        elif kind == "crop_economics":
            writer.writerow(["crop", "area_ha", "harvest_t", "cost", "cost_ha", "cost_t", "currency", "note"])
            try:
                crop = await self.crop_costs(org, role, {"workspace_id": "agro"})  # type: ignore[attr-defined]
            except Exception:
                crop = {}
            items = list((crop or {}).get("items") or [])
            if not items:
                writer.writerow(["", "", "", "", "", "", "", "Нет данных"])
            for r in items:
                writer.writerow([
                    r.get("crop") or r.get("name"), r.get("area") or r.get("area_ha"), r.get("total_yield") or r.get("harvest_t"),
                    r.get("total_cost") or r.get("cost"), r.get("cost_ha"), r.get("cost_t"), r.get("currency") or "UAH", r.get("note") or "",
                ])
            filename = "agro_crop_economics.csv"
        elif kind == "field_economics":
            writer.writerow(["field_id", "name", "area_ha", "crop", "harvest_t", "cost", "cost_ha", "currency", "note"])
            fields = [r for r in active_only(bag.get("agro_field") or []) if str(r.get("workspace_id") or "agro") == "agro"]
            if not fields:
                writer.writerow(["", "", "", "", "", "", "", "", "Нет данных"])
            for r in fields:
                writer.writerow([
                    r.get("id"), r.get("name"), r.get("area_ha") or r.get("ha"), r.get("crop"),
                    r.get("harvest_t") or r.get("tonnes"), r.get("cost"), r.get("cost_ha"), r.get("currency") or "UAH", r.get("note") or "",
                ])
            filename = "agro_field_economics.csv"
        else:
            rows = active_only(bag[{"invoices": "invoice", "payments": "payment"}[kind]])
            write_money_rows(kind, rows)
            filename = f"agro_{kind}.csv"
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org, entity_type="export", entity_id=kind, action="exported",
            summary=f"Экспорт CSV: {kind}", role=role,
            payload={"source": "command_center"},
        )
        content = buf.getvalue()
        if fmt == "xlsx":
            filename = filename.replace(".csv", ".xlsx")
        return {"ok": True, "filename": filename, "content": content, "format": fmt}
