"""AGRO 2.0 Operational Command Center — aggregated dashboard (real data only).

Extends GET /api/agro-ops/v1/dashboard. Does not fetch live weather or generate
intel reports. Missing values stay «Нет данных» — never invented.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from services.agro_ops.rbac import can, normalize_role, require

COMMAND_CENTER_VERSION = "AGRO_2_0"

SEVERITY_RU = {
    "CRITICAL": "Критично",
    "HIGH": "Важно",
    "MEDIUM": "Средне",
    "INFO": "Информация",
}

DEAL_PIPELINE = [
    ("new", "Новая", {"draft"}),
    ("negotiation", "Переговоры", {"negotiation"}),
    ("approval", "Согласование", {"approved"}),
    ("contract", "Договор", {"contracted"}),
    ("payment", "Оплата", {"paid_partly", "paid"}),
    ("delivery", "Поставка", {"in_delivery", "delivered"}),
    ("closed", "Закрыта", {"closed"}),
    ("problem", "Проблема", {"cancelled", "risk", "problem", "blocked"}),
]

SHIPMENT_STAGES = [
    ("preparing", "Готовится", {"planned", "draft", "preparing"}),
    ("loaded", "Загружено", {"loading", "loaded", "assigned"}),
    ("in_transit", "В пути", {"in_transit"}),
    ("port", "Порт", {"port", "at_port"}),
    ("customs", "Таможня", {"customs"}),
    ("delivered", "Доставлено", {"delivered", "completed", "unloading"}),
    ("delayed", "Задержано", {"delayed", "overdue", "risk"}),
]

PRICE_KIND_RU = {
    "AUTOMATIC": "Рыночная",
    "MARKET_PROVIDER": "Рыночная",
    "COUNTERPARTY": "Контрагент",
    "CONTRACT": "Контрагент",
    "OURS": "Наша цена",
    "INTERNAL": "Наша цена",
    "MANUAL": "Ручная",
}

INTEL_CARDS = [
    ("ukraine", "Украина"),
    ("world", "Мировые рынки"),
    ("trade", "Экспорт / импорт"),
    ("harvest", "Урожай"),
    ("logistics", "Логистика"),
    ("risks", "Риски"),
    ("opportunities", "Возможности"),
]

SEARCH_SPEC: list[tuple[str, str, tuple[str, ...]]] = [
    ("counterparty", "Контрагенты", ("name", "title", "edrpou", "tax_id", "inn", "egrpou", "phone", "email", "city")),
    ("deal", "Сделки", ("title", "name", "number", "deal_number", "crop", "product", "operation_number")),
    ("contract", "Договоры", ("title", "name", "number", "contract_number", "operation_number")),
    ("document", "Документы", ("title", "filename", "number", "doc_number")),
    ("shipment", "Поставки", ("title", "name", "number", "shipment_number", "crop", "operation_number")),
    ("warehouse", "Склады", ("name", "title", "city", "location", "address")),
    ("crop", "Культуры", ("name", "title", "commodity")),
    ("task", "Задачи", ("title", "name")),
    ("payment", "Платежи", ("title", "name", "number", "invoice_number")),
    ("vehicle", "Транспорт", ("name", "title", "plate", "vin")),
    ("file", "Файлы", ("filename", "title", "number")),
    ("agro_operation", "Операции", ("number", "title", "crop", "commodity")),
    ("truck_run", "Рейсы", ("plate", "title", "driver_name", "trailer_plate", "operation_number")),
    ("agro_field", "Поля", ("name", "title", "number", "cadastre", "region")),
    ("crop_season", "Сезоны", ("crop", "title", "year")),
    ("field_work", "Работы", ("title", "work_type", "status")),
    ("machine", "Машины", ("name", "title", "plate", "model", "operator")),
    ("material", "Материалы", ("name", "title", "batch", "category")),
    ("inventory_lot", "Складская партия", ("lot_number", "commodity", "crop", "operation_number")),
    ("driver", "Водители", ("full_name", "name", "phone", "title")),
]

ROLE_BLOCK_ORDER = {
    "agro_director": ["summary", "today", "deals", "shipments", "warehouses", "markets", "weather", "intel", "tasks"],
    "platform_owner": ["summary", "today", "deals", "shipments", "warehouses", "markets", "weather", "intel", "tasks"],
    "agro_accountant": ["summary", "today", "tasks", "deals", "shipments", "warehouses"],
    "agro_manager": ["summary", "today", "deals", "tasks", "shipments", "markets", "weather", "intel"],
    "agro_logistics": ["summary", "today", "shipments", "warehouses", "tasks", "deals"],
    "agro_warehouse": ["summary", "today", "warehouses", "shipments", "tasks"],
    "agro_quality": ["summary", "today", "warehouses", "shipments", "tasks"],
    "agro_agronomist": ["summary", "today", "weather", "tasks"],
    "agro_mechanic": ["summary", "today", "tasks"],
    "agro_observer": ["summary", "today", "deals", "shipments", "warehouses", "weather", "intel", "tasks"],
    "agro_viewer": ["summary", "today", "deals", "shipments", "warehouses", "weather", "intel", "tasks"],
}


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


def _pipeline_id(status: str) -> str:
    st = (status or "").lower()
    for pid, _label, members in DEAL_PIPELINE:
        if st in members:
            return pid
    return "new"


def _ship_stage(status: str, delayed: bool) -> str:
    if delayed:
        return "delayed"
    st = (status or "").lower()
    for sid, _label, members in SHIPMENT_STAGES:
        if st in members:
            return sid
    return "preparing"


def _price_kind(source_type: str) -> str:
    key = (source_type or "MANUAL").upper()
    return PRICE_KIND_RU.get(key, "Ручная")


def _days_left(raw: Any) -> int | None:
    text = str(raw or "")[:10]
    if not text or text in {"None", "—"}:
        return None
    try:
        due = datetime.fromisoformat(text).date()
    except ValueError:
        return None
    return (due - _now().date()).days


def _cp_name(bag: dict[str, list], cp_id: Any) -> str | None:
    if not cp_id:
        return None
    row = next((c for c in bag.get("counterparty") or [] if str(c.get("id")) == str(cp_id)), None)
    if not row:
        return None
    name = _s(row.get("name") or row.get("title"))
    return name or None


def _live(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Production analytics never silently include DEMO/TEST rows."""
    out = []
    for r in rows:
        if r.get("is_demo"):
            continue
        blob = f"{r.get('name') or ''} {r.get('title') or ''}"
        if "[DEMO]" in blob or blob.strip().upper().startswith("TEST"):
            continue
        out.append(r)
    return out


class AgroOpsCommandCenterMixin:
    """Mixed into AgroOpsService. Uses already-hydrated bags — no live provider calls."""

    def build_command_center(self, org: str, role: str | None) -> dict[str, Any]:
        from services.agro_ops.service import active_only
        from services.agro_ops.warehouses import _dec, _money

        bag = self._bag(org)  # type: ignore[attr-defined]
        role_id = normalize_role(role)
        show_finance = can(role, "finance")
        show_margins = can(role, "margins")
        show_intel = can(role, "intel") or role_id in {"agro_observer", "agro_viewer", "agro_manager"}
        today = _today()
        week_end = (_now().date() + timedelta(days=7)).isoformat()

        cps = _live(active_only(bag.get("counterparty") or []))
        deals = _live(active_only(bag.get("deal") or []))
        contracts = _live(active_only(bag.get("contract") or []))
        documents = _live(active_only(bag.get("document") or []))
        files = _live(active_only(bag.get("file") or []))
        invoices = _live(active_only(bag.get("invoice") or []))
        payments = _live(active_only(bag.get("payment") or []))
        shipments = _live(active_only(bag.get("shipment") or []))
        warehouses = _live(active_only(bag.get("warehouse") or []))
        lots = _live(active_only(bag.get("inventory_lot") or []))
        ops = _live(active_only(bag.get("warehouse_operation") or []))
        tasks = _live(active_only(bag.get("task") or []))
        calendar = _live(active_only(bag.get("calendar") or []))
        prices = _live(active_only(bag.get("market_price") or []))
        alerts = _live(active_only(bag.get("alert") or []))
        notifications = _live(active_only(bag.get("notification") or []))
        trips = _live(active_only(bag.get("trip") or []))
        reports = [r for r in _live(active_only(bag.get("report") or [])) if r.get("record_type") == "report"]

        fin = self.finance_summary_data(org)  # type: ignore[attr-defined]
        overdue_invoices = list(fin.get("overdue") or [])
        payable_rows = list(fin.get("payables") or [])

        active_deals = [d for d in deals if str(d.get("status")) not in {"closed", "cancelled"}]
        action_deals = [
            d for d in active_deals
            if str(d.get("status")) in {"draft", "negotiation", "approved", "paid_partly", "cancelled", "risk"}
        ]

        delayed_shipments: list[dict[str, Any]] = []
        in_transit: list[dict[str, Any]] = []
        for s in shipments:
            status = str(s.get("status") or "planned")
            deadline = s.get("deadline_at") or s.get("eta") or s.get("arrival_planned") or s.get("due_at")
            late = bool(deadline and str(deadline)[:10] < today and status not in {"delivered", "completed", "cancelled"})
            if late or status in {"delayed", "overdue", "risk"}:
                delayed_shipments.append(s)
            if status in {"planned", "in_transit", "loading", "loaded", "assigned", "port", "customs"}:
                in_transit.append(s)

        occupied = sum((_dec(lot.get("quantity")) for lot in lots), _dec(0))
        crop_names = sorted({_s(l.get("commodity") or l.get("crop")) for l in lots if _s(l.get("commodity") or l.get("crop"))})
        overdue_tasks = [
            t for t in tasks
            if t.get("due_at") and str(t.get("due_at"))[:10] < today and str(t.get("status")) not in {"done", "cancelled"}
        ]
        tasks_today = [
            t for t in tasks
            if str(t.get("due_at") or "")[:10] == today and str(t.get("status")) not in {"done", "cancelled"}
        ]
        tasks_week = [
            t for t in tasks
            if today <= str(t.get("due_at") or "")[:10] <= week_end and str(t.get("status")) not in {"done", "cancelled"}
        ]
        meetings = [
            e for e in calendar
            if today <= str(e.get("starts_at") or "")[:10] <= week_end
        ]

        today_events = self._cc_today_events(
            org,
            today=today,
            deals=deals,
            contracts=contracts,
            documents=documents,
            files=files,
            invoices=overdue_invoices,
            shipments=shipments,
            delayed=delayed_shipments,
            lots=lots,
            warehouses=warehouses,
            tasks=overdue_tasks,
            prices=prices,
            alerts=alerts,
            bag=bag,
        )
        critical_n = len([e for e in today_events if e.get("severity") == "CRITICAL"])

        pay_amount = fin.get("payables_total") if show_finance else None
        overdue_amount = fin.get("overdue_total") if show_finance else None

        summary = [
            {
                "id": "deals",
                "label_ru": "Активные сделки",
                "value": len(active_deals),
                "unit": None,
                "hint_ru": f"{len(action_deals)} требуют действия" if action_deals else ("Нет данных" if not deals else "Без срочных действий"),
                "view": "deals",
                "empty": not deals,
            },
            {
                "id": "shipments",
                "label_ru": "Поставки в пути",
                "value": len(in_transit),
                "unit": None,
                "hint_ru": f"{len(delayed_shipments)} задерживаются" if delayed_shipments else ("Нет активных перевозок" if not in_transit else "Без задержек"),
                "view": "logistics",
                "filter": "IN_TRANSIT",
                "empty": not in_transit,
            },
            {
                "id": "stock",
                "label_ru": "Склад, тонн",
                "value": _money(occupied) if lots else 0,
                "unit": "т",
                "hint_ru": f"{len(crop_names)} культур" if crop_names else ("Нет данных" if not warehouses else "Нет остатков"),
                "view": "warehouses",
                "empty": not lots,
            },
            {
                "id": "payables",
                "label_ru": "К оплате",
                "value": pay_amount if pay_amount is not None else None,
                "unit": "грн" if pay_amount not in (None, 0) else None,
                "hint_ru": (
                    "Нет доступа"
                    if not show_finance
                    else (f"{len(payable_rows)} платежа" if payable_rows else ("Нет данных" if not invoices else "Нет счетов к оплате"))
                ),
                "view": "accounting",
                "empty": not show_finance or not payable_rows,
                "masked": not show_finance,
            },
            {
                "id": "overdue",
                "label_ru": "Просрочено",
                "value": len(overdue_invoices) + len(overdue_tasks),
                "unit": None,
                "hint_ru": (
                    f"{len(overdue_invoices)} платежей · {len(overdue_tasks)} задач"
                    if (overdue_invoices or overdue_tasks)
                    else "Нет просроченных оплат"
                ),
                "view": "accounting" if overdue_invoices or not overdue_tasks else "tasks",
                "filter": "overdue",
                "empty": not overdue_invoices and not overdue_tasks,
            },
            {
                "id": "critical",
                "label_ru": "Критические события",
                "value": critical_n,
                "unit": None,
                "hint_ru": "Нет данных" if not today_events else f"{len(today_events)} событий сегодня",
                "view": "home",
                "empty": not today_events,
            },
        ]

        pipeline = []
        for pid, label, members in DEAL_PIPELINE:
            rows = [d for d in deals if str(d.get("status") or "draft").lower() in members]
            total = None
            amounts = []
            for d in rows:
                qty = _num(d.get("quantity"))
                price = _num(d.get("price"))
                if qty is not None and price is not None:
                    amounts.append(qty * price)
            if amounts:
                total = round(sum(amounts), 2)
            pipeline.append(
                {
                    "id": pid,
                    "label_ru": label,
                    "count": len(rows),
                    "value": total if show_finance or show_margins else None,
                    "currency": next((d.get("currency") for d in rows if d.get("currency")), None),
                    "view": "deals",
                    "pipeline": pid,
                }
            )

        deal_cards = []
        for d in active_deals[:8]:
            qty = _num(d.get("quantity"))
            price = _num(d.get("price"))
            value = round(qty * price, 2) if qty is not None and price is not None else None
            calc = next((c for c in active_only(bag.get("calculation") or []) if str(c.get("deal_id")) == str(d.get("id"))), None)
            totals = (calc or {}).get("totals") or {}
            deal_cards.append(
                {
                    "id": d.get("id"),
                    "title": d.get("title") or d.get("name") or "Сделка",
                    "status": d.get("status"),
                    "pipeline": _pipeline_id(str(d.get("status") or "")),
                    "counterparty": _cp_name(bag, d.get("counterparty_id")),
                    "counterparty_id": d.get("counterparty_id"),
                    "crop": d.get("crop") or d.get("product"),
                    "volume": qty,
                    "unit": d.get("unit") or "т",
                    "price": price,
                    "currency": d.get("currency"),
                    "delivery_terms": d.get("incoterms") or d.get("delivery_terms"),
                    "manager": d.get("responsible") or d.get("manager") or d.get("owner"),
                    "contract_id": d.get("contract_id"),
                    "value": value,
                    "margin": (totals.get("gross_profit") if show_margins else None),
                    "margin_pct": (totals.get("margin_pct") if show_margins else None),
                    "is_demo": bool(d.get("is_demo")),
                }
            )

        ship_stage_counts = []
        for sid, label, members in SHIPMENT_STAGES:
            if sid == "delayed":
                n = len(delayed_shipments)
            else:
                n = len(
                    [
                        s
                        for s in shipments
                        if _ship_stage(str(s.get("status") or ""), s in delayed_shipments) == sid
                    ]
                )
            ship_stage_counts.append({"id": sid, "label_ru": label, "count": n})

        ship_cards = []
        for s in (in_transit + delayed_shipments):
            if any(c.get("id") == s.get("id") for c in ship_cards):
                continue
            status = str(s.get("status") or "planned")
            eta = s.get("eta") or s.get("arrival_planned") or s.get("deadline_at")
            delayed = s in delayed_shipments
            vehicle = next((v for v in active_only(bag.get("vehicle") or []) if str(v.get("id")) == str(s.get("vehicle_id") or "")), None)
            ship_cards.append(
                {
                    "id": s.get("id"),
                    "number": s.get("shipment_number") or s.get("number") or s.get("title"),
                    "title": s.get("title") or s.get("name"),
                    "counterparty": _cp_name(bag, s.get("counterparty_id")),
                    "crop": s.get("crop") or s.get("commodity") or s.get("product"),
                    "volume": _num(s.get("quantity") or s.get("quantity_planned")),
                    "unit": s.get("unit") or "т",
                    "route": s.get("route") or s.get("from_to") or (
                        f"{s.get('origin') or ''} → {s.get('destination') or ''}".strip(" →") or None
                    ),
                    "transport": (vehicle or {}).get("plate") or s.get("transport") or s.get("vehicle_plate"),
                    "eta": eta if eta else None,
                    "eta_missing": not bool(eta),
                    "stage": _ship_stage(status, delayed),
                    "status": status,
                    "days_remaining": _days_left(eta),
                    "responsible": s.get("responsible") or s.get("owner") or s.get("manager"),
                    "delay_reason": s.get("delay_reason") or s.get("reason") if delayed else None,
                    "deal_id": s.get("deal_id"),
                    "is_demo": bool(s.get("is_demo")),
                }
            )
            if len(ship_cards) >= 12:
                break

        receipt_today = sum(
            (_dec(o.get("quantity")) for o in ops if str(o.get("type") or o.get("operation_type") or "").upper() == "RECEIPT" and str(o.get("created_at") or "")[:10] == today),
            _dec(0),
        )
        issue_today = sum(
            (_dec(o.get("quantity")) for o in ops if str(o.get("type") or o.get("operation_type") or "").upper() == "ISSUE" and str(o.get("created_at") or "")[:10] == today),
            _dec(0),
        )
        wh_cards = []
        for w in warehouses[:12]:
            wlots = [l for l in lots if str(l.get("warehouse_id")) == str(w.get("id"))]
            stock = sum((_dec(l.get("quantity")) for l in wlots), _dec(0))
            cap = _dec(w.get("capacity_total"))
            wops = [o for o in ops if str(o.get("warehouse_id")) == str(w.get("id"))]
            last = max(wops, key=lambda x: str(x.get("created_at") or ""), default=None)
            crops = sorted({_s(l.get("commodity") or l.get("crop")) for l in wlots if _s(l.get("commodity") or l.get("crop"))})
            wh_cards.append(
                {
                    "id": w.get("id"),
                    "name": w.get("name") or w.get("title") or "Склад",
                    "owner": w.get("owner") or w.get("owner_name") or _cp_name(bag, w.get("counterparty_id")),
                    "location": w.get("location") or w.get("city") or w.get("address") or w.get("region"),
                    "capacity": _money(cap) if cap else None,
                    "stock": _money(stock),
                    "free": _money(cap - stock) if cap else None,
                    "crops_count": len(crops),
                    "crops": crops,
                    "last_movement": (last or {}).get("created_at") if last else None,
                    "is_demo": bool(w.get("is_demo")),
                }
            )

        market_cards = self._cc_markets(prices, bag)
        weather_block = self._cc_weather(org)
        intel_block = self._cc_intel(reports, show_intel)
        sources = self._cc_sources(bag)

        notif_groups: dict[str, int] = defaultdict(int)
        for n in notifications:
            cat = self._cc_notif_category(n)
            if str(n.get("status")) not in {"read", "done", "archived"}:
                notif_groups[cat] += 1
        for a in alerts:
            if str(a.get("status")) not in {"read", "done", "closed"}:
                notif_groups[self._cc_notif_category(a)] += 1

        return {
            "version": COMMAND_CENTER_VERSION,
            "role": role_id,
            "blocks": ROLE_BLOCK_ORDER.get(role_id, ROLE_BLOCK_ORDER["agro_manager"]),
            "can_create": can(role, "create"),
            "can_finance": show_finance,
            "can_margins": show_margins,
            "summary": summary,
            "today": today_events[:20],
            "deals": {"pipeline": pipeline, "items": deal_cards},
            "shipments": {"stages": ship_stage_counts, "items": ship_cards},
            "warehouses": {
                "items": wh_cards,
                "receipt_today": _money(receipt_today),
                "issue_today": _money(issue_today),
                "top_crops": [{"name": n, "quantity": _money(sum((_dec(l.get("quantity")) for l in lots if _s(l.get("commodity") or l.get("crop")) == n), _dec(0)))} for n in crop_names[:12]],
            },
            "markets": market_cards,
            "weather": weather_block,
            "intel": intel_block,
            "tasks": {
                "today": [_cc_task(t) for t in tasks_today[:10]],
                "overdue": [_cc_task(t) for t in overdue_tasks[:10]],
                "week": [_cc_task(t) for t in tasks_week[:10]],
                "meetings": [
                    {
                        "id": e.get("id"),
                        "title": e.get("title") or e.get("name"),
                        "starts_at": e.get("starts_at"),
                        "deal_id": e.get("deal_id"),
                        "counterparty_id": e.get("counterparty_id"),
                    }
                    for e in meetings[:8]
                ],
            },
            "notifications": {
                "unread": sum(notif_groups.values()),
                "by_category": [{"id": k, "label_ru": NOTIF_LABELS.get(k, k), "count": v} for k, v in sorted(notif_groups.items())],
            },
            "sources_status": sources,
            "counterparties_count": len(cps),
            "trips_active": len([t for t in trips if str(t.get("status")) in {"planned", "assigned", "loading", "in_transit", "unloading"}]),
        }

    def _cc_today_events(self, org: str, **ctx: Any) -> list[dict[str, Any]]:
        today = ctx["today"]
        events: list[dict[str, Any]] = []
        bag = ctx["bag"]

        for s in ctx["delayed"]:
            events.append(
                _event(
                    "CRITICAL",
                    "Поставка задерживается",
                    f"{s.get('title') or s.get('name') or 'Поставка'} не закрыта к сроку.",
                    "shipment",
                    s,
                    action_view="shipments",
                )
            )
        for s in ctx["shipments"]:
            if str(s.get("status")) in {"port", "at_port"}:
                events.append(
                    _event(
                        "HIGH",
                        "Поставка прибыла в порт",
                        f"{s.get('title') or s.get('name') or 'Поставка'} — статус порт.",
                        "shipment",
                        s,
                        action_view="shipments",
                    )
                )
            if str(s.get("status")) in {"customs", "port", "in_transit"}:
                has_customs = any(
                    str(d.get("deal_id") or "") == str(s.get("deal_id") or "-")
                    and str(d.get("doc_type") or "") == "customs"
                    for d in ctx["documents"]
                ) or any(
                    str(f.get("entity_id")) == str(s.get("id")) and str(f.get("doc_type") or "") == "customs"
                    for f in ctx["files"]
                )
                if not has_customs and s.get("deal_id"):
                    events.append(
                        _event(
                            "HIGH",
                            "Нужно подготовить таможенные документы",
                            f"У поставки {s.get('title') or s.get('id')} нет таможенного файла.",
                            "shipment",
                            s,
                            action_view="documents",
                        )
                    )
        for inv in ctx["invoices"]:
            events.append(
                _event(
                    "CRITICAL",
                    "Просрочен платёж",
                    f"{inv.get('title') or 'Счёт'} · {inv.get('amount') or 'Нет данных'} {inv.get('currency') or ''}".strip(),
                    "invoice",
                    inv,
                    action_view="accounting",
                    deadline=inv.get("due_at"),
                )
            )
        for ev in self.contract_expiry_events(ctx["contracts"]):
            left = int(ev.get("days_left") or 0)
            sev = "CRITICAL" if left <= 1 else ("HIGH" if left <= 7 else "MEDIUM")
            events.append(
                _event(
                    sev,
                    "Истекает договор",
                    f"{ev.get('title') or 'Договор'} — {left} дн. (до {ev.get('ends_at')}).",
                    "contract",
                    {"id": ev.get("id"), "title": ev.get("title"), "ends_at": ev.get("ends_at")},
                    action_view="contracts",
                    deadline=ev.get("ends_at"),
                )
            )
        for t in ctx["tasks"]:
            events.append(
                _event(
                    "HIGH",
                    "Задача просрочена",
                    str(t.get("title") or t.get("name") or "Задача"),
                    "task",
                    t,
                    action_view="tasks",
                    deadline=t.get("due_at"),
                )
            )
        for d in ctx["deals"]:
            if str(d.get("status")) in {"closed", "cancelled", "draft"}:
                continue
            linked_docs = [x for x in ctx["documents"] if str(x.get("deal_id")) == str(d.get("id"))]
            linked_files = [x for x in ctx["files"] if str(x.get("entity_id")) == str(d.get("id"))]
            if not linked_docs and not linked_files:
                events.append(
                    _event(
                        "MEDIUM",
                        "Нет обязательного файла по сделке",
                        f"{d.get('title') or 'Сделка'} без вложения.",
                        "deal",
                        d,
                        action_view="documents",
                    )
                )
        for rule in (bag.get("alert_rule") or []):
            if rule.get("archived") or rule.get("active") is False:
                continue
            crop = _s(rule.get("commodity") or rule.get("crop"))
            target = _num(rule.get("target_price") or rule.get("threshold"))
            op = str(rule.get("operator") or rule.get("op") or "lt").lower()
            latest = next(
                (
                    p
                    for p in sorted(ctx["prices"], key=lambda x: str(x.get("valid_from") or x.get("created_at") or ""), reverse=True)
                    if _s(p.get("commodity") or p.get("crop")) == crop
                ),
                None,
            )
            price = _num((latest or {}).get("price"))
            if crop and target is not None and price is not None:
                crossed = (op in {"lt", "<", "below"} and price < target) or (op in {"gt", ">", "above"} and price > target)
                if crossed:
                    events.append(
                        {
                            "id": f"price-{rule.get('id')}",
                            "severity": "HIGH",
                            "severity_ru": SEVERITY_RU["HIGH"],
                            "title": "Цена культуры пересекла заданный уровень",
                            "explanation": f"{crop}: {price} (порог {target}). Источник: {_price_kind(str((latest or {}).get('source_type') or 'MANUAL'))}.",
                            "entity_type": "market_price",
                            "entity_id": (latest or {}).get("id"),
                            "entity_label": crop,
                            "responsible": rule.get("owner"),
                            "deadline": None,
                            "action_ru": "Открыть цены",
                            "view": "markets",
                            "is_demo": bool((latest or {}).get("is_demo")),
                        }
                    )
        for w in ctx["warehouses"]:
            min_qty = _num(w.get("min_stock") or w.get("min_quantity"))
            if min_qty is None:
                continue
            stock = sum(
                (_num(l.get("quantity")) or 0)
                for l in ctx["lots"]
                if str(l.get("warehouse_id")) == str(w.get("id"))
            )
            if stock < min_qty:
                events.append(
                    _event(
                        "HIGH",
                        "Склад ниже заданного остатка",
                        f"{w.get('name') or 'Склад'}: {stock} < {min_qty}.",
                        "warehouse",
                        w,
                        action_view="warehouses",
                    )
                )
        weather = self._cc_weather(org)
        for m in weather.get("regions") or []:
            if m.get("missing"):
                continue
            risk = str(m.get("risk_ru") or "")
            if "повышенный риск" in risk.lower() or "дефицит" in risk.lower() or "избыток" in risk.lower():
                events.append(
                    {
                        "id": f"wx-{m.get('macro_id')}",
                        "severity": "HIGH",
                        "severity_ru": SEVERITY_RU["HIGH"],
                        "title": "Погодный риск",
                        "explanation": f"{m.get('title_ru')}: {risk}",
                        "entity_type": "weather",
                        "entity_id": m.get("macro_id"),
                        "entity_label": m.get("title_ru"),
                        "responsible": None,
                        "deadline": None,
                        "action_ru": "Открыть карту",
                        "view": "weather",
                        "is_demo": False,
                    }
                )
        order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "INFO": 3}
        events.sort(key=lambda e: (order.get(str(e.get("severity")), 9), str(e.get("title"))))
        return events

    def _cc_markets(self, prices: list[dict[str, Any]], bag: dict[str, list]) -> list[dict[str, Any]]:
        from services.agro_ops.service import active_only

        markets = active_only(bag.get("market") or [])
        latest: dict[str, dict[str, Any]] = {}
        ordered = sorted(prices, key=lambda p: str(p.get("valid_from") or p.get("created_at") or ""), reverse=True)
        for p in ordered:
            crop = _s(p.get("commodity") or p.get("crop"))
            if not crop or crop in latest:
                continue
            latest[crop] = p
        cards = []
        for crop, p in list(latest.items())[:12]:
            hist = [
                x for x in prices
                if _s(x.get("commodity") or x.get("crop")) == crop
            ]
            hist.sort(key=lambda x: str(x.get("valid_from") or x.get("created_at") or ""))
            prev = _num(hist[-2].get("price")) if len(hist) > 1 else None
            cur = _num(p.get("price"))
            change = round(cur - prev, 4) if cur is not None and prev is not None else None
            market = next((m for m in markets if str(m.get("id")) == str(p.get("market_id") or "")), None)
            src = str(p.get("source_type") or "MANUAL")
            cards.append(
                {
                    "crop": crop,
                    "price": cur,
                    "currency": p.get("currency") or "UAH",
                    "unit": p.get("unit") or "т",
                    "market": (market or {}).get("name") or p.get("market_name"),
                    "source_type": src,
                    "source_label_ru": _price_kind(src),
                    "change": change,
                    "updated_at": p.get("valid_from") or p.get("created_at"),
                    "manual": src.upper() in {"MANUAL", "COUNTERPARTY", "CONTRACT", "OURS", "INTERNAL"},
                    "is_demo": bool(p.get("is_demo")),
                    "missing": cur is None,
                }
            )
        return cards

    def _cc_weather(self, org: str) -> dict[str, Any]:
        from services.agro_ops.weather import MACRO_REGIONS, UA_OBLASTS, region_narrative, _avg

        rows = self._weather_rows(org)  # type: ignore[attr-defined]
        by_oblast: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            oid = str(row.get("oblast_id") or "")
            if oid:
                by_oblast[oid].append(row)
        oblast_summaries = [self._oblast_summary(spec, by_oblast.get(spec["id"]) or []) for spec in UA_OBLASTS]  # type: ignore[attr-defined]
        regions = []
        any_data = False
        for macro in MACRO_REGIONS:
            members = [s for s in oblast_summaries if s.get("macro") == macro["id"]]
            tmax = _avg([s.get("tmax_avg") for s in members])
            p7 = _avg([s.get("precip_7") for s in members])
            p30 = _avg([s.get("precip_30") for s in members])
            narr = region_narrative(macro["id"], tmax, p7, p30)
            missing = bool(narr.get("missing"))
            if not missing:
                any_data = True
            precip_label = "Нет данных"
            if p7 is not None:
                precip_label = "низкие" if p7 < 8 else ("высокие" if p7 >= 40 else "умеренные")
            regions.append(
                {
                    "macro_id": macro["id"],
                    "title_ru": macro["short_ru"],
                    "full_title_ru": macro["label_ru"],
                    "tmax": tmax,
                    "precip_7": p7,
                    "precip_label_ru": precip_label,
                    "risk_ru": narr.get("risk_ru") if not missing else "Нет данных",
                    "next_7_ru": narr.get("next_7_ru"),
                    "recommendation_ru": None if missing else narr.get("monitor_ru"),
                    "missing": missing,
                }
            )
        high = sum(1 for r in regions if not r.get("missing") and "повышенный риск" in str(r.get("risk_ru") or "").lower())
        return {"regions": regions, "has_data": any_data, "high_risks": high}

    def _cc_intel(self, reports: list[dict[str, Any]], show: bool) -> list[dict[str, Any]]:
        if not show:
            return [{"id": i, "label_ru": l, "summary_ru": "Нет данных", "confidence": None, "sources_count": 0, "updated_at": None, "missing": True} for i, l in INTEL_CARDS]
        latest = None
        if reports:
            latest = max(reports, key=lambda r: str(r.get("generated_at") or r.get("created_at") or ""))
        sections = list((latest or {}).get("business_sections") or (latest or {}).get("sections") or [])
        by_id = {}
        for sec in sections:
            if isinstance(sec, dict):
                by_id[str(sec.get("id"))] = sec
        cards = []
        for sid, label in INTEL_CARDS:
            sec = by_id.get(sid) or {}
            bullets = sec.get("bullets") or []
            texts = []
            for b in bullets[:4]:
                if isinstance(b, dict):
                    t = _s(b.get("text") or b.get("detail_ru") or b.get("title"))
                else:
                    t = _s(b)
                if t and "pipeline_version" not in t.lower() and "http " not in t.lower():
                    texts.append(t)
            summary = " ".join(texts)[:600] if texts else (_s(sec.get("note_ru")) or "Нет данных")
            missing = not texts or str(sec.get("status")) == "NOT_CONFIGURED"
            cards.append(
                {
                    "id": sid,
                    "label_ru": label,
                    "summary_ru": "Нет данных" if missing else summary,
                    "confidence": (latest or {}).get("confidence") if latest and not missing else None,
                    "sources_count": int((latest or {}).get("sources_count") or (latest or {}).get("source_count") or 0) if latest else 0,
                    "updated_at": (latest or {}).get("generated_at") if latest else None,
                    "missing": missing or not latest,
                }
            )
        return cards

    def _cc_sources(self, bag: dict[str, list]) -> dict[str, Any]:
        from services.agro_ops.service import active_only

        snaps = active_only(bag.get("provider_snapshot") or [])
        bad_states = {"ERROR", "DEGRADED", "UNAVAILABLE", "STALE"}
        issues = [
            s for s in snaps
            if str(s.get("health_state") or s.get("status") or "").upper() in bad_states
        ]
        if not snaps:
            return {
                "ok": True,
                "label_ru": "Нет данных о источниках",
                "issues": 0,
                "href": "/workspace/agro?view=settings&tab=sources",
            }
        if issues:
            return {
                "ok": False,
                "label_ru": f"Есть проблемы с {len(issues)} источниками",
                "issues": len(issues),
                "href": "/workspace/agro?view=settings&tab=diagnostics",
            }
        return {
            "ok": True,
            "label_ru": "Данные актуальны",
            "issues": 0,
            "href": "/workspace/agro?view=settings&tab=sources",
        }

    def _cc_notif_category(self, row: dict[str, Any]) -> str:
        kind = str(row.get("kind") or row.get("category") or row.get("entity_type") or "").lower()
        title = str(row.get("title") or "").lower()
        mapping = [
            ("deal", "deals"),
            ("сделк", "deals"),
            ("payment", "payments"),
            ("invoice", "payments"),
            ("платеж", "payments"),
            ("shipment", "shipments"),
            ("постав", "shipments"),
            ("warehouse", "warehouse"),
            ("склад", "warehouse"),
            ("price", "prices"),
            ("market", "prices"),
            ("цен", "prices"),
            ("weather", "weather"),
            ("погод", "weather"),
            ("document", "documents"),
            ("файл", "documents"),
            ("task", "tasks"),
            ("задач", "tasks"),
        ]
        blob = f"{kind} {title}"
        for needle, cat in mapping:
            if needle in blob:
                return cat
        return "system"

    async def search_ops(self, organization_id: str, role: str | None, query: str) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        q = (query or "").strip().lower()
        if not q:
            return {"ok": True, "query": query, "groups": []}
        bag = self._bag(org)  # type: ignore[attr-defined]
        groups = []
        for kind, label, fields in SEARCH_SPEC:
            hits = []
            for row in active_only(bag.get(kind) or []):
                blob = " ".join(_s(row.get(f)).lower() for f in fields)
                if q in blob or q in _s(row.get("id")).lower():
                    hits.append(
                        {
                            "id": row.get("id"),
                            "kind": kind,
                            "title": row.get("title") or row.get("name") or row.get("filename") or row.get("plate") or row.get("id"),
                            "subtitle": row.get("city") or row.get("crop") or row.get("status") or row.get("edrpou") or row.get("phone"),
                            "view": _kind_view(kind),
                        }
                    )
                if len(hits) >= 8:
                    break
            if hits:
                groups.append({"id": kind, "label_ru": label, "items": hits})
        return {"ok": True, "query": query, "groups": groups}

    def _cc_timezone(self, org: str) -> str:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        for row in active_only(bag.get("settings") or []):
            tz = str(row.get("timezone") or "").strip()
            if tz:
                return tz
        return "Europe/Kyiv"

    def _cc_workspace_currency(self, org: str) -> str:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        for row in active_only(bag.get("settings") or []):
            ccy = str(row.get("preferred_currency") or row.get("currency") or "").strip()
            if ccy:
                return ccy
        return "UAH"

    async def command_center_read(
        self,
        organization_id: str,
        role: str | None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Aggregated Command Center read — does not duplicate source-of-truth tables."""
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        q = query or {}
        workspace_id = str(q.get("workspace_id") or "agro").strip() or "agro"
        dash = await self.dashboard(org, role)  # type: ignore[attr-defined]
        if not dash.get("ok"):
            return dash
        cc = dict(dash.get("command_center") or {})
        grain_stock = dict(cc.get("grain_stock") or {})
        if grain_stock.get("lots"):
            lots = list(grain_stock.get("lots") or [])
            grain_stock["lots"] = lots[:8]
            grain_stock["lots_total"] = len(lots)
            grain_stock["lots_truncated"] = len(lots) > 8
            cc["grain_stock"] = grain_stock

        role_id = normalize_role(role)
        company = role_id in {"agro_director", "agro_owner", "agro_admin", "platform_owner"}
        show_finance = can(role, "finance")
        show_inventory = company or role_id in {"agro_manager", "agro_warehouse", "agro_viewer", "agro_observer"}
        show_logistics = company or role_id in {"agro_manager", "agro_logistics", "agro_viewer", "agro_observer"}
        show_fields = company or role_id in {"agro_manager", "agro_agronomist", "agro_mechanic", "agro_viewer", "agro_observer"}
        fin = self.finance_summary_data(org) if show_finance else {}  # type: ignore[attr-defined]
        tz = self._cc_timezone(org)
        base_ccy = self._cc_workspace_currency(org)
        cash = {
            "empty": True,
            "empty_ru": "Остаток денежных средств не задан",
            "mixed": bool(fin.get("mixed_currencies")),
            "by_currency": fin.get("cash_by_currency") or fin.get("by_currency") or [],
            "fx": {"available": False, "message_ru": "Курс не подключён"},
            "receivables": fin.get("receivables_by_currency") if show_finance else [],
            "payables": fin.get("payables_by_currency") if show_finance else [],
            "overdue": fin.get("overdue_by_currency") if show_finance else [],
            "view": "accounting",
            "filter": "overdue",
        }
        if cash["by_currency"] or cash["receivables"] or cash["payables"]:
            cash["empty"] = not cash["by_currency"]
        harvest_rows = list(cc.get("grain_today") or [])
        harvest_empty = not harvest_rows and not (cc.get("director_production") or {}).get("harvest_tonnes")
        harvest = {
            "empty": harvest_empty,
            "empty_ru": "Нет данных об урожае",
            "metrics": harvest_rows,
            "director": cc.get("director_production") if show_fields else None,
            "view": "fields",
        }
        trips_in_transit = [s for s in (cc.get("shipments") or {}).get("items") or [] if str(s.get("status") or "").lower() in {"in_transit", "loading", "loaded"}]
        logistics = {
            "empty": not ((cc.get("shipments") or {}).get("items") or []),
            "empty_ru": "Нет активных перевозок",
            "in_transit": len(trips_in_transit) or next((st.get("count") for st in ((cc.get("shipments") or {}).get("stages") or []) if st.get("id") == "in_transit"), 0),
            "stages": (cc.get("shipments") or {}).get("stages") or [],
            "items": ((cc.get("shipments") or {}).get("items") or [])[:20],
            "view": "logistics",
            "filter": "IN_TRANSIT",
        }
        inventory = {
            "empty": not ((cc.get("warehouses") or {}).get("items") or []) and not (grain_stock.get("by_crop") or []),
            "empty_ru": "Нет данных об остатках",
            "by_crop": (grain_stock.get("by_crop") or [])[:12],
            "warehouses": ((cc.get("warehouses") or {}).get("items") or [])[:12],
            "view": "warehouses",
        }
        risks = {
            "empty": not (cc.get("today") or []),
            "empty_ru": "Нет критических событий",
            "items": list(cc.get("today") or [])[:20],
            "view": "home",
        }
        data_quality = cc.get("sources_status") or {"ok": True, "label_ru": "Нет данных о источниках"}
        kpis = list(cc.get("summary") or [])
        decisions = [ev for ev in (cc.get("today") or []) if str(ev.get("severity") or "") in {"critical", "warning", "high"}]
        sections = {
            "kpis": kpis,
            "decisions": decisions,
            "today": cc.get("today") or [],
            "cash": cash if show_finance else {"empty": True, "forbidden": True, "empty_ru": "Нет доступа"},
            "inventory": inventory if show_inventory else {"empty": True, "forbidden": True, "empty_ru": "Нет доступа"},
            "logistics": logistics if show_logistics else {"empty": True, "forbidden": True, "empty_ru": "Нет доступа"},
            "fields": (cc.get("director_production") or cc.get("agronomist_today") or {"empty": True, "empty_ru": "Нет данных по полям"}) if show_fields else {"empty": True, "forbidden": True, "empty_ru": "Нет доступа"},
            "harvest": harvest if show_fields or show_inventory else {"empty": True, "forbidden": True, "empty_ru": "Нет доступа"},
            "risks": risks,
            "data_quality": data_quality,
        }
        cc["cash"] = sections["cash"]
        cc["harvest"] = sections["harvest"]
        cc["timezone"] = tz
        cc["currency"] = base_ccy
        return {
            "ok": True,
            "organization_id": org,
            "workspace_id": workspace_id,
            "timezone": tz,
            "currency": base_ccy,
            "command_center_version": dash.get("command_center_version") or "AGRO_2_0",
            "kpis": kpis,
            "decisions": sections["decisions"],
            "today": sections["today"],
            "cash": sections["cash"],
            "inventory": sections["inventory"],
            "logistics": sections["logistics"],
            "fields": sections["fields"],
            "harvest": sections["harvest"],
            "risks": sections["risks"],
            "data_quality": sections["data_quality"],
            "command_center": cc,
            "cards": dash.get("cards") or {},
            "demo_mode": dash.get("demo_mode"),
            "demo_notice_ru": dash.get("demo_notice_ru"),
            "channels": dash.get("channels") or {},
            "onboarding": dash.get("onboarding") or {},
        }

    async def management_brief(
        self,
        organization_id: str,
        role: str | None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        denied = require(role, "export") or require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        cc_read = await self.command_center_read(org, role, query)
        if not cc_read.get("ok"):
            return cc_read
        tz = str(cc_read.get("timezone") or "Europe/Kyiv")
        ccy = str(cc_read.get("currency") or "UAH")
        kpis = cc_read.get("kpis") or []
        cash = cc_read.get("cash") or {}
        harvest = cc_read.get("harvest") or {}
        logistics = cc_read.get("logistics") or {}
        lines = [
            "АГРО — УПРАВЛЕНЧЕСКАЯ СВОДКА",
            f"Организация: {cc_read.get('organization_id')}",
            f"Рабочее пространство: {cc_read.get('workspace_id')}",
            f"Часовой пояс: {tz}",
            f"Валюта кабинета: {ccy}",
            "",
            "KPI",
        ]
        for k in kpis:
            val = k.get("value")
            hint = k.get("hint_ru") or ""
            lines.append(f"- {k.get('label_ru')}: {val if val is not None else 'Нет данных'} {k.get('unit') or ''} {hint}".strip())
        lines.append("")
        lines.append("Денежные средства")
        if cash.get("empty") or cash.get("forbidden"):
            lines.append(str(cash.get("empty_ru") or "Остаток денежных средств не задан"))
        elif cash.get("mixed"):
            lines.append("Несколько валют — суммы не складываются.")
            for row in cash.get("by_currency") or []:
                lines.append(f"- {row.get('currency')}: {row.get('amount')}")
        else:
            for row in cash.get("by_currency") or cash.get("receivables") or []:
                lines.append(f"- {row.get('currency')}: {row.get('amount')}")
        lines.append("")
        lines.append("Урожай")
        lines.append(str(harvest.get("empty_ru") if harvest.get("empty") else "См. KPI урожая"))
        lines.append("")
        lines.append("Логистика")
        lines.append(str(logistics.get("empty_ru") if logistics.get("empty") else f"В пути: {logistics.get('in_transit') or 0}"))
        text = "\n".join(lines)
        html = (
            "<!DOCTYPE html><html lang=\"ru\"><head><meta charset=\"utf-8\">"
            "<title>АГРО — УПРАВЛЕНЧЕСКАЯ СВОДКА</title>"
            "<style>body{font-family:sans-serif;max-width:720px;margin:24px auto;color:#111}"
            "h1{font-size:20px}pre{white-space:pre-wrap}</style></head><body>"
            "<h1>АГРО — УПРАВЛЕНЧЕСКАЯ СВОДКА</h1>"
            f"<pre>{text}</pre></body></html>"
        )
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="report",
            entity_id="management_brief",
            action="exported",
            summary="Управленческая сводка Агро",
            role=role,
            payload={"source": "command_center", "workspace_id": cc_read.get("workspace_id")},
        )
        return {
            "ok": True,
            "title": "АГРО — УПРАВЛЕНЧЕСКАЯ СВОДКА",
            "text": text,
            "html": html,
            "timezone": tz,
            "currency": ccy,
            "organization_id": cc_read.get("organization_id"),
            "workspace_id": cc_read.get("workspace_id"),
        }


NOTIF_LABELS = {
    "deals": "Сделки",
    "payments": "Платежи",
    "shipments": "Поставки",
    "warehouse": "Склад",
    "prices": "Цены",
    "weather": "Погода",
    "documents": "Документы",
    "tasks": "Задачи",
    "system": "Система",
}


def _kind_view(kind: str) -> str:
    return {
        "counterparty": "counterparties",
        "deal": "deals",
        "contract": "contracts",
        "document": "documents",
        "file": "documents",
        "shipment": "shipments",
        "warehouse": "warehouses",
        "crop": "crops",
        "task": "tasks",
        "payment": "accounting",
        "vehicle": "logistics",
        "driver": "logistics",
        "agro_operation": "operations",
        "truck_run": "operations",
        "inventory_lot": "warehouses",
        "agro_field": "fields",
        "crop_season": "fields",
        "field_work": "fields",
        "machine": "machinery",
        "material": "fields",
        "harvest_actual": "fields",
    }.get(kind, "home")


def _cc_task(t: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": t.get("id"),
        "title": t.get("title") or t.get("name"),
        "due_at": t.get("due_at"),
        "status": t.get("status"),
        "owner": t.get("owner") or t.get("responsible"),
        "deal_id": t.get("deal_id"),
        "counterparty_id": t.get("counterparty_id"),
        "shipment_id": t.get("shipment_id"),
        "warehouse_id": t.get("warehouse_id"),
        "document_id": t.get("document_id"),
        "payment_id": t.get("payment_id"),
        "is_demo": bool(t.get("is_demo")),
    }


def _event(
    severity: str,
    title: str,
    explanation: str,
    entity_type: str,
    row: dict[str, Any],
    *,
    action_view: str,
    deadline: Any = None,
) -> dict[str, Any]:
    return {
        "id": f"{entity_type}-{row.get('id')}-{title}",
        "severity": severity,
        "severity_ru": SEVERITY_RU[severity],
        "title": title,
        "explanation": explanation,
        "entity_type": entity_type,
        "entity_id": row.get("id"),
        "entity_label": row.get("title") or row.get("name") or row.get("filename"),
        "responsible": row.get("responsible") or row.get("owner") or row.get("manager"),
        "deadline": deadline or row.get("due_at") or row.get("deadline_at") or row.get("ends_at"),
        "action_ru": "Открыть",
        "view": action_view,
        "is_demo": bool(row.get("is_demo")),
    }
