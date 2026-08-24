"""AGRO 2.1 — Counterparty 360 / deals / settlements / CRM (real records only).

Extends the existing agro_ops desk. No second CRM, no invented balances.
"""

from __future__ import annotations

import csv
import io
import re
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from services.agro_ops.finance import _dec, _money
from services.agro_ops.rbac import can, normalize_role, require

CRM_VERSION = "AGRO_2_1"

CONTRACT_ALERT_DAYS = (30, 14, 7, 1)

DEAL_WORKFLOW = [
    ("draft", "Новая"),
    ("negotiation", "Переговоры"),
    ("approved", "Согласование"),
    ("awaiting_contract", "Ожидает договор"),
    ("contracted", "Договор подписан"),
    ("awaiting_payment", "Ожидает оплату"),
    ("paid_partly", "Оплачено частично"),
    ("paid", "Оплачено"),
    ("in_delivery", "В поставке"),
    ("delivered", "Получено / передано"),
    ("closed", "Закрыта"),
    ("problem", "Проблема"),
    ("cancelled", "Отменена"),
]

DEAL_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"negotiation", "approved", "cancelled", "problem"},
    "negotiation": {"approved", "draft", "cancelled", "problem"},
    "approved": {"awaiting_contract", "contracted", "negotiation", "cancelled", "problem"},
    "awaiting_contract": {"contracted", "approved", "cancelled", "problem"},
    "contracted": {"awaiting_payment", "paid_partly", "paid", "in_delivery", "cancelled", "problem"},
    "awaiting_payment": {"paid_partly", "paid", "contracted", "cancelled", "problem"},
    "paid_partly": {"paid", "in_delivery", "awaiting_payment", "cancelled", "problem"},
    "paid": {"in_delivery", "delivered", "closed", "problem"},
    "in_delivery": {"delivered", "paid", "problem", "cancelled"},
    "delivered": {"closed", "in_delivery", "problem"},
    "closed": set(),
    "problem": {"negotiation", "approved", "cancelled", "draft"},
    "cancelled": set(),
}

CONTRACT_TYPES = [
    ("framework", "Рамочный договор"),
    ("supply", "Договор поставки"),
    ("sale", "Договор купли-продажи"),
    ("logistics", "Логистический договор"),
    ("storage", "Хранение"),
    ("forwarding", "Экспедирование"),
    ("addendum", "Допсоглашение"),
    ("other", "Другое"),
]

CONTRACT_STATUSES = [
    ("draft", "Черновик"),
    ("review", "На согласовании"),
    ("active", "Действует"),
    ("expiring", "Истекает"),
    ("expired", "Истёк"),
    ("terminated", "Расторгнут"),
]

CHECKLIST_DEFAULT = [
    "contract", "invoice", "specification", "act", "ttn", "quality_certificate", "customs",
]

CHECKLIST_STATUS = ("missing", "requested", "received", "checked", "problem")

PAYMENT_SCHEDULES = {
    "prepay": "100% предоплата",
    "30_70": "30/70",
    "50_50": "50/50",
    "after_delivery": "Оплата после поставки",
    "defer": "Отсрочка N дней",
    "custom": "Произвольный график",
}

COMM_TYPES = [
    ("call", "Звонок"),
    ("email", "Email"),
    ("telegram", "Telegram"),
    ("whatsapp", "WhatsApp"),
    ("viber", "Viber"),
    ("meeting", "Встреча"),
    ("comment", "Комментарий"),
    ("system", "Системное событие"),
]

CONTACT_ROLES = [
    ("director", "Директор"),
    ("accountant", "Бухгалтер"),
    ("manager", "Менеджер"),
    ("logistics", "Логист"),
    ("buyer", "Закупщик"),
    ("agronomist", "Агроном"),
    ("lawyer", "Юрист"),
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _today() -> str:
    return _now().date().isoformat()


def _num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _s(value: Any) -> str:
    return str(value or "").strip()


def _norm_name(value: Any) -> str:
    text = _s(value).lower()
    text = re.sub(r"\b(тов|ооо|зао|чп|фг|пп|тзов|llc|ltd)\b", " ", text)
    text = re.sub(r"[^a-zа-яіїєґ0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _page(rows: list[Any], query: dict[str, str] | None) -> tuple[list[Any], dict[str, int]]:
    q = query or {}
    try:
        limit = max(1, min(100, int(q.get("limit") or 20)))
    except (TypeError, ValueError):
        limit = 20
    try:
        offset = max(0, int(q.get("offset") or 0))
    except (TypeError, ValueError):
        offset = 0
    return rows[offset : offset + limit], {"offset": offset, "limit": limit, "total": len(rows)}


def _ccy_buckets(rows: list[dict[str, Any]], amount_key: str = "amount") -> dict[str, float]:
    buckets: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for row in rows:
        ccy = _s(row.get("currency") or "UAH") or "UAH"
        buckets[ccy] += _dec(row.get(amount_key))
    return {k: _money(v) for k, v in sorted(buckets.items()) if v}


class AgroOpsCrmMixin:
    """Mixed into AgroOpsService."""

    def _crm_actor(self, role: str | None, query: dict[str, str] | None = None) -> str:
        q = query or {}
        return _s(q.get("actor") or q.get("manager") or "")

    def _manager_scope(self, role: str | None) -> bool:
        return normalize_role(role) == "agro_manager"

    def _strip_bank(self, item: dict[str, Any], role: str | None) -> dict[str, Any]:
        if can(role, "finance"):
            return item
        out = dict(item)
        for key in ("iban", "bank", "mfo", "bank_accounts", "bank_name", "account_number"):
            out.pop(key, None)
        return out

    def _deal_amount(self, deal: dict[str, Any]) -> float | None:
        explicit = _num(deal.get("amount") or deal.get("total") or deal.get("sum"))
        if explicit is not None:
            return explicit
        qty = _num(deal.get("quantity"))
        price = _num(deal.get("price"))
        if qty is None or price is None:
            return None
        return round(qty * price, 2)

    def _payments_for_deal(self, bag: dict[str, list], deal_id: str) -> list[dict[str, Any]]:
        from services.agro_ops.service import active_only

        return [
            p for p in active_only(bag.get("payment") or [])
            if str(p.get("deal_id") or "") == str(deal_id)
        ]

    def _paid_of(self, payments: list[dict[str, Any]]) -> float:
        total = Decimal("0")
        for p in payments:
            if str(p.get("status")) in {"paid", "partial", "частично"}:
                total += _dec(p.get("amount"))
        return _money(total)

    def find_duplicates(
        self, org: str, *, name: str = "", edrpou: str = "", phone: str = "", email: str = "", tax_id: str = "", exclude_id: str = ""
    ) -> list[dict[str, Any]]:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        nn = _norm_name(name)
        hits = []
        for row in active_only(bag.get("counterparty") or []):
            if exclude_id and str(row.get("id")) == str(exclude_id):
                continue
            reasons = []
            if edrpou and _s(row.get("edrpou") or row.get("tax_id")).replace(" ", "") == edrpou.replace(" ", ""):
                reasons.append("edrpou")
            if tax_id and _s(row.get("tax_id") or row.get("inn")).replace(" ", "") == tax_id.replace(" ", ""):
                reasons.append("tax_id")
            if phone and _s(row.get("phone")).replace(" ", "")[-10:] and phone.replace(" ", "")[-10:] == _s(row.get("phone")).replace(" ", "")[-10:]:
                reasons.append("phone")
            if email and _s(row.get("email")).lower() == email.lower():
                reasons.append("email")
            if nn and nn == _norm_name(row.get("name") or row.get("legal_name")):
                reasons.append("name")
            if reasons:
                hits.append({"id": row.get("id"), "name": row.get("name"), "reasons": reasons, "edrpou": row.get("edrpou"), "phone": row.get("phone")})
        return hits[:8]

    async def crm_duplicates(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        q = query or {}
        matches = self.find_duplicates(
            org,
            name=q.get("name") or "",
            edrpou=q.get("edrpou") or "",
            phone=q.get("phone") or "",
            email=q.get("email") or "",
            tax_id=q.get("tax_id") or q.get("inn") or "",
            exclude_id=q.get("exclude_id") or "",
        )
        return {
            "ok": True,
            "matches": matches,
            "message_ru": "Возможно, этот контрагент уже существует" if matches else None,
        }

    def _settlement(self, bag: dict[str, list], cp_id: str) -> dict[str, Any]:
        from services.agro_ops.service import active_only

        invoices = [i for i in active_only(bag.get("invoice") or []) if str(i.get("counterparty_id") or "") == str(cp_id)]
        payments = [p for p in active_only(bag.get("payment") or []) if str(p.get("counterparty_id") or "") == str(cp_id)]
        recv = [i for i in invoices if str(i.get("direction") or "in") == "in" and str(i.get("status")) not in {"paid", "cancelled"}]
        pay = [i for i in invoices if str(i.get("direction")) == "out" and str(i.get("status")) not in {"paid", "cancelled"}]
        recv_b = _ccy_buckets(recv)
        pay_b = _ccy_buckets(pay)
        if not recv_b and not pay_b:
            deals = [
                d
                for d in active_only(bag.get("deal") or [])
                if str(d.get("counterparty_id") or "") == str(cp_id) and str(d.get("status")) not in {"cancelled"}
            ]
            recv_acc: dict[str, float] = {}
            pay_acc: dict[str, float] = {}
            for d in deals:
                amt = self._deal_amount(d)
                if amt is None:
                    continue
                paid = self._paid_of(self._payments_for_deal(bag, str(d.get("id"))))
                rem = round(amt - paid, 2)
                if rem <= 0:
                    continue
                ccy = _s(d.get("currency") or "UAH") or "UAH"
                if str(d.get("side") or "buy") == "sell":
                    recv_acc[ccy] = round(recv_acc.get(ccy, 0) + rem, 2)
                else:
                    pay_acc[ccy] = round(pay_acc.get(ccy, 0) + rem, 2)
            recv_b, pay_b = recv_acc, pay_acc
        return {
            "receivable": recv_b,
            "payable": pay_b,
            "payments": _ccy_buckets([p for p in payments if str(p.get("status")) in {"paid", "partial"}]),
        }

    def _aging(self, invoices: list[dict[str, Any]]) -> dict[str, Any]:
        today = _now().date()
        buckets = {"current": 0, "d1_7": 0, "d8_30": 0, "d31_60": 0, "d61_90": 0, "d90p": 0}
        oldest = None
        overdue_n = 0
        for inv in invoices:
            if str(inv.get("status")) in {"paid", "cancelled"}:
                continue
            due = str(inv.get("due_at") or "")[:10]
            if not due:
                buckets["current"] += 1
                continue
            try:
                days = (today - datetime.fromisoformat(due).date()).days
            except ValueError:
                buckets["current"] += 1
                continue
            if days <= 0:
                buckets["current"] += 1
                continue
            overdue_n += 1
            oldest = days if oldest is None else max(oldest, days)
            if days <= 7:
                buckets["d1_7"] += 1
            elif days <= 30:
                buckets["d8_30"] += 1
            elif days <= 60:
                buckets["d31_60"] += 1
            elif days <= 90:
                buckets["d61_90"] += 1
            else:
                buckets["d90p"] += 1
        return {"buckets": buckets, "overdue_count": overdue_n, "oldest_days": oldest}

    def _crop_profile(self, bag: dict[str, list], cp_id: str) -> list[dict[str, Any]]:
        from services.agro_ops.service import active_only

        deals = [d for d in active_only(bag.get("deal") or []) if str(d.get("counterparty_id") or "") == str(cp_id)]
        by_crop: dict[str, dict[str, Any]] = {}
        for d in deals:
            crop = _s(d.get("crop") or d.get("product"))
            if not crop:
                continue
            bucket = by_crop.setdefault(crop, {"crop": crop, "buys": False, "sells": False, "volume": 0.0, "prices": [], "last_deal_at": None, "last_deal_id": None})
            side = str(d.get("side") or "buy")
            if side == "buy":
                bucket["buys"] = True
            else:
                bucket["sells"] = True
            qty = _num(d.get("quantity")) or 0
            bucket["volume"] = round(bucket["volume"] + qty, 4)
            price = _num(d.get("price"))
            if price is not None:
                bucket["prices"].append(price)
            ts = str(d.get("created_at") or "")
            if ts >= str(bucket["last_deal_at"] or ""):
                bucket["last_deal_at"] = ts
                bucket["last_deal_id"] = d.get("id")
        out = []
        for crop, b in sorted(by_crop.items()):
            prices = b.pop("prices")
            direction = "both" if b["buys"] and b["sells"] else ("sells" if b["sells"] else "buys")
            out.append(
                {
                    **b,
                    "direction": direction,
                    "direction_ru": "Оба" if direction == "both" else ("Продаёт" if direction == "sells" else "Покупает"),
                    "avg_price": round(sum(prices) / len(prices), 4) if prices else None,
                    "avg_price_missing": not prices,
                }
            )
        return out

    async def crm_list(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        q = query or {}
        bag = self._bag(org)  # type: ignore[attr-defined]
        rows = active_only(bag.get("counterparty") or [])
        actor = self._crm_actor(role, q)
        if self._manager_scope(role) and actor:
            rows = [r for r in rows if _s(r.get("responsible") or r.get("manager") or r.get("created_by")) in {actor, ""}]
        if q.get("status"):
            rows = [r for r in rows if str(r.get("status")) == q["status"]]
        if q.get("type"):
            rows = [r for r in rows if q["type"] in (r.get("types") or []) or str(r.get("type")) == q["type"]]
        if q.get("region"):
            rows = [r for r in rows if q["region"].lower() in _s(r.get("region") or r.get("city") or r.get("oblast")).lower()]
        if q.get("manager"):
            rows = [r for r in rows if q["manager"].lower() in _s(r.get("responsible") or r.get("manager")).lower()]
        if q.get("tag"):
            rows = [r for r in rows if q["tag"] in (r.get("tags") or [])]
        if q.get("crop"):
            crop = q["crop"].lower()
            deals = active_only(bag.get("deal") or [])
            ids = {str(d.get("counterparty_id")) for d in deals if crop in _s(d.get("crop")).lower()}
            rows = [r for r in rows if str(r.get("id")) in ids]
        if q.get("risk"):
            rows = [r for r in rows if str(r.get("risk_level") or r.get("risk_status") or "").upper() == q["risk"].upper()]
        search = (q.get("q") or "").strip().lower()
        if search:
            rows = [
                r for r in rows
                if search in _s(r.get("name")).lower()
                or search in _s(r.get("edrpou") or r.get("tax_id"))
                or search in _s(r.get("phone"))
                or search in _s(r.get("email")).lower()
            ]
        show_fin = can(role, "finance")
        items = []
        deals_all = active_only(bag.get("deal") or [])
        invoices_all = active_only(bag.get("invoice") or [])
        tasks_all = active_only(bag.get("task") or [])
        comms_all = active_only(bag.get("communication") or [])
        deals_by: dict[str, list] = defaultdict(list)
        inv_by: dict[str, list] = defaultdict(list)
        task_by: dict[str, list] = defaultdict(list)
        comm_by: dict[str, list] = defaultdict(list)
        for d in deals_all:
            deals_by[str(d.get("counterparty_id") or "")].append(d)
        for i in invoices_all:
            inv_by[str(i.get("counterparty_id") or "")].append(i)
        for t in tasks_all:
            task_by[str(t.get("counterparty_id") or "")].append(t)
        for c in comms_all:
            comm_by[str(c.get("counterparty_id") or "")].append(c)
        for r in rows:
            cid = str(r.get("id"))
            deals = [d for d in deals_by.get(cid, []) if str(d.get("status")) not in {"closed", "cancelled"}]
            invoices = inv_by.get(cid, [])
            tasks = [t for t in task_by.get(cid, []) if str(t.get("status")) not in {"done", "cancelled"}]
            comms = comm_by.get(cid, [])
            last_comm = max(comms, key=lambda x: str(x.get("created_at") or ""), default=None)
            next_task = min((t for t in tasks if t.get("due_at")), key=lambda t: str(t.get("due_at")), default=None)
            aging = self._aging(invoices)
            settle = self._settlement(bag, cid) if show_fin else {"receivable": {}, "payable": {}}
            turnover = None
            amounts = [self._deal_amount(d) for d in deals]
            known = [a for a in amounts if a is not None]
            if known and show_fin:
                # do not mix currencies — only same-currency deals contribute if all share one
                ccys = {str(d.get("currency") or "UAH") for d in deals}
                turnover = {"amount": round(sum(known), 2), "currency": next(iter(ccys)) if len(ccys) == 1 else None, "mixed": len(ccys) > 1}
            if q.get("debt") in {"1", "true"} and not (settle["receivable"] or settle["payable"]):
                continue
            if q.get("overdue") in {"1", "true"} and not aging["overdue_count"]:
                continue
            items.append(
                {
                    "id": cid,
                    "name": r.get("name"),
                    "types": r.get("types") or [],
                    "status": r.get("status"),
                    "region": r.get("region") or r.get("oblast") or r.get("city"),
                    "responsible": r.get("responsible") or r.get("manager"),
                    "active_deals": len(deals),
                    "turnover": turnover if show_fin else None,
                    "receivable": settle["receivable"] if show_fin else None,
                    "payable": settle["payable"] if show_fin else None,
                    "last_contact": (last_comm or {}).get("created_at") if last_comm else None,
                    "next_task": (next_task or {}).get("due_at") if next_task else None,
                    "next_task_title": (next_task or {}).get("title") if next_task else None,
                    "risk": r.get("risk_level") or r.get("risk_status"),
                    "overdue": aging["overdue_count"],
                    "oldest_days": aging["oldest_days"],
                    "is_demo": bool(r.get("is_demo")),
                    "phone": r.get("phone"),
                    "city": r.get("city"),
                    "tags": r.get("tags") or [],
                }
            )
        page, meta = _page(items, q)
        return {"ok": True, "items": page, **meta, "can_finance": show_fin}

    async def counterparty_360(self, organization_id: str, item_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        item = next((x for x in bag.get("counterparty") or [] if str(x.get("id")) == str(item_id)), None)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Контрагент не найден"}
        q = query or {}
        tab = q.get("tab") or "overview"
        show_fin = can(role, "finance")
        show_margin = can(role, "margins")
        related = await self.related_bundle(org, "counterparty", item_id, role)  # type: ignore[attr-defined]
        rel = (related.get("related") or {}) if related.get("ok") else {}
        banks = active_only([b for b in bag.get("bank_account") or [] if str(b.get("counterparty_id")) == str(item_id)])
        comms = [c for c in active_only(bag.get("communication") or []) if str(c.get("counterparty_id")) == str(item_id)]
        notes = [n for n in active_only(bag.get("note") or []) if str(n.get("counterparty_id")) == str(item_id)]
        invoices = [i for i in active_only(bag.get("invoice") or []) if str(i.get("counterparty_id")) == str(item_id)]
        header = self._strip_bank(
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "legal_name": item.get("legal_name") or item.get("full_name"),
                "short_name": item.get("short_name"),
                "types": item.get("types") or [],
                "status": item.get("status"),
                "status_reason": item.get("status_reason"),
                "responsible": item.get("responsible") or item.get("manager"),
                "phone": item.get("phone"),
                "email": item.get("email"),
                "city": item.get("city"),
                "region": item.get("region") or item.get("oblast"),
                "country": item.get("country"),
                "address": item.get("address"),
                "legal_address": item.get("legal_address"),
                "actual_address": item.get("actual_address"),
                "edrpou": item.get("edrpou"),
                "tax_id": item.get("tax_id") or item.get("inn"),
                "vat_status": item.get("vat_status"),
                "tags": item.get("tags") or [],
                "risk_level": item.get("risk_level") or item.get("risk_status"),
                "credit_limit": item.get("credit_limit") if show_fin else None,
                "max_defer_days": item.get("max_defer_days") if show_fin else None,
                "iban": item.get("iban") if show_fin else None,
                "bank": item.get("bank") if show_fin else None,
                "mfo": item.get("mfo") if show_fin else None,
                "is_demo": bool(item.get("is_demo")),
            },
            role,
        )
        tab_rows = {
            "contacts": rel.get("contacts") or [],
            "deals": rel.get("deals") or [],
            "contracts": rel.get("contracts") or [],
            "documents": (rel.get("documents") or []) + (rel.get("files") or []),
            "calculations": rel.get("calculations") or [],
            "shipments": rel.get("shipments") or [],
            "tasks": rel.get("tasks") or [],
            "communications": comms,
            "notes": notes + (rel.get("notes") or []),
            "activity": rel.get("activity") or [],
            "payments": rel.get("payments") or rel.get("invoices") or [],
        }
        paged, meta = _page(tab_rows.get(tab) or [], q)
        calc_totals = None
        if show_margin:
            calcs = rel.get("calculations") or []
            if calcs:
                calc_totals = (calcs[0] or {}).get("totals")
        return {
            "ok": True,
            "item": header,
            "bank_accounts": banks if show_fin else [],
            "settlement": self._settlement(bag, item_id) if show_fin else {"receivable": {}, "payable": {}, "masked": True},
            "aging": self._aging(invoices) if show_fin else None,
            "crops": self._crop_profile(bag, item_id),
            "margin": calc_totals,
            "tab": tab,
            "items": paged,
            **meta,
            "can_finance": show_fin,
            "can_margins": show_margin,
            "contract_alerts": self.contract_expiry_events(rel.get("contracts") or []),
        }

    async def deal_360(self, organization_id: str, item_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        item = next((x for x in bag.get("deal") or [] if str(x.get("id")) == str(item_id)), None)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Сделка не найдена"}
        related = await self.related_bundle(org, "deal", item_id, role)  # type: ignore[attr-defined]
        rel = (related.get("related") or {}) if related.get("ok") else {}
        payments = self._payments_for_deal(bag, item_id)
        amount = self._deal_amount(item)
        paid = self._paid_of(payments)
        remaining = round(amount - paid, 2) if amount is not None else None
        pct = round(paid / amount * 100, 2) if amount else None
        show_margin = can(role, "margins")
        calcs = rel.get("calculations") or []
        totals = (calcs[0] or {}).get("totals") if calcs and show_margin else None
        qty = _num(item.get("quantity"))
        price = _num(item.get("price"))
        line = round(qty * price, 2) if qty is not None and price is not None else None
        cost_ok = bool(totals and (totals.get("purchase_value") or totals.get("total_cost")))
        q = query or {}
        tab = q.get("tab") or "overview"
        tab_rows = {
            "payments": payments,
            "documents": (rel.get("documents") or []) + (rel.get("files") or []),
            "shipments": rel.get("shipments") or [],
            "tasks": rel.get("tasks") or [],
            "contracts": rel.get("contracts") or [],
            "activity": rel.get("activity") or [],
            "lots": rel.get("lots") or [],
        }
        paged, meta = _page(tab_rows.get(tab) or [], q)
        allowed = sorted(DEAL_TRANSITIONS.get(str(item.get("status") or "draft"), set()))
        return {
            "ok": True,
            "item": {
                **item,
                "number": item.get("number") or item.get("deal_number") or item.get("id"),
                "amount": amount,
                "line_total": line,
                "paid": paid,
                "remaining": remaining,
                "paid_pct": pct,
                "workflow": dict(DEAL_WORKFLOW).get(str(item.get("status") or "draft"), item.get("status")),
                "allowed_statuses": allowed,
            },
            "calculation": {
                "line_total": line,
                "vat": totals.get("vat_amount") if totals else None,
                "costs": (totals or {}).get("costs") if totals else None,
                "revenue": (totals or {}).get("sale_value") if totals else None,
                "cost_basis": (totals or {}).get("total_cost") if cost_ok else None,
                "gross_profit": (totals or {}).get("gross_profit") if cost_ok and show_margin else None,
                "margin_pct": (totals or {}).get("margin_pct") if cost_ok and show_margin else None,
                "cost_missing": not cost_ok,
                "margin_ru": None if cost_ok and show_margin else ("Себестоимость: нет данных. Маржа: не рассчитана" if show_margin else None),
            },
            "checklist": item.get("checklist") or [],
            "schedule": item.get("payment_schedule") or {},
            "tab": tab,
            "items": paged,
            **meta,
            "can_finance": can(role, "finance"),
            "can_margins": show_margin,
            "credit_warning": None,
        }

    async def set_deal_status(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)["deal"]  # type: ignore[attr-defined]
        cur = next((x for x in bag if str(x.get("id")) == str(item_id)), None)
        if not cur:
            return {"ok": False, "error": "not_found", "message_ru": "Сделка не найдена"}
        nxt = str(body.get("status") or "")
        current = str(cur.get("status") or "draft")
        if nxt == current:
            return {"ok": True, "item": cur}
        allowed = DEAL_TRANSITIONS.get(current, set())
        if nxt not in allowed:
            return {
                "ok": False,
                "error": "validation",
                "message_ru": f"Нельзя перейти из «{dict(DEAL_WORKFLOW).get(current, current)}» в «{dict(DEAL_WORKFLOW).get(nxt, nxt)}»",
                "allowed": sorted(allowed),
            }
        if nxt == "approved":
            denied = require(role, "approve")
            if denied:
                return denied
        comment = _s(body.get("comment") or body.get("reason"))
        result = await self.update_entity(org, "deal", item_id, {"status": nxt, "status_comment": comment}, role)  # type: ignore[attr-defined]
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="deal",
            entity_id=item_id,
            action="status_changed",
            summary=f"Статус: {current} → {nxt}",
            role=role,
            actor_id=body.get("actor_id"),
            payload={"from": current, "to": nxt, "comment": comment, "source": body.get("source") or "USER"},
        )
        return result

    def normalize_deal_crm(self, item: dict[str, Any], org: str, role: str | None) -> dict[str, Any]:
        qty = _num(item.get("quantity"))
        price = _num(item.get("price"))
        if qty is not None and price is not None and item.get("amount") in (None, ""):
            item["amount"] = round(qty * price, 2)
        if not item.get("checklist"):
            item["checklist"] = [{"doc_type": t, "status": "missing", "file_id": None} for t in CHECKLIST_DEFAULT]
        if item.get("payment_terms") or item.get("schedule_kind"):
            item["payment_schedule"] = self._build_schedule(item)
        warning = None
        if str(item.get("side") or "buy") == "sell" and item.get("counterparty_id"):
            warning = self._credit_warning(org, str(item.get("counterparty_id")), role)
        return {"warning": warning}

    def _credit_warning(self, org: str, cp_id: str, role: str | None) -> dict[str, Any] | None:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        cp = next((c for c in active_only(bag.get("counterparty") or []) if str(c.get("id")) == cp_id), None)
        if not cp:
            return None
        limit = _num(cp.get("credit_limit"))
        if limit is None:
            return None
        settle = self._settlement(bag, cp_id)
        # outstanding in same currency as limit if possible
        recv = settle.get("receivable") or {}
        outstanding = sum(recv.values()) if recv else 0
        if outstanding > limit:
            return {
                "code": "LIMIT_EXCEEDED",
                "message_ru": f"Превышен кредитный лимит ({outstanding} > {limit}). Сделка не блокируется.",
            }
        if str(cp.get("risk_level") or "").upper() == "BLOCKED":
            return {"code": "RISK_BLOCKED", "message_ru": "Контрагент с уровнем риска BLOCKED. Требуется внимание, сделка не блокируется автоматически."}
        return None

    def _build_schedule(self, item: dict[str, Any]) -> dict[str, Any]:
        kind = str(item.get("schedule_kind") or item.get("payment_terms") or "custom")
        amount = _num(item.get("amount"))
        planned = str(item.get("planned_at") or item.get("due_at") or _today())[:10]
        milestones = []
        if amount is None:
            return {"kind": kind, "label_ru": PAYMENT_SCHEDULES.get(kind, kind), "milestones": []}
        if kind in {"prepay", "100"}:
            milestones = [{"pct": 100, "amount": amount, "due_at": planned, "status": "planned"}]
        elif kind in {"30_70", "30/70"}:
            milestones = [
                {"pct": 30, "amount": round(amount * 0.3, 2), "due_at": planned, "status": "planned"},
                {"pct": 70, "amount": round(amount * 0.7, 2), "due_at": planned, "status": "planned"},
            ]
        elif kind in {"50_50", "50/50"}:
            milestones = [
                {"pct": 50, "amount": round(amount * 0.5, 2), "due_at": planned, "status": "planned"},
                {"pct": 50, "amount": round(amount * 0.5, 2), "due_at": planned, "status": "planned"},
            ]
        elif kind == "after_delivery":
            milestones = [{"pct": 100, "amount": amount, "due_at": None, "status": "planned", "note_ru": "После поставки"}]
        elif kind == "defer":
            days = int(item.get("defer_days") or item.get("payment_defer_days") or 0)
            due = (datetime.fromisoformat(planned) + timedelta(days=days)).date().isoformat() if planned else None
            milestones = [{"pct": 100, "amount": amount, "due_at": due, "status": "planned"}]
        else:
            milestones = list(item.get("milestones") or [])
        return {"kind": kind, "label_ru": PAYMENT_SCHEDULES.get(kind, "Произвольный график"), "milestones": milestones}

    async def add_communication(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create") or require(role, "tasks")
        if denied and not can(role, "create"):
            denied = require(role, "tasks")
            if denied:
                return denied
        payload = {
            "title": body.get("title") or body.get("summary") or dict(COMM_TYPES).get(str(body.get("comm_type") or "comment"), "Комментарий"),
            "comm_type": body.get("comm_type") or "comment",
            "channel": body.get("channel") or body.get("comm_type") or "comment",
            "source": body.get("source") or "USER",
            "counterparty_id": body.get("counterparty_id"),
            "deal_id": body.get("deal_id"),
            "text": body.get("text") or body.get("comment"),
            "happened_at": body.get("happened_at") or datetime.now(timezone.utc).isoformat(),
        }
        if payload["source"] not in {"USER", "SYSTEM", "API", "IMPORT", "TELEGRAM"}:
            payload["source"] = "USER"
        if payload["comm_type"] in {"telegram", "whatsapp", "email"} and payload["source"] == "USER" and not payload.get("text"):
            return {"ok": False, "error": "validation", "message_ru": "Интеграция не подключена. Можно сохранить только ручную запись."}
        return await self.create_entity(organization_id, "communication", payload, role)  # type: ignore[attr-defined]

    async def add_note(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            denied = require(role, "tasks")
            if denied:
                return denied
        payload = {
            "title": body.get("title") or (str(body.get("text") or "")[:80] or "Заметка"),
            "text": body.get("text") or body.get("comment"),
            "counterparty_id": body.get("counterparty_id"),
            "deal_id": body.get("deal_id"),
        }
        return await self.create_entity(organization_id, "note", payload, role)  # type: ignore[attr-defined]

    async def create_follow_up(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "tasks")
        if denied:
            return denied
        title = _s(body.get("title") or "Follow-up")
        task = await self.create_entity(  # type: ignore[attr-defined]
            organization_id,
            "task",
            {
                "title": title,
                "due_at": body.get("due_at"),
                "counterparty_id": body.get("counterparty_id"),
                "deal_id": body.get("deal_id"),
                "owner": body.get("owner"),
                "kind": "follow_up",
            },
            role,
        )
        return task

    async def crm_analytics(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "analytics")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        cps = active_only(bag.get("counterparty") or [])
        deals = active_only(bag.get("deal") or [])
        if self._manager_scope(role) and not can(role, "margins"):
            actor = self._crm_actor(role, None)
            if actor:
                cps = [c for c in cps if _s(c.get("responsible") or c.get("manager") or c.get("created_by")) in {actor, ""}]
                deals = [d for d in deals if _s(d.get("responsible") or d.get("manager") or d.get("created_by")) in {actor, ""}]
        cut = (_now() - timedelta(days=30)).isoformat()
        show_fin = can(role, "finance")
        show_margin = can(role, "margins")
        by_ccy_sale: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        by_ccy_buy: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for d in deals:
            amt = self._deal_amount(d)
            if amt is None:
                continue
            ccy = _s(d.get("currency") or "UAH") or "UAH"
            if str(d.get("side")) == "sell":
                by_ccy_sale[ccy] += _dec(amt)
            else:
                by_ccy_buy[ccy] += _dec(amt)
        invoices = active_only(bag.get("invoice") or [])
        aging = self._aging(invoices)
        top = []
        if show_fin:
            vol: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
            names = {str(c.get("id")): c.get("name") for c in cps}
            for d in deals:
                amt = self._deal_amount(d)
                if amt is None:
                    continue
                vol[str(d.get("counterparty_id") or "")] += _dec(amt)
            top = [{"id": k, "name": names.get(k), "turnover": _money(v)} for k, v in sorted(vol.items(), key=lambda kv: kv[1], reverse=True)[:8] if k]
        return {
            "ok": True,
            "active_counterparties": len(cps),
            "new_30d": len([c for c in cps if str(c.get("created_at") or "") >= cut]),
            "active_deals": len([d for d in deals if str(d.get("status")) not in {"closed", "cancelled"}]),
            "sales": {k: _money(v) for k, v in by_ccy_sale.items()} if show_fin else None,
            "purchases": {k: _money(v) for k, v in by_ccy_buy.items()} if show_fin else None,
            "aging": aging if show_fin else None,
            "top_counterparties": top,
            "margin": None if not show_margin else "Нет данных",
        }

    async def import_counterparties(self, organization_id: str, body: dict[str, Any], role: str | None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        raw = body.get("csv") or body.get("text") or ""
        mapping = body.get("mapping") or {}
        preview = bool(body.get("preview"))
        commit = bool(body.get("commit")) and not preview
        parsed_rows = body.get("rows")
        if parsed_rows:
            # client-parsed XLSX/CSV rows — still preview-before-commit
            reader = [{str(k): v for k, v in (row or {}).items()} for row in parsed_rows if isinstance(row, dict)]
        else:
            if not raw:
                return {"ok": False, "error": "validation", "message_ru": "Нет CSV для импорта"}
            reader = list(csv.DictReader(io.StringIO(str(raw))))
        created = updated = skipped = 0
        errors = []
        preview_rows = []
        for i, row in enumerate(reader, 1):
            def col(key: str, default: str = "") -> str:
                src = mapping.get(key) or key
                return _s(row.get(src) or row.get(default) or row.get(key))

            name = col("name", "название")
            if not name:
                errors.append({"row": i, "error": "no_name", "message_ru": "Нет названия"})
                skipped += 1
                continue
            payload = {
                "name": name,
                "edrpou": col("edrpou") or col("ЕДРПОУ"),
                "phone": col("phone") or col("телефон"),
                "email": col("email"),
                "city": col("city") or col("город"),
                "region": col("region") or col("область"),
                "types": [t.strip() for t in (col("types") or "counterparty").split(",") if t.strip()],
            }
            dups = self.find_duplicates(org, name=payload["name"], edrpou=payload["edrpou"], phone=payload["phone"], email=payload["email"])
            preview_rows.append({**payload, "duplicates": dups, "row": i})
            if preview or not commit:
                continue
            if dups:
                skipped += 1
                errors.append({"row": i, "error": "duplicate", "message_ru": "Возможно, этот контрагент уже существует", "matches": dups})
                continue
            res = await self.create_entity(org, "counterparty", payload, role)  # type: ignore[attr-defined]
            if res.get("ok"):
                created += 1
            else:
                skipped += 1
                errors.append({"row": i, "error": res.get("error"), "message_ru": res.get("message_ru")})
        return {
            "ok": True,
            "preview": preview or not commit,
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "rows": preview_rows[:50],
        }

    async def export_crm(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "export")
        if denied:
            return denied
        listed = await self.crm_list(organization_id, role, {**(query or {}), "limit": "10000", "offset": "0"})
        if not listed.get("ok"):
            return listed
        show_fin = can(role, "finance")
        buf = io.StringIO()
        fields = ["name", "types", "status", "region", "responsible", "active_deals", "phone"]
        if show_fin:
            fields += ["receivable", "payable"]
        writer = csv.DictWriter(buf, fieldnames=fields)
        writer.writeheader()
        for row in listed.get("items") or []:
            writer.writerow({k: row.get(k) if k not in {"types", "receivable", "payable"} else str(row.get(k) or "") for k in fields})
        return {"ok": True, "csv": buf.getvalue(), "filename": "agro_crm.csv"}

    def contract_expiry_events(self, contracts: list[dict[str, Any]], days: tuple[int, ...] = CONTRACT_ALERT_DAYS) -> list[dict[str, Any]]:
        today = _now().date()
        events = []
        horizon = max(days)
        for c in contracts:
            end = str(c.get("ends_at") or c.get("expiry_at") or c.get("valid_until") or c.get("due_at") or "")[:10]
            if not end or str(c.get("status")) in {"expired", "terminated", "cancelled"}:
                continue
            try:
                left = (datetime.fromisoformat(end).date() - today).days
            except ValueError:
                continue
            if left < 0 or left > horizon:
                continue
            bucket = min((d for d in days if left <= d), default=None)
            if bucket is None:
                continue
            events.append({"id": c.get("id"), "title": c.get("title"), "ends_at": end, "days_left": left, "bucket": bucket})
        return events
