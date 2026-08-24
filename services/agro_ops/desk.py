"""AGRO 1.2 — alerts, crop availability/demand, deliveries, calendar, notifications."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from services.agro_ops.rbac import normalize_role, require

TWO = Decimal("0.01")
DEMO_MARK = "DEMO"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dec(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _qty(value: Any) -> float:
    return float(_dec(value))


def _pct(delivered: Decimal, planned: Decimal) -> float:
    if planned <= 0:
        return 0.0
    return float((delivered * Decimal("100") / planned).quantize(TWO, rounding=ROUND_HALF_UP))


def _parse_dt(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.fromisoformat(raw[:10]).replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def _matches(price: Decimal, operator: str, target: Decimal) -> bool:
    op = (operator or "lt").lower()
    if op in {"lt", "<"}:
        return price < target
    if op in {"lte", "<="}:
        return price <= target
    if op in {"gt", ">"}:
        return price > target
    if op in {"gte", ">="}:
        return price >= target
    if op in {"eq", "="}:
        return price == target
    return False


class AgroOpsDeskMixin:
    """Crop book, deliveries, price alerts, notification actions, demo seed."""

    def normalize_desk_item(self, kind: str, item: dict[str, Any]) -> dict[str, Any]:
        if kind in {"availability", "demand"}:
            item.setdefault("unit", "т")
            item.setdefault("commodity", item.get("crop") or item.get("name"))
            item["quantity"] = _qty(item.get("quantity"))
            if not item.get("name"):
                item["name"] = f"{item.get('commodity') or 'Культура'} {item['quantity']} {item['unit']}"
            if not item.get("title"):
                item["title"] = item["name"]
        if kind == "alert_rule":
            item.setdefault("operator", item.get("condition") or "lt")
            item.setdefault("currency", "UAH")
            item.setdefault("active", True)
            item.setdefault("cooldown_hours", 24)
            item["target_price"] = float(_dec(item.get("target_price") or item.get("price")))
            item.setdefault("commodity", item.get("crop") or "Пшеница")
            if not item.get("name"):
                item["name"] = f"{item['commodity']} {item['operator']} {item['target_price']}"
            if not item.get("title"):
                item["title"] = item["name"]
        if kind == "shipment":
            planned = item.get("quantity_planned")
            if planned in (None, ""):
                planned = item.get("quantity")
            item["quantity_planned"] = _qty(planned)
            item.setdefault("quantity", item["quantity_planned"])
            item.setdefault("quantity_delivered", _qty(item.get("quantity_delivered")))
            item["progress_pct"] = _pct(_dec(item["quantity_delivered"]), _dec(item["quantity_planned"]))
            item.setdefault("crop", item.get("commodity") or "Пшеница")
            item.setdefault("commodity", item.get("crop"))
        if kind == "task":
            item.setdefault("priority", "medium")
            item.setdefault("owner", item.get("created_by") or "")
            item.setdefault("deadline", item.get("due_at"))
            item.setdefault("due_at", item.get("deadline") or item.get("due_at"))
            item.setdefault("entity_type", item.get("linked_type"))
            item.setdefault("entity_id", item.get("linked_id") or item.get("linked_entity_id"))
        if kind == "delivery_leg":
            item["quantity"] = _qty(item.get("quantity"))
            if not item.get("title"):
                item["title"] = f"Частичная поставка {item['quantity']}"
        return item

    async def _after_entity_create(self, org: str, kind: str, item: dict[str, Any], role: str | None) -> None:
        if kind == "shipment":
            await self._ensure_delivery_calendar(org, item, role)
        if kind == "trip" and item.get("shipment_id"):
            await self.refresh_shipment_progress(org, str(item["shipment_id"]), role, trip=item)
        if kind == "calendar" and item.get("remind_before_days") not in (None, ""):
            await self._ensure_reminder_flag(org, item)

    async def _ensure_delivery_calendar(self, org: str, shipment: dict[str, Any], role: str | None) -> None:
        deadline = shipment.get("deadline_at") or shipment.get("due_at") or shipment.get("planned_at")
        if not deadline:
            return
        title = f"Срок поставки: {shipment.get('title') or shipment.get('name')}"
        await self.create_entity(  # type: ignore[attr-defined]
            org,
            "calendar",
            {
                "title": title,
                "starts_at": deadline,
                "event_type": "shipment",
                "shipment_id": shipment.get("id"),
                "deal_id": shipment.get("deal_id"),
                "counterparty_id": shipment.get("counterparty_id"),
                "entity_type": "shipment",
                "entity_id": shipment.get("id"),
            },
            role,
        )

    async def _ensure_reminder_flag(self, org: str, event: dict[str, Any]) -> None:
        event.setdefault("reminder_sent", False)

    async def crop_directory(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.agro_ops.service import DEFAULT_CROPS, _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        crops = active_only(bag.get("crop") or [])
        by_name = {str(c.get("name") or "").strip().lower(): c for c in crops}
        names: list[str] = []
        for name in DEFAULT_CROPS:
            if name.lower() not in {n.lower() for n in names}:
                names.append(name)
        for c in crops:
            n = str(c.get("name") or "").strip()
            if n and n.lower() not in {x.lower() for x in names}:
                names.append(n)
        items = []
        for name in names:
            stored = by_name.get(name.lower())
            bal = self._crop_balance_data(org, name, stored.get("id") if stored else None)
            items.append(
                {
                    "name": name,
                    "crop_id": stored.get("id") if stored else None,
                    "in_catalog": True,
                    "registered": bool(stored),
                    **bal,
                }
            )
        return {"ok": True, "items": items}

    def _crop_balance_data(self, org: str, commodity: str, crop_id: str | None) -> dict[str, Any]:
        from services.agro_ops.service import active_only

        bag = self._bag(org)  # type: ignore[attr-defined]
        key = (commodity or "").strip().lower()

        def match(row: dict[str, Any]) -> bool:
            if crop_id and str(row.get("crop_id") or "") == str(crop_id):
                return True
            return str(row.get("commodity") or row.get("crop") or "").strip().lower() == key

        avail = sum((_dec(r.get("quantity")) for r in active_only(bag.get("availability") or []) if match(r)), Decimal("0"))
        demand = sum((_dec(r.get("quantity")) for r in active_only(bag.get("demand") or []) if match(r)), Decimal("0"))
        return {
            "available": float(avail),
            "demand": float(demand),
            "gap": float(avail - demand),
            "unit": "т",
        }

    async def crop_balance(self, organization_id: str, crop_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        crop = next((c for c in active_only(self._bag(org)["crop"]) if str(c.get("id")) == str(crop_id)), None)  # type: ignore[attr-defined]
        if not crop:
            return {"ok": False, "error": "not_found", "message_ru": "Культура не найдена"}
        bal = self._crop_balance_data(org, str(crop.get("name") or ""), str(crop["id"]))
        return {"ok": True, "item": {**crop, **bal}}

    async def refresh_shipment_progress(
        self,
        organization_id: str,
        shipment_id: str,
        role: str | None = None,
        *,
        trip: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        ship = next((s for s in bag.get("shipment") or [] if str(s.get("id")) == str(shipment_id) and not s.get("archived_at")), None)
        if not ship:
            return {"ok": False, "error": "not_found", "message_ru": "Поставка не найдена"}
        if trip:
            qty = _dec(trip.get("weight_actual") or trip.get("weight_planned") or trip.get("quantity"))
            if qty > 0:
                await self.create_entity(  # type: ignore[attr-defined]
                    org,
                    "delivery_leg",
                    {
                        "shipment_id": shipment_id,
                        "trip_id": trip.get("id"),
                        "quantity": float(qty),
                        "title": f"Рейс {trip.get('title') or trip.get('id')}",
                    },
                    role,
                )
        legs = active_only([x for x in bag.get("delivery_leg") or [] if str(x.get("shipment_id")) == str(shipment_id)])
        delivered = sum((_dec(x.get("quantity")) for x in legs), Decimal("0"))
        planned = _dec(ship.get("quantity_planned") or ship.get("quantity"))
        patch = {
            "quantity_delivered": float(delivered),
            "progress_pct": _pct(delivered, planned),
            "quantity_planned": float(planned),
        }
        return await self.update_entity(org, "shipment", shipment_id, patch, role or "platform_owner")  # type: ignore[attr-defined]

    async def record_delivery_progress(
        self, organization_id: str, shipment_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        qty = _dec(body.get("quantity"))
        if qty <= 0:
            return {"ok": False, "error": "validation", "message_ru": "Укажите количество больше нуля"}
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        ship = next((s for s in self._bag(org).get("shipment") or [] if str(s.get("id")) == str(shipment_id)), None)  # type: ignore[attr-defined]
        if not ship:
            return {"ok": False, "error": "not_found", "message_ru": "Поставка не найдена"}
        leg = await self.create_entity(  # type: ignore[attr-defined]
            org,
            "delivery_leg",
            {
                "shipment_id": shipment_id,
                "trip_id": body.get("trip_id"),
                "quantity": float(qty),
                "title": body.get("title") or f"Частичная поставка {qty}",
                "notes": body.get("notes"),
            },
            role,
        )
        if not leg.get("ok"):
            return leg
        refreshed = await self.refresh_shipment_progress(org, shipment_id, role)
        return {"ok": True, "item": refreshed.get("item"), "leg": leg.get("item")}

    async def evaluate_alerts(self, organization_id: str | None = None, role: str | None = "platform_owner") -> dict[str, Any]:
        denied = require(role, "intel") if role and role != "platform_owner" else None
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        created: list[dict[str, Any]] = []
        skipped = 0
        for rule in active_only(bag.get("alert_rule") or []):
            if rule.get("active") is False:
                continue
            commodity = str(rule.get("commodity") or rule.get("crop") or "").strip().lower()
            prices = [
                p
                for p in active_only(bag.get("market_price") or [])
                if str(p.get("commodity") or p.get("crop") or "").strip().lower() == commodity
            ]
            if not prices:
                continue
            latest = max(prices, key=lambda p: str(p.get("valid_from") or p.get("created_at") or ""))
            price = _dec(latest.get("price"))
            target = _dec(rule.get("target_price"))
            if not _matches(price, str(rule.get("operator") or "lt"), target):
                continue
            cooldown_h = float(rule.get("cooldown_hours") or 24)
            last = next(
                (
                    a
                    for a in bag.get("alert") or []
                    if str(a.get("rule_id")) == str(rule.get("id")) and not a.get("archived_at")
                ),
                None,
            )
            if last:
                ts = _parse_dt(last.get("triggered_at") or last.get("created_at"))
                if ts and datetime.now(timezone.utc) - ts < timedelta(hours=cooldown_h):
                    skipped += 1
                    continue
            demo = bool(rule.get("is_demo"))
            title = f"{'[DEMO] ' if demo else ''}Ценовой сигнал: {rule.get('commodity')} {rule.get('operator')} {rule.get('target_price')}"
            alert = await self.create_entity(  # type: ignore[attr-defined]
                org,
                "alert",
                {
                    "title": title,
                    "name": title,
                    "rule_id": rule.get("id"),
                    "commodity": rule.get("commodity"),
                    "price": float(price),
                    "target_price": float(target),
                    "operator": rule.get("operator"),
                    "market_price_id": latest.get("id"),
                    "market_id": latest.get("market_id"),
                    "triggered_at": _now(),
                    "is_demo": demo,
                    "status": "new",
                },
                "platform_owner",
            )
            if not alert.get("ok"):
                continue
            note = await self._emit_notification(
                org,
                title=title,
                entity_type="market_price",
                entity_id=str(latest.get("id")),
                deeplink="/workspace/agro?view=markets",
                extra={
                    "alert_id": alert["item"]["id"],
                    "rule_id": rule.get("id"),
                    "kind": "price_alert",
                    "is_demo": demo,
                },
            )
            created.append({"alert": alert["item"], "notification": note})
        series_alerts = await self._evaluate_series_alerts(org, bag, created)
        created.extend(series_alerts)
        return {"ok": True, "created": len(created), "skipped_cooldown": skipped, "items": created}

    async def _evaluate_series_alerts(
        self, org: str, bag: dict[str, Any], already: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        from services.agro_ops.service import active_only
        from services.agro_ops.analytics import is_numeric_observation

        created: list[dict[str, Any]] = []
        observations: list[dict[str, Any]] = []
        for kind in ("price_observation", "trade_observation", "crop_observation", "weather_observation"):
            observations.extend(active_only(bag.get(kind) or []))
        numeric = [o for o in observations if is_numeric_observation(o) and str(o.get("data_class") or "") != "demo"]
        by_series: dict[str, list[dict[str, Any]]] = {}
        for obs in numeric:
            key = str(obs.get("series_id") or obs.get("source_reference") or obs.get("id"))
            by_series.setdefault(key, []).append(obs)

        async def _fire(title: str, extra: dict[str, Any], cooldown_h: float = 24) -> None:
            last = next(
                (
                    a
                    for a in bag.get("alert") or []
                    if str(a.get("title")) == title and not a.get("archived_at")
                ),
                None,
            )
            if last:
                ts = _parse_dt(last.get("triggered_at") or last.get("created_at"))
                if ts and datetime.now(timezone.utc) - ts < timedelta(hours=cooldown_h):
                    return
            alert = await self.create_entity(  # type: ignore[attr-defined]
                org,
                "alert",
                {"title": title, "name": title, "triggered_at": _now(), "status": "new", **extra},
                "platform_owner",
            )
            if not alert.get("ok"):
                return
            note = await self._emit_notification(
                org,
                title=title,
                entity_type="alert",
                entity_id=str(alert["item"]["id"]),
                deeplink="/workspace/agro?view=intel",
                extra={"kind": extra.get("kind") or "series_alert", "alert_id": alert["item"]["id"]},
            )
            created.append({"alert": alert["item"], "notification": note})

        for series_id, rows in by_series.items():
            rows.sort(key=lambda r: str(r.get("observed_at") or r.get("published_at") or ""))
            if len(rows) < 2:
                if str(rows[-1].get("weather_risk") or "").upper() == "HIGH" if rows else False:
                    await _fire(
                        f"Погодный риск HIGH: {rows[-1].get('title')}",
                        {"kind": "weather_risk", "series_id": series_id, "commodity": rows[-1].get("commodity")},
                    )
                continue
            prev = rows[-2].get("normalized_value")
            latest = rows[-1].get("normalized_value")
            try:
                prev_f, latest_f = float(prev), float(latest)
            except (TypeError, ValueError):
                continue
            if prev_f == 0:
                continue
            pct = (latest_f - prev_f) / abs(prev_f) * 100
            kind = str(rows[-1].get("series_kind") or "")
            title_base = str(rows[-1].get("title") or series_id)
            if kind == "price" and pct <= -5:
                await _fire(f"Цена упала {pct:.1f}%: {title_base}", {"kind": "price_drop", "pct": pct, "series_id": series_id})
            if kind == "trade" and abs(pct) >= 10:
                await _fire(f"Экспорт/торговля изменились {pct:.1f}%: {title_base}", {"kind": "export_change", "pct": pct, "series_id": series_id})
            if kind in {"production", "yield", "area"} and abs(pct) >= 5:
                await _fire(f"Оценка производства изменилась {pct:.1f}%: {title_base}", {"kind": "production_change", "pct": pct, "series_id": series_id})
            if str(rows[-1].get("weather_risk") or "").upper() == "HIGH":
                await _fire(f"Погодный риск HIGH: {title_base}", {"kind": "weather_risk", "series_id": series_id})
        for obs in numeric:
            if obs.get("provider_id") == "usda_wasde" and obs.get("title"):
                await _fire(f"Новый WASDE / USDA материал: {obs.get('title')}", {"kind": "wasde_release", "provider_id": "usda_wasde"})
                break
        return created

    async def evaluate_reminders(self, organization_id: str | None = None, role: str | None = "platform_owner") -> dict[str, Any]:
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        sent = 0
        today = datetime.now(timezone.utc).date()
        for ev in active_only(bag.get("calendar") or []):
            days = ev.get("remind_before_days")
            if days in (None, ""):
                continue
            if ev.get("reminder_sent"):
                continue
            start = _parse_dt(ev.get("starts_at"))
            if not start:
                continue
            remind_on = start.date() - timedelta(days=int(days))
            if today < remind_on:
                continue
            title = f"Напоминание: {ev.get('title')}"
            await self._emit_notification(
                org,
                title=title,
                entity_type="calendar",
                entity_id=str(ev.get("id")),
                deeplink="/workspace/agro?view=calendar",
                extra={"kind": "reminder", "calendar_id": ev.get("id"), "is_demo": bool(ev.get("is_demo"))},
            )
            await self.update_entity(org, "calendar", str(ev["id"]), {"reminder_sent": True}, "platform_owner")  # type: ignore[attr-defined]
            sent += 1
        for ev in self.contract_expiry_events(active_only(bag.get("contract") or [])):  # type: ignore[attr-defined]
            key = f"expiry_{ev.get('id')}_{ev.get('bucket')}"
            already = next(
                (
                    n
                    for n in bag.get("notification") or []
                    if str(n.get("expiry_key") or (n.get("payload") or n.get("extra") or {}).get("expiry_key") or "") == key
                ),
                None,
            )
            if already:
                continue
            await self._emit_notification(
                org,
                title=f"Истекает договор: {ev.get('title')} ({ev.get('days_left')} дн.)",
                entity_type="contract",
                entity_id=str(ev.get("id") or ""),
                deeplink="/workspace/agro?view=contracts",
                extra={"kind": "contract_expiry", "expiry_key": key, "days_left": ev.get("days_left")},
            )
            sent += 1
        return {"ok": True, "sent": sent}

    async def set_calendar_reminder(
        self, organization_id: str, event_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "tasks")
        if denied:
            return denied
        days = body.get("days_before")
        if days in (None, ""):
            return {"ok": False, "error": "validation", "message_ru": "Укажите за сколько дней напомнить"}
        return await self.update_entity(  # type: ignore[attr-defined]
            organization_id,
            "calendar",
            event_id,
            {"remind_before_days": int(days), "reminder_sent": False},
            role,
        )

    async def notification_action(
        self, organization_id: str, notification_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        action = str(body.get("action") or "").strip()
        if action == "open":
            denied = require(role, "get")
        elif action == "disable_rule":
            denied = require(role, "edit")
        else:
            denied = require(role, "tasks")
        if denied:
            return denied
        from services.agro_ops.service import _org

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        note = next((n for n in self._bag(org).get("notification") or [] if str(n.get("id")) == str(notification_id)), None)  # type: ignore[attr-defined]
        if not note:
            return {"ok": False, "error": "not_found", "message_ru": "Уведомление не найдено"}
        if action == "open":
            await self.update_entity(org, "notification", notification_id, {"status": "opened", "opened_at": _now()}, role)  # type: ignore[attr-defined]
            linked = None
            et, eid = note.get("entity_type") or note.get("kind"), note.get("entity_id")
            if et and eid and et in self._bag(org):  # type: ignore[attr-defined]
                linked = next((x for x in self._bag(org)[et] if str(x.get("id")) == str(eid)), None)  # type: ignore[attr-defined]
            return {"ok": True, "action": "open", "item": {**note, "status": "opened"}, "linked": linked, "deeplink": note.get("deeplink")}
        if action == "mark_read":
            updated = await self.update_entity(org, "notification", notification_id, {"status": "read", "read_at": _now()}, role)  # type: ignore[attr-defined]
            return {"ok": True, "action": "mark_read", "item": updated.get("item")}
        if action == "snooze":
            hours = int(body.get("hours") or 24)
            until = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
            updated = await self.update_entity(org, "notification", notification_id, {"status": "snoozed", "snoozed_until": until}, role)  # type: ignore[attr-defined]
            return {"ok": True, "action": "snooze", "item": updated.get("item")}
        if action == "create_task":
            title = str(body.get("title") or note.get("title") or "Проверить сигнал")
            task = await self.create_entity(  # type: ignore[attr-defined]
                org,
                "task",
                {
                    "title": title,
                    "owner": body.get("owner") or normalize_role(role),
                    "due_at": body.get("deadline") or body.get("due_at"),
                    "deadline": body.get("deadline") or body.get("due_at"),
                    "priority": body.get("priority") or "medium",
                    "entity_type": note.get("entity_type") or note.get("kind"),
                    "entity_id": note.get("entity_id"),
                    "notification_id": notification_id,
                    "alert_id": note.get("alert_id"),
                    "shipment_id": note.get("shipment_id"),
                    "deal_id": note.get("deal_id"),
                    "counterparty_id": note.get("counterparty_id"),
                },
                role,
            )
            return {"ok": True, "action": "create_task", "item": task.get("item")}
        if action == "add_calendar":
            ev = await self.create_entity(  # type: ignore[attr-defined]
                org,
                "calendar",
                {
                    "title": body.get("title") or note.get("title") or "Событие из уведомления",
                    "starts_at": body.get("starts_at") or _now(),
                    "event_type": body.get("event_type") or "task",
                    "entity_type": note.get("entity_type"),
                    "entity_id": note.get("entity_id"),
                    "notification_id": notification_id,
                    "deal_id": note.get("deal_id"),
                    "shipment_id": note.get("shipment_id"),
                },
                role,
            )
            return {"ok": True, "action": "add_calendar", "item": ev.get("item")}
        if action == "disable_rule":
            rule_id = note.get("rule_id") or body.get("rule_id")
            if not rule_id:
                return {"ok": False, "error": "validation", "message_ru": "У уведомления нет связанного правила"}
            updated = await self.update_entity(org, "alert_rule", str(rule_id), {"active": False}, role)  # type: ignore[attr-defined]
            return {"ok": True, "action": "disable_rule", "item": updated.get("item")}
        return {"ok": False, "error": "validation", "message_ru": "Неизвестное действие уведомления"}

    async def create_task_from_entity(
        self, organization_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "tasks")
        if denied:
            return denied
        title = str(body.get("title") or "").strip()
        if not title:
            entity = str(body.get("entity_type") or "объект")
            num = str(body.get("entity_id") or body.get("shipment_id") or "")[:8]
            title = f"Проверить поставку №{num}" if entity in {"shipment", "delivery"} else f"Проверить {entity}"
        return await self.create_entity(  # type: ignore[attr-defined]
            organization_id,
            "task",
            {
                "title": title,
                "owner": body.get("owner") or normalize_role(role),
                "due_at": body.get("deadline") or body.get("due_at"),
                "deadline": body.get("deadline") or body.get("due_at"),
                "priority": body.get("priority") or "medium",
                "entity_type": body.get("entity_type"),
                "entity_id": body.get("entity_id"),
                "shipment_id": body.get("shipment_id"),
                "deal_id": body.get("deal_id"),
                "alert_id": body.get("alert_id"),
                "counterparty_id": body.get("counterparty_id"),
                "field_id": body.get("field_id"),
                "work_id": body.get("work_id"),
                "analysis_id": body.get("analysis_id"),
                "commodity": body.get("commodity"),
            },
            role,
        )

    async def _emit_notification(
        self,
        org: str,
        *,
        title: str,
        entity_type: str,
        entity_id: str,
        deeplink: str,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        extra = extra or {}
        note = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "title": title,
            "kind": extra.get("kind") or entity_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "deeplink": deeplink,
            "channel": "in_app",
            "status": "new",
            "created_at": _now(),
            **extra,
        }
        saved = await self._persist("notification", note)  # type: ignore[attr-defined]
        self._bag(org)["notification"].insert(0, saved)  # type: ignore[attr-defined]
        return saved

    async def bootstrap_demo(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.agro_ops.service import _org, active_only

        org = _org(organization_id)
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        existing = next((s for s in active_only(self._bag(org).get("settings") or []) if s.get("demo_loaded")), None)  # type: ignore[attr-defined]
        if existing:
            return {"ok": True, "already": True, "demo_mode": True, "message_ru": "Демо AGRO уже загружено", "item": existing}

        async def make(kind: str, body: dict[str, Any]) -> dict[str, Any]:
            body = {**body, "is_demo": True}
            res = await self.create_entity(org, kind, body, role)  # type: ignore[attr-defined]
            return res.get("item") or {}

        crop = await make("crop", {"name": "Пшеница", "title": "[DEMO] Пшеница"})
        supplier = await make("counterparty", {"name": "[DEMO] ООО Поставщик", "types": ["supplier"]})
        buyer = await make("counterparty", {"name": "[DEMO] ООО Покупатель", "types": ["buyer"]})
        avail = await make(
            "availability",
            {"commodity": "Пшеница", "crop_id": crop.get("id"), "quantity": 500, "counterparty_id": supplier.get("id"), "region": "Одесская обл."},
        )
        demand = await make(
            "demand",
            {"commodity": "Пшеница", "crop_id": crop.get("id"), "quantity": 800, "counterparty_id": buyer.get("id")},
        )
        ship = await make(
            "shipment",
            {
                "title": "[DEMO] Поставка пшеницы 300 т",
                "quantity": 300,
                "crop": "Пшеница",
                "counterparty_id": buyer.get("id"),
                "deadline_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        market = await make("market", {"name": "[DEMO] Одесса", "market_type": "manual"})
        rule = await make(
            "alert_rule",
            {"commodity": "Пшеница", "operator": "lt", "target_price": 8500, "currency": "UAH", "name": "[DEMO] Пшеница < 8500"},
        )
        await self._emit_notification(
            org,
            title="[DEMO] Демо-сигнал AGRO — не рыночные данные",
            entity_type="alert_rule",
            entity_id=str(rule.get("id") or ""),
            deeplink="/workspace/agro?view=notifications",
            extra={"kind": "demo", "is_demo": True, "rule_id": rule.get("id")},
        )
        settings = await make("settings", {"name": "demo", "demo_loaded": True, "title": "[DEMO] AGRO seed"})
        return {
            "ok": True,
            "already": False,
            "demo_mode": True,
            "message_ru": "DEMO AGRO загружено. Все демо-строки помечены [DEMO] и исключены из производственного анализа.",
            "item": {
                "crop": crop,
                "availability": avail,
                "demand": demand,
                "shipment": ship,
                "market": market,
                "alert_rule": rule,
                "settings": settings,
            },
        }
