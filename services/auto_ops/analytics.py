"""AUTO 1.5 director analytics mixin — economics, cash flow, completeness.

Org-scoped aggregations over existing Auto ops bags. No invented balances.
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from services.auto_ops.analytics_catalog import (
    ACCOUNT_TYPES,
    COST_BUCKETS,
    ECONOMICS_FILTERS,
    FUNNEL_STAGES,
    LOW_MARGIN_PCT,
    MIN_COMPARE_N,
    PERIODS,
    READINESS_DOCS,
    SALE_STALE_DAYS,
    csv_bytes,
    days_between,
    forecast_profit,
    in_period,
    matches_economics_filter,
    parse_day,
    period_bounds,
    quality_of,
    recommend_price_cut,
    sort_rows,
    status_label,
)
from services.auto_ops.catalog import EXPENSE_LABELS, FINANCE_KPI_GROUPS, STATUS_LABELS
from services.auto_ops.crm_catalog import profit_snapshot
from services.auto_ops.customs_catalog import CUSTOMS_EXPENSE_IDS, SELLING_COST_IDS
from services.auto_ops.documents_catalog import REGISTRATION_PACKAGE_ITEMS, SALE_PACKAGE_ITEMS
from services.auto_ops.logistics_catalog import LOGISTICS_EXPENSE_IDS
from services.auto_ops.rbac import can, normalize_role, require

logger = logging.getLogger(__name__)

ANALYTICS_BAG_KEYS = ("status_history", "finance_accounts")


class AutoOpsAnalyticsMixin:
    """Director analytics on top of vehicles, expenses, CRM, logistics, customs."""

    def _workspace(self, org: str, query: dict[str, str] | None = None) -> str:
        q = query or {}
        return str(q.get("workspace_id") or org)

    def _scoped(self, org: str, items: list[dict[str, Any]], workspace_id: str | None = None) -> list[dict[str, Any]]:
        ws = workspace_id or org
        out = []
        for row in items:
            if str(row.get("organization_id") or org) != org:
                continue
            row_ws = str(row.get("workspace_id") or row.get("organization_id") or org)
            if row_ws not in {org, ws}:
                continue
            out.append(row)
        return out

    def _manager_scope(self, role: str | None, actor_id: str | None, query: dict[str, str] | None) -> str | None:
        if normalize_role(role) != "auto_manager":
            return (query or {}).get("manager") or None
        return actor_id or (query or {}).get("manager") or None

    def _filter_vehicles(self, vehicles: list[dict[str, Any]], manager_id: str | None) -> list[dict[str, Any]]:
        if manager_id in (None, ""):
            return vehicles
        return [v for v in vehicles if str(v.get("assigned_manager_id") or "") == str(manager_id)]

    async def _record_status_history(
        self,
        org: str,
        vehicle_id: str,
        status: str,
        *,
        actor_id: str | None = None,
        source: str = "WEB",
    ) -> None:
        bag = self._bag(org)
        prev = next((h for h in bag["status_history"] if str(h.get("vehicle_id")) == str(vehicle_id) and h.get("left_at") is None), None)
        now = self._now()
        if prev and str(prev.get("status")) == str(status):
            return
        if prev:
            prev["left_at"] = now
            await self._persist_update("status_history", str(prev["id"]), {"left_at": now, "updated_at": now})
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "workspace_id": org,
            "vehicle_id": str(vehicle_id),
            "status": status,
            "entered_at": now,
            "left_at": None,
            "source": source,
            "created_by": actor_id,
            "created_at": now,
            "updated_at": now,
        }
        saved = await self._persist("status_history", item)
        bag["status_history"].insert(0, saved)

    def _history_for(self, org: str, vehicle_id: str) -> list[dict[str, Any]]:
        rows = [h for h in self._bag(org)["status_history"] if str(h.get("vehicle_id")) == str(vehicle_id)]
        rows.sort(key=lambda h: str(h.get("entered_at") or ""))
        return rows

    def _days_at_status(self, org: str, vehicle_id: str, statuses: set[str]) -> int | None:
        total = 0
        known = False
        for h in self._history_for(org, vehicle_id):
            if str(h.get("status")) not in statuses:
                continue
            d = days_between(h.get("entered_at"), h.get("left_at"))
            if d is None:
                continue
            known = True
            total += d
        return total if known else None

    def _cycle_start(self, vehicle: dict[str, Any], history: list[dict[str, Any]]) -> str | None:
        if vehicle.get("purchase_date"):
            return str(vehicle.get("purchase_date"))[:10]
        if history:
            return str(history[0].get("entered_at") or "")[:10] or None
        return str(vehicle.get("created_at") or "")[:10] or None

    def _bucket_costs(self, org: str, vehicle_id: str) -> dict[str, float]:
        out = {k: 0.0 for k in ("purchase", "logistics", "customs", "repair", "other")}
        for exp in self._bag(org)["expenses"]:
            if str(exp.get("vehicle_id")) != str(vehicle_id) or str(exp.get("payment_status")) == "cancelled":
                continue
            if str(exp.get("payment_status") or "").lower() in {"planned", "pending"}:
                continue
            base = self._expense_base(exp)
            cat = str(exp.get("category") or "OTHER")
            placed = False
            for bucket, cats in COST_BUCKETS.items():
                if cat in cats:
                    out[bucket] += base
                    placed = True
                    break
            if not placed:
                out["other"] += base
        return {k: round(v, 2) for k, v in out.items()}

    def _landed_cost(self, org: str, vehicle_id: str) -> dict[str, Any]:
        """Split paid expenses into landed-cost lines without double-counting."""
        lines = {
            "purchase": 0.0,
            "auction_fee": 0.0,
            "logistics": 0.0,
            "customs_duty": 0.0,
            "excise": 0.0,
            "vat": 0.0,
            "broker": 0.0,
            "certification": 0.0,
            "registration": 0.0,
            "other": 0.0,
        }
        selling = 0.0
        for exp in self._bag(org)["expenses"]:
            if str(exp.get("vehicle_id")) != str(vehicle_id) or str(exp.get("payment_status")) == "cancelled":
                continue
            if str(exp.get("payment_status") or "").lower() in {"planned", "pending"}:
                continue
            base = self._expense_base(exp)
            cat = str(exp.get("category") or "OTHER")
            if cat in SELLING_COST_IDS:
                selling += base
                continue
            if cat == "PURCHASE":
                lines["purchase"] += base
            elif cat == "AUCTION_FEE":
                lines["auction_fee"] += base
            elif cat == "DUTY":
                lines["customs_duty"] += base
            elif cat == "EXCISE":
                lines["excise"] += base
            elif cat == "IMPORT_VAT":
                lines["vat"] += base
            elif cat == "BROKER":
                lines["broker"] += base
            elif cat in {"CERTIFICATION", "CERT_LAB"}:
                lines["certification"] += base
            elif cat in {"REGISTRATION", "MREO"}:
                lines["registration"] += base
            elif cat in LOGISTICS_EXPENSE_IDS and cat not in {"BROKER", "OTHER"}:
                lines["logistics"] += base
            else:
                lines["other"] += base
        lines = {k: round(v, 2) for k, v in lines.items()}
        total = round(sum(lines.values()), 2)
        selling = round(selling, 2)
        return {
            "lines": lines,
            "landed_cost": total,
            "selling_costs": selling,
            "invested": round(total + selling, 2),
            "from_records": True,
            "note_ru": "Landed cost по фактическим расходам. Продажные затраты (ремонт/запчасти) отдельно. Двойного учёта нет.",
        }

    def _planned_remaining(self, org: str, vehicle_id: str) -> float:
        total = 0.0
        for exp in self._bag(org)["expenses"]:
            if str(exp.get("vehicle_id")) != str(vehicle_id):
                continue
            if str(exp.get("payment_status") or "").lower() not in {"planned", "pending"}:
                continue
            total += self._expense_base(exp)
        return round(total, 2)

    def _missing_cost_notes(self, org: str, vehicle: dict[str, Any], buckets: dict[str, float]) -> list[str]:
        status = str(vehicle.get("status") or "")
        notes: list[str] = []
        if buckets["purchase"] <= 0 and status not in {"INTEREST", "AUCTION", "CANCELLED"}:
            notes.append("не внесена цена покупки")
        if status in {"SEA_TRANSIT", "DESTINATION_PORT", "CUSTOMS", "PREPARATION", "READY_FOR_SALE", "RESERVED", "SOLD"} and buckets["logistics"] <= 0:
            notes.append("не внесена логистика")
        if status in {"CUSTOMS", "CUSTOMS_CLEARED", "IN_UKRAINE", "PREPARATION", "READY_FOR_SALE", "RESERVED", "SOLD"}:
            if buckets["customs"] <= 0:
                notes.append("не внесена стоимость растаможки")
            has_broker = any(
                str(e.get("vehicle_id")) == str(vehicle.get("id")) and str(e.get("category")) == "BROKER" and str(e.get("payment_status")) != "cancelled"
                for e in self._bag(org)["expenses"]
            )
            if not has_broker:
                notes.append("не внесена стоимость таможенного брокера")
        if status in {"PREPARATION", "READY_FOR_SALE", "RESERVED", "SOLD"} and buckets["repair"] <= 0:
            notes.append("не внесён ремонт")
        return notes

    def _completeness(self, org: str, vehicle: dict[str, Any], buckets: dict[str, float]) -> dict[str, Any]:
        notes = self._missing_cost_notes(org, vehicle, buckets)
        required = 4
        known = required - min(len(notes), required)
        percent = int(round((known / required) * 100)) if required else 0
        quality = quality_of(known=known, required=required)
        final = quality == "KNOWN" and str(vehicle.get("status")) == "SOLD"
        return {
            "financial_completeness_percent": percent,
            "quality": quality,
            "missing": notes,
            "profit_kind_ru": "Финальная прибыль" if final else "Предварительная прибыль",
            "note_ru": ("Себестоимость неполная: " + "; ".join(notes) + ".") if notes else "Себестоимость по внесённым расходам.",
        }

    def _doc_readiness(self, org: str, vehicle_id: str) -> dict[str, Any]:
        present = {str(d.get("document_type")) for d in self._bag(org)["documents"] if str(d.get("vehicle_id")) == str(vehicle_id) and not d.get("archived_at")}
        items = []
        missing = []
        for dtype, label in READINESS_DOCS:
            ok = dtype in present or (dtype == "title" and "title_copy" in present)
            items.append({"document_type": dtype, "label": label, "present": ok})
            if not ok:
                missing.append(dtype)
        return {"items": items, "missing": missing, "complete": not missing, "percent": int(round((len(items) - len(missing)) / len(items) * 100)) if items else 0}

    def _economics_row(self, org: str, vehicle: dict[str, Any], role: str | None) -> dict[str, Any]:
        vid = str(vehicle.get("id"))
        buckets = self._bucket_costs(org, vid)
        invested = round(sum(buckets.values()), 2)
        history = self._history_for(org, vid)
        start = self._cycle_start(vehicle, history)
        sold = str(vehicle.get("status")) == "SOLD"
        sale = self._completed_sale(org, vid) if sold else None
        revenue = None
        if sold:
            revenue = (sale or {}).get("price") or vehicle.get("sale_price_actual")
            try:
                revenue = float(revenue) if revenue not in (None, "") else None
            except (TypeError, ValueError):
                revenue = None
        end = vehicle.get("sale_date") or ((sale or {}).get("completed_at") if sale else None) if sold else None
        days = days_between(start, end)
        complete = self._completeness(org, vehicle, buckets)
        remaining = self._planned_remaining(org, vid)
        expected = vehicle.get("sale_price_expected")
        try:
            expected_f = float(expected) if expected not in (None, "") else None
        except (TypeError, ValueError):
            expected_f = None
        forecast = None if sold else forecast_profit(invested=invested, remaining=remaining, expected_sale=expected_f)
        profit = margin = None
        profit_kind = complete["profit_kind_ru"]
        if sold and revenue is not None:
            snap = profit_snapshot(cost=invested, revenue=revenue)
            profit = snap["profit"]
            margin = snap["margin_pct"]
            if complete["quality"] != "KNOWN":
                profit_kind = "Предварительная прибыль"
        elif sold:
            profit_kind = "Прибыль неизвестна"
        finance_ok = can(role, "finance")
        row = {
            "id": vid,
            "vehicle_id": vid,
            "title": self._vehicle_title(vehicle),
            "vin": vehicle.get("vin"),
            "purchase_date": start,
            "status": vehicle.get("status"),
            "status_ru": STATUS_LABELS.get(str(vehicle.get("status") or ""), str(vehicle.get("status") or "")),
            "days_in_cycle": days,
            "sold": sold,
            "sale_date": str(end)[:10] if end else None,
            "manager": vehicle.get("assigned_manager_id"),
            "is_demo": bool(vehicle.get("is_demo")),
            "quality": complete["quality"],
            "financial_completeness_percent": complete["financial_completeness_percent"],
            "missing": complete["missing"],
            "completeness_note_ru": complete["note_ru"],
            "profit_kind_ru": profit_kind,
            "documents": self._doc_readiness(org, vid),
        }
        if finance_ok:
            landed = self._landed_cost(org, vid)
            row.update(
                {
                    "purchase": buckets["purchase"],
                    "logistics": buckets["logistics"],
                    "customs": buckets["customs"],
                    "repair": buckets["repair"],
                    "cost": invested,
                    "landed_cost": landed["landed_cost"],
                    "landed": landed["lines"],
                    "selling_costs": landed["selling_costs"],
                    "sale_price": revenue if sold else None,
                    "profit": profit if sold else None,
                    "margin_pct": margin if sold else None,
                    "forecast": forecast,
                    "profit_sold_only": sold,
                }
            )
        else:
            row["finance_restricted"] = True
        return row

    def _all_economics(self, org: str, role: str | None, query: dict[str, str] | None, actor_id: str | None) -> list[dict[str, Any]]:
        ws = self._workspace(org, query)
        vehicles = self._filter_vehicles(self._scoped(org, self._bag(org)["vehicles"], ws), self._manager_scope(role, actor_id, query))
        vehicles = [v for v in vehicles if str(v.get("status")) != "CANCELLED"]
        rows = [self._economics_row(org, v, role) for v in vehicles]
        filt = (query or {}).get("filter") or (query or {}).get("tab") or "all"
        rows = [r for r in rows if matches_economics_filter(r, filt)]
        return sort_rows(rows, (query or {}).get("sort") or "days_in_cycle", (query or {}).get("dir") or "desc")

    async def analytics_economics(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        rows = self._all_economics(org, role, query, actor_id)
        return {"ok": True, "items": rows, "total": len(rows), "filters": ECONOMICS_FILTERS, "from_records": True}

    async def analytics_ranking(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "finance")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        rows = self._all_economics(org, role, {"filter": "all", **(query or {})}, actor_id)
        sold = [r for r in rows if r.get("sold") and r.get("profit") is not None]
        strongest = sort_rows(sold, "profit", "desc")[:5]
        weakest = sort_rows(sold, "profit", "asc")[:5]
        unsold = [r for r in rows if not r.get("sold") and (r.get("forecast") or {}).get("forecast_profit") is not None]
        forecast_rank = sort_rows(
            [{**r, "profit": (r.get("forecast") or {}).get("forecast_profit"), "margin_pct": (r.get("forecast") or {}).get("forecast_margin")} for r in unsold],
            "profit",
            "desc",
        )[:5]
        return {
            "ok": True,
            "strongest": strongest,
            "weakest": weakest,
            "unsold_forecast": forecast_rank,
            "note_ru": "Реализованный рейтинг только по проданным. Непроданные — отдельный ПРОГНОЗ.",
        }

    def _period_query(self, query: dict[str, str] | None) -> tuple[Any, Any]:
        q = query or {}
        return period_bounds(q.get("period") or "all", q.get("date_from") or q.get("from"), q.get("date_to") or q.get("to"))

    async def analytics_finance(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "finance")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        start, end = self._period_query(query)
        ws = self._workspace(org, query)
        received = spent = 0.0
        for rec in self._scoped(org, self._bag(org)["receipts"], ws):
            if str(rec.get("status")) != "confirmed":
                continue
            day = rec.get("confirmed_at") or rec.get("created_at")
            if not in_period(day, start, end):
                continue
            received += float(rec.get("amount_base_currency") or rec.get("amount") or 0)
        for exp in self._scoped(org, self._bag(org)["expenses"], ws):
            if str(exp.get("payment_status")) not in {"paid", "confirmed"}:
                continue
            day = exp.get("payment_date") or exp.get("created_at")
            if not in_period(day, start, end):
                continue
            spent += self._expense_base(exp)
        receivables = overdue = 0.0
        today = datetime.now(timezone.utc).date()
        for deal in self._scoped(org, self._bag(org)["deals"], ws):
            roll = self._payment_rollup(org, deal)
            receivables += roll.get("outstanding") or 0
            due = parse_day(deal.get("due_at") or deal.get("payment_due"))
            if (roll.get("outstanding") or 0) > 0 and due and due < today:
                overdue += roll["outstanding"]
        upcoming = 0.0
        for exp in self._scoped(org, self._bag(org)["expenses"], ws):
            if str(exp.get("payment_status") or "").lower() in {"planned", "pending"}:
                upcoming += self._expense_base(exp)
        frozen = realized = forecast_sum = 0.0
        rows = self._all_economics(org, role, query, actor_id)
        for row in rows:
            if row.get("sold"):
                if in_period(row.get("purchase_date"), start, end) or in_period(row.get("sale_date"), start, end) or (start is None):
                    realized += float(row.get("profit") or 0)
            else:
                frozen += float(row.get("cost") or 0)
                fp = (row.get("forecast") or {}).get("forecast_profit")
                if fp is not None:
                    forecast_sum += float(fp)
        return {
            "ok": True,
            "period": (query or {}).get("period") or "all",
            "periods": PERIODS,
            "currency": "USD",
            "from_records": True,
            "cards": {
                "received": round(received, 2),
                "spent": round(spent, 2),
                "receivables": round(receivables, 2),
                "upcoming_expenses": round(upcoming, 2),
                "frozen_capital": round(frozen, 2),
                "realized_profit": round(realized, 2),
                "forecast_profit": round(forecast_sum, 2),
                "overdue_receivables": round(overdue, 2),
            },
            "labels_ru": {
                "received": "Деньги получены",
                "spent": "Деньги потрачены",
                "receivables": "Дебиторка клиентов",
                "upcoming_expenses": "Предстоящие расходы",
                "frozen_capital": "Замороженный капитал",
                "realized_profit": "Реализованная прибыль",
                "forecast_profit": "Прогнозная прибыль",
            },
        }

    def _opening_balance(self, org: str, workspace_id: str) -> float | None:
        accounts = [a for a in self._scoped(org, self._bag(org)["finance_accounts"], workspace_id) if a.get("enabled") is not False]
        if not accounts:
            return None
        known = [a for a in accounts if a.get("balance") not in (None, "")]
        if not known:
            return None
        return round(sum(float(a.get("balance") or 0) for a in known), 2)

    async def analytics_cashflow(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "finance")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        ws = self._workspace(org, query)
        opening = self._opening_balance(org, ws)
        events: list[dict[str, Any]] = []
        for rec in self._scoped(org, self._bag(org)["receipts"], ws):
            status = str(rec.get("status") or "")
            kind = "ACTUAL" if status == "confirmed" else "EXPECTED"
            if status in {"cancelled", "void"}:
                continue
            day = str(rec.get("confirmed_at") or rec.get("due_at") or rec.get("created_at") or "")[:10]
            if not day:
                continue
            amt = float(rec.get("amount_base_currency") or rec.get("amount") or 0)
            events.append({"date": day, "incoming": amt, "outgoing": 0.0, "kind": kind, "source": "receipt", "label_ru": "Оплата клиента"})
        for exp in self._scoped(org, self._bag(org)["expenses"], ws):
            st = str(exp.get("payment_status") or "")
            if st == "cancelled":
                continue
            kind = "ACTUAL" if st in {"paid", "confirmed"} else "EXPECTED"
            day = str(exp.get("payment_date") or exp.get("due_at") or exp.get("created_at") or "")[:10]
            if not day:
                continue
            cat = str(exp.get("category") or "OTHER")
            events.append(
                {
                    "date": day,
                    "incoming": 0.0,
                    "outgoing": self._expense_base(exp),
                    "kind": kind,
                    "source": cat.lower(),
                    "label_ru": EXPENSE_LABELS.get(cat, cat),
                }
            )
        by_day: dict[str, dict[str, float]] = defaultdict(lambda: {"incoming": 0.0, "outgoing": 0.0, "incoming_actual": 0.0, "outgoing_actual": 0.0, "incoming_expected": 0.0, "outgoing_expected": 0.0})
        for ev in events:
            d = ev["date"]
            by_day[d]["incoming"] += ev["incoming"]
            by_day[d]["outgoing"] += ev["outgoing"]
            key_in = "incoming_actual" if ev["kind"] == "ACTUAL" else "incoming_expected"
            key_out = "outgoing_actual" if ev["kind"] == "ACTUAL" else "outgoing_expected"
            by_day[d][key_in] += ev["incoming"]
            by_day[d][key_out] += ev["outgoing"]
        rows = []
        running = opening
        gap = None
        for day in sorted(by_day):
            bucket = by_day[day]
            net = round(bucket["incoming"] - bucket["outgoing"], 2)
            if running is not None:
                running = round(running + net, 2)
            row = {
                "date": day,
                "incoming": round(bucket["incoming"], 2),
                "outgoing": round(bucket["outgoing"], 2),
                "net": net,
                "running_balance": running,
                "incoming_actual": round(bucket["incoming_actual"], 2),
                "outgoing_actual": round(bucket["outgoing_actual"], 2),
                "incoming_expected": round(bucket["incoming_expected"], 2),
                "outgoing_expected": round(bucket["outgoing_expected"], 2),
            }
            rows.append(row)
            if running is not None and running < 0 and gap is None:
                gap = {
                    "date": day,
                    "incoming": row["incoming"],
                    "outgoing": row["outgoing"],
                    "gap": running,
                    "message_ru": f"⚠ Возможный кассовый разрыв {day}: поступления {row['incoming']}, расходы {row['outgoing']}, разрыв {running}.",
                }
        return {
            "ok": True,
            "items": rows,
            "events": events,
            "opening_balance": opening,
            "opening_known": opening is not None,
            "gap": gap,
            "note_ru": None if opening is not None else "Стартовый остаток не задан — бегущий баланс и кассовый разрыв не прогнозируются.",
        }

    async def analytics_receivables(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "finance")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        ws = self._workspace(org, query)
        today = datetime.now(timezone.utc).date()
        rows = []
        total = overdue = d7 = d30 = 0.0
        for deal in self._scoped(org, self._bag(org)["deals"], ws):
            roll = self._payment_rollup(org, deal)
            owed = roll.get("outstanding") or 0
            if owed <= 0:
                continue
            vehicle = self._find(org, "vehicles", str(deal.get("vehicle_id") or "")) if deal.get("vehicle_id") else None
            client = self._find(org, "clients", str(deal.get("client_id") or "")) if deal.get("client_id") else None
            due = parse_day(deal.get("due_at") or deal.get("payment_due"))
            days_over = (today - due).days if due and due < today else 0
            total += owed
            if days_over > 0:
                overdue += owed
            if due and 0 <= (due - today).days <= 7:
                d7 += owed
            if due and 0 <= (due - today).days <= 30:
                d30 += owed
            rows.append(
                {
                    "deal_id": deal.get("id"),
                    "client": (client or {}).get("name"),
                    "client_id": deal.get("client_id"),
                    "vehicle": self._vehicle_title(vehicle) if vehicle else None,
                    "vehicle_id": deal.get("vehicle_id"),
                    "vin": (vehicle or {}).get("vin"),
                    "sale_price": roll.get("sale_price"),
                    "paid": roll.get("paid"),
                    "outstanding": owed,
                    "due_at": str(due) if due else None,
                    "overdue_days": days_over if days_over > 0 else 0,
                    "manager": deal.get("assigned_manager_id"),
                    "currency": roll.get("currency"),
                }
            )
        return {
            "ok": True,
            "items": rows,
            "summary": {
                "total_owed": round(total, 2),
                "overdue": round(overdue, 2),
                "due_7d": round(d7, 2),
                "due_30d": round(d30, 2),
            },
            "from_records": True,
        }

    async def analytics_sales(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "finance")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        rows = [r for r in self._all_economics(org, role, query, actor_id) if r.get("sold") and r.get("profit") is not None]
        n = len(rows)
        revenue = sum(float(r.get("sale_price") or 0) for r in rows)
        profit = sum(float(r.get("profit") or 0) for r in rows)
        margins = [float(r["margin_pct"]) for r in rows if r.get("margin_pct") is not None]
        days = [int(r["days_in_cycle"]) for r in rows if r.get("days_in_cycle") is not None]
        by_month: dict[str, dict[str, float]] = defaultdict(lambda: {"sales": 0, "revenue": 0.0, "profit": 0.0})
        for r in rows:
            month = str(r.get("purchase_date") or r.get("sale_date") or "")[:7] or "unknown"
            by_month[month]["sales"] += 1
            by_month[month]["revenue"] += float(r.get("sale_price") or 0)
            by_month[month]["profit"] += float(r.get("profit") or 0)
        chart = [{"month": m, **{k: (round(v, 2) if isinstance(v, float) else v) for k, v in vals.items()}} for m, vals in sorted(by_month.items())]
        return {
            "ok": True,
            "metrics": {
                "vehicles_sold": n,
                "revenue": round(revenue, 2),
                "profit": round(profit, 2),
                "avg_profit": round(profit / n, 2) if n else None,
                "avg_margin": round(sum(margins) / len(margins), 2) if margins else None,
                "avg_days_to_sale": round(sum(days) / len(days), 1) if days else None,
                "avg_deal_cycle": round(sum(days) / len(days), 1) if days else None,
            },
            "chart": chart,
            "from_records": True,
        }

    async def analytics_managers(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        if normalize_role(role) == "auto_manager":
            org = self._org(organization_id)
            await self.ensure_hydrated(org)
            mid = self._manager_scope(role, actor_id, query) or ""
            base = self._manager_metrics(org, mid or None)
            return {"ok": True, "items": base, "employee_scoring": False, "company_profit_hidden": True, "note_ru": "Менеджер видит только свои операционные счётчики."}
        denied = require(role, "reports")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        finance_ok = can(role, "finance")
        items = []
        for row in self._manager_metrics(org, (query or {}).get("manager")):
            mid = row["manager_id"]
            econ = [r for r in self._all_economics(org, role, {"manager": mid}, actor_id) if r.get("sold")]
            clients = len({str(c.get("id")) for c in self._bag(org)["clients"] if str(c.get("assigned_manager_id") or "") == mid})
            vehicles = sum(1 for v in self._bag(org)["vehicles"] if str(v.get("assigned_manager_id") or "") == mid)
            overdue_tasks = sum(
                1
                for t in self._bag(org)["tasks"]
                if str(t.get("assigned_manager_id") or "") == mid
                and t.get("status") in {"open", "in_progress"}
                and parse_day(t.get("due_at"))
                and parse_day(t.get("due_at")) < datetime.now(timezone.utc).date()
            )
            profits = [float(r["profit"]) for r in econ if r.get("profit") is not None]
            margins = [float(r["margin_pct"]) for r in econ if r.get("margin_pct") is not None]
            days = [int(r["days_in_cycle"]) for r in econ if r.get("days_in_cycle") is not None]
            extra = {
                **row,
                "active_clients": clients,
                "vehicles_assigned": vehicles,
                "overdue_tasks": overdue_tasks,
                "score": None,
                "ranking": None,
            }
            if finance_ok:
                extra.update(
                    {
                        "profit": round(sum(profits), 2) if profits else 0,
                        "avg_margin": round(sum(margins) / len(margins), 2) if margins else None,
                        "avg_days_to_sale": round(sum(days) / len(days), 1) if days else None,
                    }
                )
            items.append(extra)
        return {"ok": True, "items": items, "employee_scoring": False, "note_ru": "Сбалансированные счётчики. Рейтинга по выручке нет."}

    async def analytics_logistics(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        ships = self._scoped(org, self._bag(org)["shipments"], self._workspace(org, query))
        def pair_days(start: Any, end: Any) -> int | None:
            if start in (None, "") or end in (None, ""):
                return None
            return days_between(start, end)

        def avg_days(getter) -> float | None:
            vals = [v for v in (getter(s) for s in ships) if v is not None]
            return round(sum(vals) / len(vals), 1) if len(vals) >= 1 else None

        transit = avg_days(lambda s: pair_days(s.get("departed_at") or s.get("etd") or s.get("atd") or s.get("created_at"), s.get("arrived_at") or s.get("ata") or s.get("current_eta") or s.get("eta")))
        port_days = avg_days(lambda s: pair_days(s.get("arrived_port_at") or s.get("ata"), s.get("atd") or s.get("port_release_at")))
        customs_days = avg_days(lambda s: pair_days(s.get("customs_handoff_date"), s.get("delivery_date_actual")))
        delayed = [s for s in ships if str(s.get("status") or "").upper() in {"DELAYED"} or (s.get("current_eta") and s.get("planned_eta") and str(s.get("current_eta")) > str(s.get("planned_eta")))]
        delay_vals = []
        for s in ships:
            planned, current = s.get("planned_eta"), s.get("current_eta")
            if planned and current:
                d = days_between(planned, current)
                if d is not None:
                    delay_vals.append(d)
        avg_delay = round(sum(delay_vals) / len(delay_vals), 1) if delay_vals else None
        costs = []
        if can(role, "finance"):
            for s in ships:
                snap = self._logistics_costs(org, shipment_id=str(s.get("id")), vehicle_id=str(s.get("vehicle_id") or ""))
                if snap.get("from_records") and (snap.get("actual") or snap.get("planned")):
                    costs.append(float(snap.get("actual") or snap.get("planned") or 0))
        avg_cost = round(sum(costs) / len(costs), 2) if costs else None
        sample_ok = len(ships) >= MIN_COMPARE_N
        return {
            "ok": True,
            "metrics": {
                "avg_transit_days": transit,
                "avg_port_days": port_days,
                "avg_customs_days": customs_days,
                "avg_delivery_cycle": transit,
                "avg_delay_days": avg_delay,
                "avg_logistics_cost": avg_cost,
                "delayed_shipments": len(delayed),
                "sample_size": len(ships),
            },
            "delayed": [{"id": s.get("id"), "vehicle_id": s.get("vehicle_id"), "status": s.get("status")} for s in delayed],
            "sample_ok": sample_ok,
            "note_ru": None if sample_ok else "Недостаточно данных для достоверного сравнения.",
            "from_records": True,
            "finance_restricted": not can(role, "finance"),
        }

    async def analytics_suppliers(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        items = []
        for kind, bag_key, name_field in (
            ("auction", "vehicles", "auction_name"),
            ("carrier", "carriers", "company_name"),
            ("forwarder", "carriers", "company_name"),
            ("broker", "brokers", "company_name"),
        ):
            source = self._bag(org).get(bag_key) or []
            if kind == "auction":
                names = [str(v.get("auction_name") or "") for v in source if v.get("auction_name")]
                for name in sorted(set(names)):
                    jobs = names.count(name)
                    items.append({"kind": kind, "name": name, "jobs": jobs, "avg_cost": None, "avg_delay": None, "rating": None})
                continue
            for row in source:
                items.append({"kind": kind, "name": row.get(name_field), "id": row.get("id"), "jobs": 1, "avg_cost": None, "avg_delay": None, "rating": None})
        return {"ok": True, "items": items, "note_ru": "Рейтинги не выставляются. Только фактические счётчики.", "from_records": True}

    async def analytics_customs(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        cases = self._scoped(org, self._bag(org)["customs_cases"], self._workspace(org, query))
        finance_ok = can(role, "finance")

        def pair_days(start: Any, end: Any) -> int | None:
            if start in (None, "") or end in (None, ""):
                return None
            return days_between(start, end)

        def avg(vals: list[float]) -> float | None:
            return round(sum(vals) / len(vals), 2) if vals else None

        durations: list[float] = []
        duties: list[float] = []
        excises: list[float] = []
        vats: list[float] = []
        totals: list[float] = []
        certs: list[float] = []
        regs: list[float] = []
        landeds: list[float] = []
        delayed_ids: list[str] = []
        blocked_ids: list[str] = []
        pending = missing_docs = 0
        for case in cases:
            vid = str(case.get("vehicle_id") or "")
            d = pair_days(case.get("created_at"), case.get("cleared_at") or case.get("registered_at"))
            if d is not None:
                durations.append(float(d))
            st = str(case.get("status") or "")
            if st in {"DOCUMENTS_PREP", "PAYMENT_PENDING"}:
                pending += 1
            if st == "ON_HOLD":
                delayed_ids.append(vid)
            if st == "REJECTED":
                blocked_ids.append(vid)
            miss = self._doc_readiness(org, vid).get("missing") or []
            if "customs_declaration" in miss:
                missing_docs += 1
            if finance_ok:
                if case.get("duty_uah") not in (None, ""):
                    duties.append(float(case["duty_uah"]))
                if case.get("excise_uah") not in (None, ""):
                    excises.append(float(case["excise_uah"]))
                if case.get("import_vat_uah") not in (None, ""):
                    vats.append(float(case["import_vat_uah"]))
                if case.get("state_total_uah") not in (None, "") or case.get("grand_total_uah") not in (None, ""):
                    totals.append(float(case.get("state_total_uah") if case.get("state_total_uah") not in (None, "") else case.get("grand_total_uah")))
                landed = self._landed_cost(org, vid)
                lines = landed["lines"]
                if lines["certification"]:
                    certs.append(lines["certification"])
                if lines["registration"]:
                    regs.append(lines["registration"])
                if landed["landed_cost"]:
                    landeds.append(landed["landed_cost"])
                if not duties and lines["customs_duty"]:
                    pass
        n = len(cases)
        delayed = len({i for i in delayed_ids if i})
        blocked = len({i for i in blocked_ids if i})
        return {
            "ok": True,
            "metrics": {
                "avg_customs_duration": round(sum(durations) / len(durations), 1) if durations else None,
                "avg_customs_days": round(sum(durations) / len(durations), 1) if durations else None,
                "avg_duty": avg(duties) if finance_ok else None,
                "avg_excise": avg(excises) if finance_ok else None,
                "avg_vat": avg(vats) if finance_ok else None,
                "avg_customs_total": avg(totals) if finance_ok else None,
                "avg_customs_cost": avg(totals) if finance_ok else None,
                "avg_certification_cost": avg(certs) if finance_ok else None,
                "avg_registration_cost": avg(regs) if finance_ok else None,
                "avg_landed_cost": avg(landeds) if finance_ok else None,
                "pending": pending,
                "delayed": delayed,
                "blocked": blocked,
                "vehicles_delayed": delayed,
                "blocked_vehicles": blocked,
                "missing_docs": missing_docs,
                "sample_size": n,
            },
            "delayed": [{"vehicle_id": vid} for vid in delayed_ids if vid],
            "blocked": [{"vehicle_id": vid} for vid in blocked_ids if vid],
            "note_ru": None if n >= MIN_COMPARE_N else "Недостаточно данных для достоверного сравнения.",
            "from_records": True,
        }

    async def analytics_repair(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        items = []
        for v in self._scoped(org, self._bag(org)["vehicles"], self._workspace(org, query)):
            vid = str(v.get("id"))
            planned = actual = 0.0
            for exp in self._bag(org)["expenses"]:
                if str(exp.get("vehicle_id")) != vid or str(exp.get("category")) not in {"REPAIR", "PARTS"}:
                    continue
                if str(exp.get("payment_status")) == "cancelled":
                    continue
                base = self._expense_base(exp)
                if str(exp.get("payment_status") or "").lower() in {"planned", "pending"}:
                    planned += base
                else:
                    actual += base
            if planned == 0 and actual == 0 and str(v.get("status")) not in {"PREPARATION"}:
                continue
            days = self._days_at_status(org, vid, {"PREPARATION"})
            variance = round(actual - planned, 2) if planned else None
            items.append(
                {
                    "vehicle_id": vid,
                    "title": self._vehicle_title(v),
                    "vin": v.get("vin"),
                    "planned_repair": round(planned, 2) if can(role, "finance") else None,
                    "actual_repair": round(actual, 2) if can(role, "finance") else None,
                    "variance": variance if can(role, "finance") else None,
                    "days_in_repair": days,
                    "budget_exceeded": bool(planned and actual > planned),
                }
            )
        return {"ok": True, "items": items, "from_records": True}

    async def analytics_documents(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        attention = []
        sale_ready = 0
        registration_ready = 0
        vehicles = self._filter_vehicles(self._scoped(org, self._bag(org)["vehicles"], self._workspace(org, query)), self._manager_scope(role, actor_id, query))
        for v in vehicles:
            if str(v.get("status")) in {"CANCELLED", "INTEREST"}:
                continue
            ready = self._doc_readiness(org, str(v.get("id")))
            sale = self._eval_package(org, v, SALE_PACKAGE_ITEMS)
            registration = self._eval_package(org, v, REGISTRATION_PACKAGE_ITEMS)
            if sale.get("ready"):
                sale_ready += 1
            if registration.get("ready"):
                registration_ready += 1
            if ready["missing"] or sale.get("missing") or registration.get("missing"):
                attention.append(
                    {
                        "vehicle_id": v.get("id"),
                        "title": self._vehicle_title(v),
                        "vin": v.get("vin"),
                        **ready,
                        "sale_ready": bool(sale.get("ready")),
                        "registration_ready": bool(registration.get("ready")),
                        "sale_missing": sale.get("missing"),
                    }
                )
        return {
            "ok": True,
            "attention_count": len(attention),
            "sale_ready_count": sale_ready,
            "registration_ready_count": registration_ready,
            "items": attention,
            "message_ru": f"Документы требуют внимания: {len(attention)} авто",
        }

    async def analytics_funnel(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        vehicles = self._filter_vehicles(self._scoped(org, self._bag(org)["vehicles"], self._workspace(org, query)), self._manager_scope(role, actor_id, query))
        finance_ok = can(role, "finance")
        stages = []
        for spec in FUNNEL_STAGES:
            wanted = set(spec["statuses"])
            group = [v for v in vehicles if str(v.get("status")) in wanted]
            capital = sum(self._vehicle_invested(org, str(v.get("id"))) for v in group) if finance_ok else None
            days_vals = []
            for v in group:
                d = self._days_at_status(org, str(v.get("id")), wanted)
                if d is not None:
                    days_vals.append(d)
            stages.append(
                {
                    "id": spec["id"],
                    "label_ru": spec["label_ru"],
                    "count": len(group),
                    "capital": round(capital, 2) if capital is not None else None,
                    "avg_days": round(sum(days_vals) / len(days_vals), 1) if days_vals else None,
                    "duration_quality": "KNOWN" if days_vals else "UNKNOWN",
                    "vehicle_ids": [v.get("id") for v in group],
                }
            )
        return {"ok": True, "items": stages, "from_records": True}

    async def analytics_risks(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        econ = self._all_economics(org, role, query, actor_id)
        risks = []
        for row in econ:
            if row.get("sold") and row.get("margin_pct") is not None and float(row["margin_pct"]) < LOW_MARGIN_PCT:
                risks.append({"id": "low_margin", "vehicle_id": row["vehicle_id"], "title": row["title"], "message_ru": f"Маржа {row['margin_pct']}% ниже {LOW_MARGIN_PCT}%"})
            if not row.get("sold") and (row.get("days_in_cycle") or 0) >= SALE_STALE_DAYS and str(row.get("status")) in {"READY_FOR_SALE", "RESERVED"}:
                risks.append({"id": "stale_sale", "vehicle_id": row["vehicle_id"], "title": row["title"], "message_ru": f"Авто в продаже {row['days_in_cycle']} дней"})
        for item in (await self.analytics_repair(organization_id, role, query, actor_id)).get("items") or []:
            if item.get("budget_exceeded"):
                risks.append({"id": "repair_over", "vehicle_id": item["vehicle_id"], "title": item["title"], "message_ru": "Ремонт превысил бюджет"})
        logi = await self.analytics_logistics(organization_id, role, query, actor_id)
        for s in logi.get("delayed") or []:
            risks.append({"id": "eta", "vehicle_id": s.get("vehicle_id"), "shipment_id": s.get("id"), "message_ru": "ETA просрочен / задержка перевозки"})
        recv = await self.analytics_receivables(organization_id, role if can(role, "finance") else "auto_director", query, actor_id) if can(role, "finance") else {"items": []}
        for r in recv.get("items") or []:
            if r.get("overdue_days"):
                risks.append({"id": "overdue_payment", "deal_id": r.get("deal_id"), "vehicle_id": r.get("vehicle_id"), "message_ru": f"Просрочка оплаты {r['overdue_days']} дн. · {r.get('client')}"})
        cf = await self.analytics_cashflow(organization_id, role, query, actor_id) if can(role, "finance") else {}
        if cf.get("gap"):
            risks.append({"id": "cash_gap", "message_ru": cf["gap"]["message_ru"], "date": cf["gap"]["date"]})
        return {"ok": True, "items": risks, "total": len(risks)}

    def director_summary_text(self, org: str, role: str | None, actor_id: str | None = None) -> str:
        econ = self._all_economics(org, role, {}, actor_id)
        cards_total = len(econ)
        invested = sum(float(r.get("cost") or 0) for r in econ)
        frozen = sum(float(r.get("cost") or 0) for r in econ if not r.get("sold"))
        docs = sum(1 for r in econ if (r.get("documents") or {}).get("missing"))
        sold30 = [r for r in econ if r.get("sold") and r.get("margin_pct") is not None and (r.get("days_in_cycle") is None or True)]
        start, end = period_bounds("30d")
        sold30 = [r for r in econ if r.get("sold") and in_period(r.get("purchase_date"), start, end)]
        margins = [float(r["margin_pct"]) for r in sold30 if r.get("margin_pct") is not None]
        avg_m = round(sum(margins) / len(margins), 1) if margins else None
        eta7 = 0
        for v in self._bag(org)["vehicles"]:
            ship = next((s for s in self._bag(org)["shipments"] if str(s.get("vehicle_id")) == str(v.get("id"))), None)
            eta = parse_day((ship or {}).get("eta") or (ship or {}).get("current_eta"))
            if eta and 0 <= (eta - datetime.now(timezone.utc).date()).days <= 7:
                eta7 += 1
        overdue_pay = 0
        if can(role, "finance"):
            today = datetime.now(timezone.utc).date()
            for d in self._bag(org)["deals"]:
                roll = self._payment_rollup(org, d)
                due = parse_day(d.get("due_at") or d.get("payment_due"))
                if (roll.get("outstanding") or 0) > 0 and due and due < today:
                    overdue_pay += 1
        lines = [
            f"{cards_total} автомобиля в системе." if cards_total != 1 else "1 автомобиль в системе.",
            f"${invested:,.0f} капитала вложено.".replace(",", " "),
            f"${frozen:,.0f} остаётся заморожено.".replace(",", " "),
            f"{docs} автомобиля требуют внимания по документам." if docs else "Документы по парку без критичных пробелов.",
            f"{overdue_pay} платежа клиентов просрочены." if overdue_pay else "Просроченных платежей клиентов нет.",
            f"{eta7} автомобиля прибудут в течение 7 дней." if eta7 else "Прибытий в ближайшие 7 дней по ETA нет.",
        ]
        if avg_m is not None:
            lines.append(f"Средняя реализованная маржа за 30 дней — {avg_m}%.")
        else:
            lines.append("Средняя реализованная маржа за 30 дней неизвестна — нет продаж с полной маржой.")
        return " ".join(lines)

    async def analytics_director(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        if normalize_role(role) == "auto_manager":
            org = self._org(organization_id)
            await self.ensure_hydrated(org)
            econ = self._all_economics(org, role, query, actor_id)
            return {
                "ok": True,
                "restricted": True,
                "sprint": "AUTO_1.8.5",
                "summary_ru": f"На сегодня: {len(econ)} автомобилей в вашем операционном контуре. Компания-wide прибыль скрыта.",
                "counts": {"vehicles": len(econ)},
                "from_records": True,
            }
        denied = require(role, "reports") if not can(role, "finance") else None
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        dash = await self.dashboard(org, role)
        funnel = await self.analytics_funnel(org, role, query, actor_id)
        docs = await self.analytics_documents(org, role, query, actor_id)
        risks = await self.analytics_risks(org, role, query, actor_id)
        finance = await self.analytics_finance(org, role, {"period": "30d", **(query or {})}, actor_id) if can(role, "finance") else {"cards": {}}
        return {
            "ok": True,
            "sprint": "AUTO_1.8.5",
            "summary_ru": self.director_summary_text(org, role, actor_id),
            "dashboard": dash if dash.get("ok") else {},
            "funnel": funnel.get("items"),
            "documents_attention": docs.get("attention_count"),
            "document_completeness": docs,
            "sale_readiness": docs.get("sale_ready_count"),
            "registration_readiness": docs.get("registration_ready_count"),
            "vehicles_missing_documents": docs.get("items"),
            "risks": risks.get("items"),
            "finance_30d": finance.get("cards"),
            "from_records": True,
        }

    async def analytics_ai(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "reports")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        director = await self.analytics_director(org, role, query, actor_id)
        ranking = await self.analytics_ranking(org, role, query, actor_id) if can(role, "finance") else {}
        recs = []
        for row in ranking.get("weakest") or []:
            cost = float(row.get("cost") or 0)
            price = float(row.get("sale_price") or 0)
            if cost and price:
                target = round(price * 0.96, 2)
                calc = recommend_price_cut(cost=cost, current_price=price, target_price=target)
                recs.append(
                    {
                        "vehicle_id": row["vehicle_id"],
                        "title": row["title"],
                        "message_ru": (
                            f"{row['title']} VIN {row.get('vin')}. "
                            f"Фактическая себестоимость ${calc['cost']:.0f}. Текущая цена ${calc['current_price']:.0f}. "
                            f"При снижении до ${calc['target_price']:.0f} ориентировочная маржа составит {calc['target_margin_pct']}%."
                        ),
                        "calc": calc,
                    }
                )
        payload = {
            "summary_ru": director.get("summary_ru"),
            "finance_30d": director.get("finance_30d"),
            "risks": director.get("risks"),
            "funnel": director.get("funnel"),
            "recommendations": recs,
        }
        explanation = None
        try:
            from openrouter import ask_openrouter

            prompt = (
                "Объясни риски автобизнеса только по JSON. Не добавляй цифры, которых нет во входных данных.\n"
                + str(payload)
            )
            explanation = await ask_openrouter([{"role": "user", "content": prompt}])
        except Exception as exc:  # noqa: BLE001
            logger.info("auto analytics AI skipped: %s", exc)
        return {"ok": True, "metrics": payload, "explanation_ru": explanation, "recommendations": recs, "ai_optional": True}

    async def list_finance_accounts(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "finance")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        items = list(self._bag(org)["finance_accounts"])
        return {"ok": True, "items": items, "types": ACCOUNT_TYPES, "custody": False, "note_ru": "Только учёт остатков. Crypto custody не строится."}

    async def upsert_finance_account(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "finance_write")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        atype = str(body.get("account_type") or body.get("type") or "OTHER").upper()
        allowed = {a["id"] for a in ACCOUNT_TYPES}
        if atype not in allowed:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип счёта"}
        existing = self._find(org, "finance_accounts", str(body["id"])) if body.get("id") else None
        if existing is None:
            existing = next((a for a in self._bag(org)["finance_accounts"] if str(a.get("account_type")) == atype), None)
        item = existing or {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "workspace_id": org,
            "account_type": atype,
            "created_at": self._now(),
        }
        item.update(
            {
                "account_type": atype,
                "label": body.get("label") or next(a["label_ru"] for a in ACCOUNT_TYPES if a["id"] == atype),
                "currency": body.get("currency") or next(a["currency"] for a in ACCOUNT_TYPES if a["id"] == atype),
                "balance": body.get("balance"),
                "enabled": False if body.get("enabled") is False else True,
                "updated_at": self._now(),
            }
        )
        old_balance = existing.get("balance") if existing else None
        if existing is None:
            saved = await self._persist("finance_account", item)
            self._bag(org)["finance_accounts"].insert(0, saved)
        else:
            saved = item
            await self._persist_update("finance_account", str(item["id"]), item)
        await self._audit(
            organization_id=org,
            action="finance_account_upserted",
            entity_type="finance_account",
            entity_id=str(saved["id"]),
            role=role,
            actor_id=actor_id,
            old_value={"balance": old_balance},
            new_value={"balance": saved.get("balance"), "account_type": atype},
            summary=str(body.get("source") or "WEB"),
        )
        return {"ok": True, "item": saved}

    async def analytics_export(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        if not (can(role, "finance") or can(role, "reports")):
            return require(role, "finance")
        kind = ((query or {}).get("kind") or "economics").strip()
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        if kind == "economics":
            data = await self.analytics_economics(org, role, query, actor_id)
            headers = ["Автомобиль", "VIN", "Дата покупки", "Статус", "Дней", "Покупка", "Логистика", "Таможня", "Ремонт", "Себестоимость", "Цена продажи", "Прибыль", "Маржа", "Менеджер"]
            rows = [
                [r.get("title"), r.get("vin"), r.get("purchase_date"), r.get("status_ru"), r.get("days_in_cycle"), r.get("purchase"), r.get("logistics"), r.get("customs"), r.get("repair"), r.get("cost"), r.get("sale_price"), r.get("profit"), r.get("margin_pct"), r.get("manager")]
                for r in data.get("items") or []
            ]
        elif kind == "receivables":
            data = await self.analytics_receivables(org, role, query, actor_id)
            headers = ["Клиент", "Автомобиль", "VIN", "Цена сделки", "Получено", "Остаток", "Срок", "Просрочка", "Менеджер"]
            rows = [[r.get("client"), r.get("vehicle"), r.get("vin"), r.get("sale_price"), r.get("paid"), r.get("outstanding"), r.get("due_at"), r.get("overdue_days"), r.get("manager")] for r in data.get("items") or []]
        elif kind == "cashflow":
            data = await self.analytics_cashflow(org, role, query, actor_id)
            headers = ["Дата", "Incoming", "Outgoing", "Net", "Running"]
            rows = [[r.get("date"), r.get("incoming"), r.get("outgoing"), r.get("net"), r.get("running_balance")] for r in data.get("items") or []]
        elif kind == "expenses":
            headers = ["id", "vehicle_id", "category", "amount", "currency", "status", "date"]
            rows = [[e.get("id"), e.get("vehicle_id"), e.get("category"), e.get("amount"), e.get("currency"), e.get("payment_status"), e.get("payment_date") or e.get("created_at")] for e in self._bag(org)["expenses"]]
            data = {"ok": True}
        elif kind == "documents":
            return await self.export_documents_csv(org, role, query, actor_id)
        elif kind == "receipts":
            headers = ["id", "deal_id", "amount", "status", "kind"]
            rows = [[r.get("id"), r.get("deal_id"), r.get("amount"), r.get("status"), r.get("kind")] for r in self._bag(org)["receipts"]]
            data = {"ok": True}
        elif kind in {"customs_cases", "customs"}:
            listed = await self.list_customs_cases(org, role, query)
            headers = ["id", "VIN", "Автомобиль", "Статус", "Брокер", "Декларация", "Регистрация", "Номер", "Workspace"]
            rows = [
                [c.get("id"), c.get("vin"), c.get("vehicle_title"), c.get("status_ru"), c.get("broker_name"), c.get("declaration_number"), c.get("reg_status"), c.get("registration_number") or c.get("plate_expected"), c.get("workspace_id")]
                for c in listed.get("items") or []
            ]
            data = listed
        elif kind in {"tax_breakdown", "tax"}:
            listed = await self.list_customs_cases(org, role, query)
            headers = ["VIN", "Декларация", "Мито", "Акциз", "НДС", "Итого", "Валюта"]
            rows = []
            for c in listed.get("items") or []:
                calc = c.get("calculation") or {}
                rows.append([c.get("vin"), c.get("declaration_number"), calc.get("duty_uah"), calc.get("excise_uah"), calc.get("import_vat_uah"), calc.get("grand_total_uah"), calc.get("currency")])
            data = listed
        elif kind in {"customs_payments", "outstanding"}:
            headers = ["id", "VIN", "Дело", "Категория", "Сумма", "Валюта", "Статус", "Дата"]
            rows = []
            for e in self._bag(org)["expenses"]:
                if str(e.get("category") or "") not in CUSTOMS_EXPENSE_IDS:
                    continue
                if kind == "outstanding" and str(e.get("payment_status") or "") in {"paid", "confirmed", "cancelled"}:
                    continue
                veh = self._find(org, "vehicles", str(e.get("vehicle_id") or ""))
                rows.append([e.get("id"), (veh or {}).get("vin"), e.get("customs_id"), e.get("category"), e.get("amount"), e.get("currency"), e.get("payment_status"), e.get("payment_date") or e.get("created_at")])
            data = {"ok": True}
        elif kind in {"readiness", "customs_readiness"}:
            listed = await self.list_customs_cases(org, role, query)
            headers = ["VIN", "Автомобиль", "Статус", "Документов", "Не хватает"]
            rows = []
            for c in listed.get("items") or []:
                chk = c.get("checklist") or {}
                missing = [m.get("label_ru") for m in chk.get("missing") or []]
                rows.append([c.get("vin"), c.get("vehicle_title"), c.get("status_ru"), chk.get("present_count"), "; ".join(str(m) for m in missing)])
            data = listed
        elif kind in {"registration", "customs_registration"}:
            listed = await self.list_customs_cases(org, role, query)
            headers = ["VIN", "Автомобиль", "Рег. статус", "Номер", "Ожидаемый номер", "МРЕО", "Дата"]
            rows = [
                [c.get("vin"), c.get("vehicle_title"), (c.get("registration") or {}).get("status_ru"), c.get("registration_number"), c.get("plate_expected"), c.get("mreo_office"), c.get("mreo_date")]
                for c in listed.get("items") or []
            ]
            data = listed
        else:
            data = await self.analytics_economics(org, role, query, actor_id)
            headers = ["title", "vin", "profit", "margin_pct"]
            rows = [[r.get("title"), r.get("vin"), r.get("profit"), r.get("margin_pct")] for r in data.get("items") or []]
        raw = csv_bytes(headers, rows)
        return {"ok": True, "filename": f"auto-{kind}.csv", "content_type": "text/csv; charset=utf-8", "content": raw, "format": "csv"}

    async def evaluate_analytics_alerts(self, organization_id: str, role: str | None = "auto_director") -> dict[str, Any]:
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        risks = await self.analytics_risks(org, role, {}, None)
        sent = 0
        for risk in risks.get("items") or []:
            await self.notify_telegram_staff(
                org,
                title=str(risk.get("message_ru") or "Риск Авто"),
                entity_type="analytics_risk",
                entity_id=str(risk.get("vehicle_id") or risk.get("deal_id") or risk.get("id") or "risk"),
                vehicle_id=str(risk["vehicle_id"]) if risk.get("vehicle_id") else None,
            )
            sent += 1
        docs = await self.document_alerts(org, role)
        sent += int(docs.get("sent") or 0)
        return {"ok": True, "sent": sent, "total": (risks.get("total") or 0) + len(docs.get("items") or [])}

    async def seed_demo_analytics(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not body.get("confirm_demo"):
            return {"ok": False, "error": "validation", "message_ru": "Для демо аналитики передайте confirm_demo=true."}
        if not can(role, "create"):
            return require(role, "create")
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        created = []
        specs = [
            ("WBAFR9C50DD000001", "PURCHASED", "mgr-a", 18000, None, None),
            ("WBAFR9C50DD000002", "SEA_TRANSIT", "mgr-a", 18500, 1600, None),
            ("WBAFR9C50DD000003", "DESTINATION_PORT", "mgr-b", 19000, 2100, None),
            ("WBAFR9C50DD000004", "CUSTOMS", "mgr-a", 20000, 2200, 4500),
            ("WBAFR9C50DD000005", "PREPARATION", "mgr-b", 17500, 1800, 4200),
            ("WBAFR9C50DD000006", "READY_FOR_SALE", "mgr-a", 21000, 2000, 5000),
            ("WBAFR9C50DD000007", "RESERVED", "mgr-a", 16500, 1500, 3800),
            ("WBAFR9C50DD000008", "SOLD", "mgr-b", 18000, 1700, 4000),
            ("WBAFR9C50DD000009", "SOLD", "mgr-a", 22000, 1900, 4800),
            ("WBAFR9C50DD000010", "SOLD", "mgr-b", 25000, 2400, 5200),
        ]
        acc = "auto_accountant" if can(role, "finance_write") else role
        for i, (vin, status, mgr, purchase, freight, customs) in enumerate(specs, start=1):
            veh = await self.create_vehicle(
                org,
                {
                    "vin": vin,
                    "manufacturer": "BMW",
                    "model": f"DEMO {i}",
                    "year": 2014,
                    "status": "PURCHASED",
                    "purchase_date": f"2026-0{(i % 6) + 1:d}-05",
                    "purchase_price": purchase,
                    "assigned_manager_id": mgr,
                    "sale_price_expected": purchase + 8000 if status != "SOLD" else None,
                    "sale_price_actual": purchase + 9000 if status == "SOLD" else None,
                    "is_demo": True,
                },
                role,
                actor_id,
            )
            if not veh.get("ok"):
                continue
            vid = (veh.get("item") or {}).get("id")
            if not vid:
                continue
            await self.create_expense(org, {"vehicle_id": vid, "category": "PURCHASE", "amount": purchase, "currency": "USD", "payment_status": "paid", "is_demo": True}, acc, actor_id)
            if freight:
                await self.create_expense(org, {"vehicle_id": vid, "category": "SEA_FREIGHT", "amount": freight, "currency": "USD", "payment_status": "paid" if i > 2 else "planned", "is_demo": True}, role, actor_id)
            if customs:
                await self.create_expense(org, {"vehicle_id": vid, "category": "IMPORT_VAT", "amount": customs, "currency": "USD", "payment_status": "paid", "is_demo": True}, acc, actor_id)
            if status != "PURCHASED":
                await self.update_vehicle(org, vid, {"status": status, "is_demo": True}, role, actor_id)
            created.append(vid)
        await self.upsert_finance_account(org, {"account_type": "BANK_USD", "balance": 80000, "label": "DEMO Bank USD"}, "auto_director", actor_id)
        return {"ok": True, "items": created, "is_demo": True, "message_ru": "Создан DEV/DEMO набор аналитики AUTO 1.5. Не смешивается с продакшеном без confirm_demo."}
