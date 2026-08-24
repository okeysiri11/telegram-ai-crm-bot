"""AUTO 1.4 live Telegram ops — mixin for AutoOpsService.

Reuses the existing ADOS bot. Authorizes company staff, never a public VIN bot.
"""

from __future__ import annotations

import base64
import uuid
from datetime import datetime, timezone
from typing import Any

from services.auto_ops.documents_catalog import SALE_PACKAGE_ITEMS
from services.auto_ops.rbac import can, normalize_role, require
from services.auto_ops.telegram_auth import (
    DENIED_TEXT_RU,
    callback_token,
    command_allowed,
    idempotency_key,
    looks_like_intercept,
    menu_for_role,
    parse_auto_command,
    verify_callback_owner,
)

TELEGRAM_BAG_KEYS = ("telegram_members", "telegram_outbox")

_RUNTIME: dict[str, Any] = {
    "mode": "polling",
    "webhook_url": "",
    "started_at": None,
    "last_update_at": None,
    "last_error": None,
    "duplicate_conflict": False,
}


def telegram_runtime() -> dict[str, Any]:
    return dict(_RUNTIME)


def note_telegram_update(*, error: str | None = None) -> None:
    _RUNTIME["last_update_at"] = datetime.now(timezone.utc).isoformat()
    if error:
        _RUNTIME["last_error"] = error
    else:
        _RUNTIME["last_error"] = None


def note_telegram_mode(*, mode: str, webhook_url: str = "", duplicate_conflict: bool = False) -> None:
    _RUNTIME["mode"] = mode if mode in {"polling", "webhook"} else "polling"
    _RUNTIME["webhook_url"] = webhook_url or ""
    _RUNTIME["duplicate_conflict"] = bool(duplicate_conflict)
    if not _RUNTIME.get("started_at"):
        _RUNTIME["started_at"] = datetime.now(timezone.utc).isoformat()


def reset_telegram_runtime_for_tests() -> None:
    _RUNTIME.update(
        {
            "mode": "polling",
            "webhook_url": "",
            "started_at": None,
            "last_update_at": None,
            "last_error": None,
            "duplicate_conflict": False,
        }
    )


class AutoOpsTelegramMixin:
    """Telegram members, inbound commands, summaries, bot status."""

    def telegram_user_bound(self, telegram_id: int) -> bool:
        return self._member_by_telegram(int(telegram_id)) is not None

    def _member_by_telegram(self, telegram_id: int) -> dict[str, Any] | None:
        tid = str(int(telegram_id))
        for org, bag in getattr(self, "_mem", {}).items():
            for row in bag.get("telegram_members") or []:
                if str(row.get("telegram_id")) == tid and row.get("enabled") is not False:
                    return {**row, "organization_id": org}
        return None

    async def upsert_telegram_member(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "admin")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        try:
            tid = int(body.get("telegram_id"))
        except (TypeError, ValueError):
            return {"ok": False, "error": "validation", "message_ru": "Укажите telegram_id сотрудника"}
        member_role = normalize_role(body.get("role") or "auto_manager")
        if member_role == "denied":
            return {"ok": False, "error": "validation", "message_ru": "Клиенты не добавляются в закрытый бот Авто"}
        existing = next((m for m in self._bag(org)["telegram_members"] if str(m.get("telegram_id")) == str(tid)), None)
        other = self._member_by_telegram(tid)
        if other and str(other.get("organization_id")) != org:
            return {"ok": False, "error": "conflict", "message_ru": "Этот Telegram уже привязан к другой организации"}
        item = existing or {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "telegram_id": tid,
            "created_at": self._now(),
        }
        item.update(
            {
                "role": member_role,
                "username": body.get("username"),
                "label": body.get("label") or body.get("name"),
                "enabled": False if body.get("enabled") is False else True,
                "updated_at": self._now(),
            }
        )
        if existing is None:
            saved = await self._persist("telegram_member", item)
            self._bag(org)["telegram_members"].insert(0, saved)
        else:
            saved = item
            await self._persist_update("telegram_member", str(item["id"]), item)
        await self._audit(
            organization_id=org,
            action="telegram_member_upserted",
            entity_type="telegram_member",
            entity_id=str(saved["id"]),
            role=role,
            actor_id=actor_id,
            new_value={"telegram_id": tid, "role": member_role},
        )
        return {"ok": True, "item": saved}

    async def list_telegram_members(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "admin")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        items = list(self._bag(org)["telegram_members"])
        return {"ok": True, "items": items, "total": len(items)}

    async def telegram_bot_status(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "admin")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        today = str(self._now())[:10]
        sent_today = sum(1 for o in self._bag(org)["telegram_outbox"] if str(o.get("created_at") or "")[:10] == today)
        members = [m for m in self._bag(org)["telegram_members"] if m.get("enabled") is not False]
        runtime = telegram_runtime()
        return {
            "ok": True,
            "mode": runtime.get("mode") or "polling",
            "webhook_url": runtime.get("webhook_url") or "",
            "last_successful_update": runtime.get("last_update_at"),
            "last_error": runtime.get("last_error"),
            "started_at": runtime.get("started_at"),
            "duplicate_conflict": bool(runtime.get("duplicate_conflict")),
            "authorized_users": [{"telegram_id": m.get("telegram_id"), "role": m.get("role"), "label": m.get("label")} for m in members],
            "authorized_count": len(members),
            "notifications_sent_today": sent_today,
            "entrypoint": "main.py",
            "new_bot": False,
        }

    def _callback_store(self) -> dict[str, dict[str, Any]]:
        store = getattr(self, "_tg_callbacks", None)
        if store is None:
            store = {}
            self._tg_callbacks = store
        return store

    def _idem_store(self) -> dict[str, dict[str, Any]]:
        store = getattr(self, "_tg_idem", None)
        if store is None:
            store = {}
            self._tg_idem = store
        return store

    def _bind_callback(self, telegram_id: int, action: str, entity_id: str = "", payload: dict[str, Any] | None = None) -> str:
        token = callback_token(telegram_id, action, entity_id)
        self._callback_store()[token] = {
            "owner": int(telegram_id),
            "action": action,
            "entity_id": entity_id,
            "payload": payload or {},
        }
        return token

    async def _record_outbox(self, org: str, *, telegram_id: int, kind: str, text: str, dedupe: str | None = None) -> dict[str, Any]:
        if dedupe:
            for row in self._bag(org)["telegram_outbox"]:
                if row.get("dedupe_key") == dedupe:
                    return row
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "telegram_id": int(telegram_id),
            "kind": kind,
            "text": text[:2000],
            "dedupe_key": dedupe,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        saved = await self._persist("telegram_outbox", item)
        self._bag(org)["telegram_outbox"].insert(0, saved)
        return saved

    def _buttons(self, telegram_id: int, role: str | None) -> list[list[dict[str, str]]]:
        rows: list[list[dict[str, str]]] = []
        row: list[dict[str, str]] = []
        for item in menu_for_role(role):
            token = self._bind_callback(telegram_id, item["id"], "")
            row.append({"text": item["label_ru"], "callback_data": token})
            if len(row) == 3:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        return rows

    async def handle_telegram_inbound(
        self,
        *,
        telegram_id: int,
        text: str = "",
        extra: dict[str, Any] | None = None,
        callback_data: str | None = None,
    ) -> dict[str, Any]:
        note_telegram_update()
        extra = extra or {}
        member = self._member_by_telegram(int(telegram_id))
        if callback_data:
            return await self._handle_callback(int(telegram_id), callback_data, member)
        if not member:
            if looks_like_intercept(text) and parse_auto_command(text)["cmd"] != "menu":
                return {"ok": False, "error": "forbidden", "message_ru": DENIED_TEXT_RU, "intercepted": True}
            if parse_auto_command(text)["cmd"] == "menu" and (text or "").strip().lower().startswith("/auto"):
                return {"ok": False, "error": "forbidden", "message_ru": DENIED_TEXT_RU, "intercepted": True}
            return {"ok": False, "error": "forbidden", "message_ru": DENIED_TEXT_RU, "intercepted": False}
        org = str(member["organization_id"])
        role = str(member.get("role") or "auto_manager")
        await self.ensure_hydrated(org)
        parsed = parse_auto_command(text)
        cmd = parsed["cmd"] or "menu"
        pending = getattr(self, "_tg_upload_pending", {}).get(int(telegram_id))
        if pending and not str(text or "").startswith("/") and not extra.get("content_bytes"):
            extra = {**extra, "pending": pending}
            parsed = {"cmd": "doc", "args": (text or "").split(), "rest": text or ""}
            cmd = "doc"
        if not command_allowed(role, cmd):
            return {"ok": False, "error": "forbidden", "message_ru": f"Роль не может выполнить команду: {cmd}", "intercepted": True}
        key = idempotency_key(int(telegram_id), text + ("|" + str(sorted((extra or {}).items())) if cmd in {"customspay", "customsdoc", "customsstatus"} else ""))
        mutating = cmd in {"expense", "pay", "task", "photo", "doc", "docs", "reserve", "vehicle_status", "customspay", "customsdoc", "customsstatus"}
        if mutating:
            prev = self._idem_store().get(key)
            if prev:
                return {**prev, "duplicate": True, "message_ru": prev.get("message_ru") or "Повтор. Операция уже выполнена."}
        result = await self._dispatch_telegram(org, role, int(telegram_id), parsed, extra)
        result["intercepted"] = True
        result["organization_id"] = org
        result["role"] = role
        result["keyboard"] = result.get("keyboard") or self._buttons(int(telegram_id), role)
        if mutating and result.get("ok"):
            self._idem_store()[key] = {k: result[k] for k in result if k != "keyboard"}
        await self._audit(
            organization_id=org,
            action=f"telegram_{cmd}",
            entity_type="telegram",
            entity_id=str(telegram_id),
            role=role,
            actor_id=str(telegram_id),
            new_value={"cmd": cmd, "ok": result.get("ok")},
        )
        return result

    async def _handle_callback(self, telegram_id: int, callback_data: str, member: dict[str, Any] | None) -> dict[str, Any]:
        stored = self._callback_store().get(callback_data)
        if not stored:
            return {"ok": False, "error": "forbidden", "message_ru": "Кнопка недействительна", "intercepted": True}
        if not verify_callback_owner(telegram_id, stored.get("owner")):
            return {"ok": False, "error": "forbidden", "message_ru": "Эта кнопка принадлежит другому сотруднику", "intercepted": True}
        if not member:
            return {"ok": False, "error": "forbidden", "message_ru": DENIED_TEXT_RU, "intercepted": True}
        action = str(stored.get("action") or "menu")
        if action == "customspay_confirm":
            return await self.handle_telegram_inbound(
                telegram_id=telegram_id,
                text=f"/customspay {stored.get('vin') or ''}",
                extra={"confirm": True, "expense_id": stored.get("entity_id"), "vin": stored.get("vin")},
            )
        if action == "customspay_charge":
            return await self.handle_telegram_inbound(
                telegram_id=telegram_id,
                text=f"/customspay {stored.get('vin') or ''}",
                extra={"category": stored.get("category"), "vin": stored.get("vin")},
            )
        if action == "customsstatus":
            return await self.handle_telegram_inbound(
                telegram_id=telegram_id,
                text=f"/customsstatus {stored.get('vin') or ''}",
                extra={"status": stored.get("status"), "vin": stored.get("vin")},
            )
        if action == "customsdoc_type":
            return await self.handle_telegram_inbound(
                telegram_id=telegram_id,
                text=f"/customsdoc {stored.get('vin') or ''}",
                extra={"document_type": stored.get("document_type"), "vin": stored.get("vin")},
            )
        text_map = {
            "vin": "/vin",
            "vehicles": "/vin",
            "logistics": "/logistics",
            "customs": "/customs",
            "clients": "/client",
            "deals": "/deal",
            "pay": "/pay",
            "expense": "/expense",
            "tasks": "/task",
            "report": "/report",
            "analytics": "/analytics",
            "risks": "/risks",
            "cashflow": "/cashflow",
            "botstatus": "/botstatus",
            "members": "/botstatus",
            "reserve": "/reserve",
            "docs": "/docs",
            "doc": "/doc",
            "photo": "/photo",
            "sale": "/sale",
        }
        hint = text_map.get(action, "/auto")
        entity = str(stored.get("entity_id") or "")
        if entity and action in {"docs", "doc"}:
            hint = f"{hint} {entity}".strip()
        return await self.handle_telegram_inbound(telegram_id=telegram_id, text=hint)

    async def _dispatch_telegram(self, org: str, role: str, telegram_id: int, parsed: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
        cmd = parsed["cmd"]
        args = parsed.get("args") or []
        rest = parsed.get("rest") or ""
        if cmd == "menu":
            return {
                "ok": True,
                "message_ru": f"Авто OS. Роль: {normalize_role(role)}. Новый бот не строится — вы в существующем боте ADOS.",
            }
        if cmd == "botstatus":
            status = await self.telegram_bot_status(org, role)
            if not status.get("ok"):
                return status
            return {
                "ok": True,
                "item": status,
                "message_ru": (
                    f"Режим: {status['mode']}\n"
                    f"Последнее обновление: {status['last_successful_update'] or '—'}\n"
                    f"Последняя ошибка: {status['last_error'] or 'нет'}\n"
                    f"Сотрудников: {status['authorized_count']}\n"
                    f"Уведомлений сегодня: {status['notifications_sent_today']}"
                ),
            }
        if cmd == "report":
            return await self._tg_report(org, role, telegram_id)
        if cmd == "analytics":
            return await self._tg_analytics(org, role)
        if cmd == "risks":
            return await self._tg_risks(org, role)
        if cmd == "cashflow":
            return await self._tg_cashflow(org, role)
        if cmd in {"vin", "vehicles"}:
            return await self._tg_vin(org, role, args, rest)
        if cmd == "logistics":
            return await self._tg_logistics(org, role, args)
        if cmd == "container":
            return await self._tg_container(org, role, args)
        if cmd == "eta":
            return await self._tg_eta(org, role, args)
        if cmd in {"customs", "vat", "broker"}:
            return await self._tg_customs(org, role, args)
        if cmd == "customspay":
            return await self._tg_customs_pay(org, role, args, extra, telegram_id)
        if cmd == "customsdoc":
            return await self._tg_customs_doc(org, role, args, extra, telegram_id)
        if cmd == "customsstatus":
            return await self._tg_customs_status(org, role, args, extra, telegram_id)
        if cmd == "client":
            return await self._tg_client(org, role, rest)
        if cmd in {"deal", "sale"}:
            return await self._tg_deal(org, role, args)
        if cmd == "expense":
            return await self._tg_expense(org, role, args, extra, telegram_id)
        if cmd == "pay":
            return await self._tg_pay(org, role, args, extra, telegram_id)
        if cmd == "task":
            return await self._tg_task(org, role, args, rest, extra)
        if cmd == "photo":
            return await self._tg_photo(org, role, args, extra, telegram_id)
        if cmd == "doc":
            return await self._tg_doc(org, role, args, extra, telegram_id)
        if cmd == "docs":
            return await self._tg_docs(org, role, args, extra, telegram_id)
        if cmd == "reserve":
            return await self._tg_reserve(org, role, args, extra)
        if cmd == "vehicle_status":
            return await self._tg_vehicle_status(org, role, args)
        return {"ok": False, "error": "validation", "message_ru": "Неизвестная команда Авто"}

    async def _find_vehicle_by_vin(self, org: str, role: str | None, vin: str) -> dict[str, Any] | None:
        listed = await self.list_vehicles(org, role, {"q": vin})
        items = listed.get("items") or []
        needle = (vin or "").strip().upper()
        for row in items:
            if str(row.get("vin") or "").upper() == needle or needle in str(row.get("vin") or "").upper():
                return row
        return items[0] if len(items) == 1 else None

    async def _tg_vin(self, org: str, role: str, args: list[str], rest: str) -> dict[str, Any]:
        q = (args[0] if args else rest).strip()
        if not q:
            listed = await self.list_vehicles(org, role, {})
            lines = [f"{v.get('vin')} · {v.get('title') or v.get('manufacturer')} · {v.get('status_ru') or v.get('status')}" for v in (listed.get("items") or [])[:8]]
            return {"ok": True, "items": listed.get("items") or [], "message_ru": "Автомобили:\n" + ("\n".join(lines) if lines else "Парк пуст.")}
        found = await self.search_auto(org, role, {"q": q})
        vehicle = await self._find_vehicle_by_vin(org, role, q)
        if not vehicle:
            return {"ok": False, "error": "not_found", "message_ru": "VIN не найден в этой организации"}
        detail = await self.get_vehicle(org, str(vehicle["id"]), role)
        item = detail.get("item") or vehicle
        return {
            "ok": True,
            "item": item,
            "search": found.get("items") or [],
            "message_ru": (
                f"{item.get('title') or item.get('manufacturer')} {item.get('model') or ''}\n"
                f"VIN: {item.get('vin')}\n"
                f"Статус: {item.get('status_ru') or item.get('status')}\n"
                f"Где: {item.get('location_current') or '—'}"
            ),
        }

    async def _tg_logistics(self, org: str, role: str, args: list[str]) -> dict[str, Any]:
        vin = args[0] if args else ""
        vehicle = await self._find_vehicle_by_vin(org, role, vin) if vin else None
        if vin and not vehicle:
            return {"ok": False, "error": "not_found", "message_ru": "VIN не найден в этой организации"}
        vid = str(vehicle["id"]) if vehicle else ""
        block = self.vehicle_logistics_block(org, vid, role) if vid else {"message_ru": "Укажите VIN: /logistics <VIN>"}
        ship = (block or {}).get("shipment") or {}
        return {
            "ok": True,
            "item": block,
            "message_ru": (
                f"Логистика {vin or ''}\n"
                f"Этап: {ship.get('status_ru') or ship.get('status') or 'нет перевозки'}\n"
                f"Контейнер: {((block or {}).get('container') or {}).get('container_number') or '—'}\n"
                f"ETA: {ship.get('eta') or ship.get('current_eta') or 'введено вручную / нет'}"
            ),
        }

    async def _tg_container(self, org: str, role: str, args: list[str]) -> dict[str, Any]:
        number = args[0] if args else ""
        if not number:
            return {"ok": False, "error": "validation", "message_ru": "Укажите номер контейнера"}
        found = await self.search_auto(org, role, {"q": number})
        hits = [h for h in (found.get("items") or []) if h.get("kind") == "container"]
        if not hits:
            return {"ok": False, "error": "not_found", "message_ru": "Контейнер не найден в этой организации"}
        return {"ok": True, "items": hits, "message_ru": f"Контейнер {hits[0].get('title')}"}

    async def _tg_eta(self, org: str, role: str, args: list[str]) -> dict[str, Any]:
        return await self._tg_logistics(org, role, args)

    async def _tg_customs(self, org: str, role: str, args: list[str]) -> dict[str, Any]:
        vin = args[0] if args else ""
        vehicle = await self._find_vehicle_by_vin(org, role, vin) if vin else None
        if not vehicle:
            return {"ok": False, "error": "not_found", "message_ru": "VIN не найден в этой организации"}
        block = self.vehicle_customs_block(org, str(vehicle["id"]), role)
        case = (block or {}).get("case") or {}
        return {
            "ok": True,
            "item": block,
            "message_ru": (
                f"Растаможка {vin}\n"
                f"Статус: {case.get('status_ru') or case.get('status') or 'дела нет'}\n"
                f"НДС/платежи — только из записи организации, не калькулятор Гостаможни."
            ),
        }

    async def _tg_customs_pay(self, org: str, role: str, args: list[str], extra: dict[str, Any], telegram_id: int) -> dict[str, Any]:
        from services.auto_ops.customs_catalog import CUSTOMS_CHARGE_CATEGORIES
        from services.auto_ops.telegram_auth import callback_token

        vin = str(extra.get("vin") or (args[0] if args else "")).strip()
        vehicle = await self._find_vehicle_by_vin(org, role, vin) if vin else None
        if not vehicle:
            return {"ok": False, "error": "validation", "message_ru": "Формат: /customspay VIN"}
        block = self.vehicle_customs_block(org, str(vehicle["id"]), role)
        case = (block or {}).get("case") or {}
        if not case.get("id"):
            return {"ok": False, "error": "not_found", "message_ru": "Дело растаможки не найдено"}
        if extra.get("confirm") and extra.get("expense_id"):
            return await self.confirm_customs_payment(org, str(case["id"]), str(extra.get("expense_id")), extra, role, str(telegram_id))
        category = str(extra.get("category") or extra.get("charge") or (args[1] if len(args) > 1 else "")).upper()
        amount = extra.get("amount") if extra.get("amount") not in (None, "") else (args[2] if len(args) > 2 else None)
        if not category:
            keyboard: list[list[dict[str, str]]] = []
            row: list[dict[str, str]] = []
            for cid, label in CUSTOMS_CHARGE_CATEGORIES[:6]:
                token = callback_token(int(telegram_id), f"pay:{cid}", vin)
                self._callback_store()[token] = {"owner": int(telegram_id), "action": "customspay_charge", "category": cid, "vin": vin}
                row.append({"text": label, "callback_data": token})
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
            return {"ok": True, "item": case, "message_ru": f"Выберите статью платежа для {vin}. Подтверждение — отдельный шаг.", "keyboard": keyboard}
        if amount in (None, ""):
            return {"ok": False, "error": "validation", "message_ru": "Укажите сумму: /customspay VIN + статья + сумма"}
        created = await self.add_customs_payment(
            org,
            str(case["id"]),
            {
                "category": category,
                "amount": amount,
                "currency": extra.get("currency") or "UAH",
                "comment": extra.get("comment") or extra.get("description"),
                "document_id": extra.get("document_id"),
            },
            role,
            str(telegram_id),
        )
        if not created.get("ok"):
            return created
        token = callback_token(int(telegram_id), "payok", str(created["item"]["id"]))
        self._callback_store()[token] = {"owner": int(telegram_id), "action": "customspay_confirm", "entity_id": created["item"]["id"], "vin": vin}
        return {
            "ok": True,
            "item": created.get("item"),
            "confirmed": False,
            "message_ru": f"Платёж {amount} {category} записан как запланированный. Нажмите «Подтвердить», чтобы провести оплату.",
            "keyboard": [[{"text": "Подтвердить платёж", "callback_data": token}]],
        }

    async def _tg_customs_doc(self, org: str, role: str, args: list[str], extra: dict[str, Any], telegram_id: int) -> dict[str, Any]:
        vin = str(extra.get("vin") or (args[0] if args else "")).strip()
        dtype = str(extra.get("document_type") or extra.get("type") or (args[1] if len(args) > 1 else "") or "customs_declaration")
        vehicle = await self._find_vehicle_by_vin(org, role, vin) if vin else None
        if not vehicle:
            return {"ok": False, "error": "validation", "message_ru": "Формат: /customsdoc VIN тип"}
        block = self.vehicle_customs_block(org, str(vehicle["id"]), role)
        case = (block or {}).get("case") or {}
        customs_id = str(case.get("id") or "") or None
        raw = extra.get("content_bytes")
        if raw is None and extra.get("content_base64"):
            try:
                raw = base64.b64decode(extra.get("content_base64"))
            except Exception:
                raw = None
        pending_store = getattr(self, "_tg_upload_pending", None)
        if pending_store is None:
            self._tg_upload_pending = {}
            pending_store = self._tg_upload_pending
        pending = extra.get("pending") or pending_store.get(int(telegram_id))
        if pending and pending.get("content_bytes") and not raw:
            raw = pending.get("content_bytes")
            extra = {**extra, "filename": pending.get("filename"), "mime_type": pending.get("mime_type")}
            pending_store.pop(int(telegram_id), None)
        if raw:
            uploaded = await self.upload_file(
                org,
                filename=str(extra.get("filename") or extra.get("file_name") or f"{dtype}.pdf"),
                mime_type=str(extra.get("mime_type") or "application/pdf"),
                data=raw if isinstance(raw, (bytes, bytearray)) else bytes(raw),
                entity_type="vehicle",
                entity_id=str(vehicle["id"]),
                role=role,
                uploaded_by=str(telegram_id),
                document_type=dtype,
                customs_id=customs_id,
            )
            if not uploaded.get("ok"):
                return uploaded
            item = uploaded.get("linked") or uploaded.get("item") or {}
            return {"ok": True, "item": item, "message_ru": f"Документ {dtype} сохранён в карточку и дело растаможки {vin}"}
        created = await self.create_document(
            org,
            {
                "vehicle_id": vehicle["id"],
                "customs_id": customs_id,
                "document_type": dtype,
                "file_name": extra.get("filename") or f"{dtype}.pdf",
                "owner_type": "vehicle",
                "source": "TELEGRAM",
            },
            role,
            str(telegram_id),
        )
        if not created.get("ok"):
            return created
        return {"ok": True, "item": created.get("item"), "message_ru": f"Документ {dtype} привязан к {vin} и делу растаможки"}

    async def _tg_customs_status(self, org: str, role: str, args: list[str], extra: dict[str, Any], telegram_id: int) -> dict[str, Any]:
        from services.auto_ops.customs_catalog import CASE_STATUS_LABELS, allowed_next_statuses, normalize_case_status, transition_allowed
        from services.auto_ops.telegram_auth import callback_token

        if not (can(role, "edit") or can(role, "create")):
            return require(role, "edit") or {"ok": False, "error": "forbidden", "message_ru": "Смену этапа растаможки выполняет менеджер или директор"}
        vin = str(extra.get("vin") or (args[0] if args else "")).strip()
        vehicle = await self._find_vehicle_by_vin(org, role, vin) if vin else None
        if not vehicle:
            return {"ok": False, "error": "validation", "message_ru": "Формат: /customsstatus VIN"}
        block = self.vehicle_customs_block(org, str(vehicle["id"]), role)
        case = (block or {}).get("case") or {}
        if not case.get("id"):
            return {"ok": False, "error": "not_found", "message_ru": "Дело растаможки не найдено"}
        current = str(case.get("status") or "")
        target = extra.get("status") or extra.get("stage") or (args[1] if len(args) > 1 else "")
        if target:
            nxt = normalize_case_status(target)
            if not transition_allowed(current, nxt, telegram=True):
                return {
                    "ok": False,
                    "error": "validation",
                    "message_ru": f"Нельзя перейти {CASE_STATUS_LABELS.get(current, current)} → {CASE_STATUS_LABELS.get(nxt, nxt)}",
                }
            updated = await self.update_customs_case(org, str(case["id"]), {"status": nxt, "telegram": True}, role, str(telegram_id))
            return updated if not updated.get("ok") else {"ok": True, "item": updated.get("item"), "message_ru": f"Этап: {CASE_STATUS_LABELS.get(nxt, nxt)}"}
        nxts = allowed_next_statuses(current, telegram=True)
        keyboard = []
        row: list[dict[str, str]] = []
        for st in nxts:
            token = callback_token(int(telegram_id), f"st:{st}", vin)
            self._callback_store()[token] = {"owner": int(telegram_id), "action": "customsstatus", "status": st, "vin": vin}
            row.append({"text": CASE_STATUS_LABELS.get(st, st), "callback_data": token})
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        return {
            "ok": True,
            "item": case,
            "allowed_next": nxts,
            "message_ru": f"Текущий этап: {CASE_STATUS_LABELS.get(current, current)}\nВыберите следующий допустимый этап.",
            "keyboard": keyboard,
        }

    async def _tg_client(self, org: str, role: str, rest: str) -> dict[str, Any]:
        listed = await self.list_clients(org, role)
        items = listed.get("items") or []
        if rest:
            needle = rest.strip().upper()
            items = [c for c in items if needle in f"{c.get('name')} {c.get('phone')}".upper()]
        if not items:
            return {"ok": False, "error": "not_found", "message_ru": "Клиент не найден"}
        c = items[0]
        return {"ok": True, "item": c, "items": items, "message_ru": f"Клиент: {c.get('name')}\nТелефон: {c.get('phone') or '—'}"}

    async def _tg_deal(self, org: str, role: str, args: list[str]) -> dict[str, Any]:
        q = {"vin": args[0]} if args else {}
        listed = await self.list_deals(org, role, q)
        items = listed.get("items") or []
        if not items:
            return {"ok": False, "error": "not_found", "message_ru": "Сделка не найдена"}
        d = items[0]
        ans = d.get("answers") or {}
        return {
            "ok": True,
            "item": d,
            "message_ru": (
                f"Клиент: {ans.get('client')}\n"
                f"Авто: {ans.get('vehicle')}\n"
                f"Этап: {ans.get('stage')}\n"
                f"Оплачено: {ans.get('paid')} · Долг: {ans.get('owed')}\n"
                f"Дальше: {ans.get('next')}"
            ),
        }

    async def _tg_expense(self, org: str, role: str, args: list[str], extra: dict[str, Any], telegram_id: int) -> dict[str, Any]:
        vin = str(extra.get("vin") or (args[0] if args else "")).strip()
        amount = extra.get("amount") if extra.get("amount") not in (None, "") else (args[1] if len(args) > 1 else None)
        category = str(extra.get("category") or (args[2] if len(args) > 2 else "OTHER")).upper()
        vehicle = await self._find_vehicle_by_vin(org, role, vin) if vin else None
        if not vehicle or amount in (None, ""):
            return {"ok": False, "error": "validation", "message_ru": "Формат: /expense VIN сумма категория"}
        created = await self.create_expense(
            org,
            {"vehicle_id": vehicle["id"], "category": category, "amount": amount, "currency": extra.get("currency") or "USD", "payment_status": extra.get("payment_status") or "paid"},
            role,
            str(telegram_id),
        )
        if not created.get("ok"):
            return created
        await self.notify_telegram_staff(
            org, title=f"Расход {amount} {category} · {vin}", entity_type="expense", entity_id=str(created["item"]["id"]), vehicle_id=str(vehicle["id"])
        )
        return {"ok": True, "item": created.get("item"), "message_ru": f"Расход {amount} {category} записан на {vin}"}

    async def _tg_pay(self, org: str, role: str, args: list[str], extra: dict[str, Any], telegram_id: int) -> dict[str, Any]:
        if not can(role, "finance_write"):
            return require(role, "finance_write") or {"ok": False, "error": "forbidden", "message_ru": "Подтверждение платежа — бухгалтер / директор"}
        vin = str(extra.get("vin") or (args[0] if args else "")).strip()
        amount = extra.get("amount") if extra.get("amount") not in (None, "") else (args[1] if len(args) > 1 else None)
        vehicle = await self._find_vehicle_by_vin(org, role, vin) if vin else None
        if not vehicle or amount in (None, ""):
            return {"ok": False, "error": "validation", "message_ru": "Формат: /pay VIN сумма"}
        deals = await self.list_deals(org, role, {"vehicle_id": str(vehicle["id"])})
        deal = (deals.get("items") or [None])[0]
        created = await self.create_receipt(
            org,
            {
                "vehicle_id": vehicle["id"],
                "deal_id": (deal or {}).get("id"),
                "client_id": (deal or {}).get("client_id") or vehicle.get("client_id"),
                "kind": extra.get("kind") or "PARTIAL",
                "amount": amount,
                "currency": extra.get("currency") or "USD",
                "status": extra.get("status") or "confirmed",
                "reference": extra.get("reference") or f"TG-{telegram_id}",
            },
            role,
            str(telegram_id),
        )
        if not created.get("ok"):
            return created
        await self.notify_telegram_staff(
            org, title=f"Платёж {amount} · {vin}", entity_type="receipt", entity_id=str(created["item"]["id"]), vehicle_id=str(vehicle["id"])
        )
        return {"ok": True, "item": created.get("item"), "message_ru": f"Поступление {amount} по {vin} подтверждено"}

    async def _tg_task(self, org: str, role: str, args: list[str], rest: str, extra: dict[str, Any]) -> dict[str, Any]:
        vin = str(extra.get("vin") or (args[0] if args else "")).strip()
        title = str(extra.get("title") or (" ".join(args[1:]) if len(args) > 1 else rest.replace(vin, "", 1).strip()))
        vehicle = await self._find_vehicle_by_vin(org, role, vin) if vin else None
        if not title:
            return {"ok": False, "error": "validation", "message_ru": "Формат: /task VIN текст задачи"}
        created = await self.create_task(org, {"title": title, "vehicle_id": (vehicle or {}).get("id"), "status": extra.get("status") or "open"}, role)
        if not created.get("ok"):
            return created
        if extra.get("complete") and created.get("item"):
            done = await self.complete_task(org, str(created["item"]["id"]), role)
            await self.notify_telegram_staff(org, title=f"Задача закрыта: {title}", entity_type="task", entity_id=str(created["item"]["id"]), vehicle_id=(vehicle or {}).get("id"))
            return {"ok": True, "item": done.get("item"), "message_ru": f"Задача закрыта: {title}"}
        await self.notify_telegram_staff(org, title=f"Задача: {title}", entity_type="task", entity_id=str(created["item"]["id"]), vehicle_id=(vehicle or {}).get("id"))
        return {"ok": True, "item": created.get("item"), "message_ru": f"Задача создана: {title}"}

    async def _tg_photo(self, org: str, role: str, args: list[str], extra: dict[str, Any], telegram_id: int) -> dict[str, Any]:
        vin = str(extra.get("vin") or (args[0] if args else "")).strip()
        vehicle = await self._find_vehicle_by_vin(org, role, vin) if vin else None
        raw = extra.get("content_bytes")
        if extra.get("content_base64") and not raw:
            raw = base64.b64decode(str(extra["content_base64"]))
        if not vehicle or not raw:
            return {"ok": False, "error": "validation", "message_ru": "Пришлите фото с подписью VIN или /photo VIN + файл"}
        uploaded = await self.upload_file(
            org,
            filename=str(extra.get("filename") or "telegram.jpg"),
            mime_type=str(extra.get("mime_type") or "image/jpeg"),
            data=raw,
            entity_type="vehicle",
            entity_id=str(vehicle["id"]),
            role=role,
            uploaded_by=str(telegram_id),
            as_photo=True,
            photo_category=str(extra.get("photo_category") or "OTHER"),
        )
        if not uploaded.get("ok"):
            return uploaded
        linked = uploaded.get("linked") or uploaded.get("item")
        await self.notify_telegram_staff(org, title=f"Фото · {vin}", entity_type="photo", entity_id=str((linked or {}).get("id") or ""), vehicle_id=str(vehicle["id"]))
        return {"ok": True, "item": linked, "message_ru": f"Фото привязано к {vin}"}

    async def _tg_doc(self, org: str, role: str, args: list[str], extra: dict[str, Any], telegram_id: int) -> dict[str, Any]:
        pending_store = getattr(self, "_tg_upload_pending", None)
        if pending_store is None:
            self._tg_upload_pending = {}
            pending_store = self._tg_upload_pending
        pending = extra.get("pending") or pending_store.get(int(telegram_id))
        vin = str(extra.get("vin") or (args[0] if args else "")).strip()
        dtype = str(extra.get("document_type") or (args[1] if len(args) > 1 else "") or "other")
        raw = extra.get("content_bytes")
        if raw is None and extra.get("content_base64"):
            import base64

            try:
                raw = base64.b64decode(extra.get("content_base64"))
            except Exception:
                raw = None
        if raw and not vin:
            pending_store[int(telegram_id)] = {
                "filename": extra.get("filename") or extra.get("file_name") or "telegram.bin",
                "mime_type": extra.get("mime_type") or "application/octet-stream",
                "content_bytes": raw,
            }
            return {"ok": True, "message_ru": "Укажите VIN автомобиля для этого документа"}
        if pending and not vin:
            vin = str(args[0] if args else extra.get("rest") or "").strip()
        vehicle = await self._find_vehicle_by_vin(org, role, vin) if vin else None
        if not vehicle:
            return {"ok": False, "error": "validation", "message_ru": "Формат: /doc VIN тип"}
        if pending and pending.get("content_bytes") and not raw:
            raw = pending.get("content_bytes")
            extra = {**extra, "filename": pending.get("filename"), "mime_type": pending.get("mime_type")}
            pending_store.pop(int(telegram_id), None)
        if raw:
            uploaded = await self.upload_file(
                org,
                filename=str(extra.get("filename") or extra.get("file_name") or f"{dtype}.pdf"),
                mime_type=str(extra.get("mime_type") or "application/pdf"),
                data=raw if isinstance(raw, (bytes, bytearray)) else bytes(raw),
                entity_type="vehicle",
                entity_id=str(vehicle["id"]),
                role=role,
                uploaded_by=str(telegram_id),
                document_type=dtype,
            )
            if not uploaded.get("ok"):
                return uploaded
            pending_store.pop(int(telegram_id), None)
            item = uploaded.get("linked") or uploaded.get("item") or {}
            title = self._vehicle_title(vehicle) if hasattr(self, "_vehicle_title") else vin
            await self.notify_telegram_staff(org, title=f"Документ {dtype} · {vin}", entity_type="document", entity_id=str(item.get("id") or ""), vehicle_id=str(vehicle["id"]))
            return {
                "ok": True,
                "item": item,
                "message_ru": f"Документ сохранён\n{title}\nVIN: {vehicle.get('vin')}\nТип: {dtype}",
                "keyboard": self._doc_buttons(telegram_id, vin),
            }
        created = await self.create_document(
            org,
            {
                "vehicle_id": vehicle["id"],
                "document_type": dtype,
                "file_name": extra.get("filename") or f"{dtype}.pdf",
                "owner_type": extra.get("owner_type") or "vehicle",
                "deal_id": extra.get("deal_id"),
                "client_id": extra.get("client_id"),
                "source": "TELEGRAM",
            },
            role,
            str(telegram_id),
        )
        if not created.get("ok"):
            return created
        await self.notify_telegram_staff(org, title=f"Документ {dtype} · {vin}", entity_type="document", entity_id=str(created["item"]["id"]), vehicle_id=str(vehicle["id"]))
        return {"ok": True, "item": created.get("item"), "message_ru": f"Документ {dtype} привязан к {vin}"}

    def _doc_buttons(self, telegram_id: int, vin: str) -> list[list[dict[str, str]]]:
        from services.auto_ops.telegram_auth import callback_token

        dossier = callback_token(int(telegram_id), "docs", vin)
        add = callback_token(int(telegram_id), "doc", vin)
        self._callback_store()[dossier] = {"owner": int(telegram_id), "action": "docs", "entity_id": vin}
        self._callback_store()[add] = {"owner": int(telegram_id), "action": "doc", "entity_id": vin}
        return [[{"text": "Открыть досье", "callback_data": dossier}, {"text": "Добавить документ", "callback_data": add}]]

    async def _tg_docs(self, org: str, role: str, args: list[str], extra: dict[str, Any], telegram_id: int) -> dict[str, Any]:
        vin = str(extra.get("vin") or extra.get("entity_id") or (args[0] if args else "")).strip()
        if not vin:
            return {"ok": False, "error": "validation", "message_ru": "Формат: /docs VIN"}
        vehicle = await self._find_vehicle_by_vin(org, role, vin)
        if not vehicle:
            return {"ok": False, "error": "not_found", "message_ru": "VIN не найден в этой организации"}
        pack = self._eval_package(org, vehicle, SALE_PACKAGE_ITEMS)
        missing = pack.get("missing") or []
        lines = [f"Документы: {pack.get('present_count')}/{pack.get('required_count')}"]
        if missing:
            lines.append("Отсутствуют:")
            lines.extend(f"- {m}" for m in missing)
        else:
            lines.append("Пакет продажи готов.")
        return {
            "ok": True,
            "item": pack,
            "message_ru": "\n".join(lines),
            "keyboard": self._doc_buttons(telegram_id, str(vehicle.get("vin") or vin)),
        }

    async def _tg_reserve(self, org: str, role: str, args: list[str], extra: dict[str, Any]) -> dict[str, Any]:
        vin = str(extra.get("vin") or (args[0] if args else "")).strip()
        vehicle = await self._find_vehicle_by_vin(org, role, vin) if vin else None
        client_id = extra.get("client_id") or (args[1] if len(args) > 1 else None)
        if not vehicle or not client_id:
            return {"ok": False, "error": "validation", "message_ru": "Формат: /reserve VIN client_id"}
        created = await self.create_reservation(
            org,
            {
                "vehicle_id": vehicle["id"],
                "client_id": client_id,
                "deal_id": extra.get("deal_id"),
                "expires_at": extra.get("expires_at") or "2026-12-31",
                "override": extra.get("override"),
                "override_reason": extra.get("override_reason"),
            },
            role,
        )
        if not created.get("ok"):
            return created
        await self.notify_telegram_staff(org, title=f"Резерв · {vin}", entity_type="reservation", entity_id=str(created["item"]["id"]), vehicle_id=str(vehicle["id"]))
        return {"ok": True, "item": created.get("item"), "message_ru": f"Резерв на {vin}"}

    async def _tg_vehicle_status(self, org: str, role: str, args: list[str]) -> dict[str, Any]:
        if len(args) < 2:
            return {"ok": False, "error": "validation", "message_ru": "Формат: /status VIN СТАТУС"}
        vehicle = await self._find_vehicle_by_vin(org, role, args[0])
        if not vehicle:
            return {"ok": False, "error": "not_found", "message_ru": "VIN не найден в этой организации"}
        updated = await self.update_vehicle(org, str(vehicle["id"]), {"status": args[1].upper(), "source": "TELEGRAM"}, role)
        if not updated.get("ok"):
            return updated
        item = updated.get("item") or {}
        await self.notify_telegram_staff(org, title=f"Статус {args[0]}: {item.get('status_ru') or item.get('status')}", entity_type="vehicle", entity_id=str(vehicle["id"]), vehicle_id=str(vehicle["id"]))
        return {"ok": True, "item": item, "message_ru": f"Статус {args[0]}: {item.get('status_ru') or item.get('status')}"}

    async def _tg_report(self, org: str, role: str, telegram_id: int) -> dict[str, Any]:
        director = await self.analytics_director(org, role)
        dash = director.get("dashboard") or await self.dashboard(org, role)
        cards = dash.get("cards") or {}
        fin = director.get("finance_30d") or {}
        att = director.get("risks") or dash.get("attention") or []
        text = (
            "🚗 AUTO — Сводка\n"
            f"Авто: {cards.get('vehicles_total', 0)}\n"
            f"В пути: {cards.get('in_transit', 0)}\n"
            f"Таможня: {cards.get('at_customs', 0)}\n"
            f"В продаже: {cards.get('for_sale', 0)}\n"
        )
        if can(role, "finance"):
            invested = (dash.get("finance") or {}).get("invested")
            frozen = fin.get("frozen_capital")
            recv = fin.get("receivables")
            profit = fin.get("realized_profit")
            text += (
                f"\n💰 Вложено: {invested if invested is not None else '—'}\n"
                f"🔒 Заморожено: {frozen if frozen is not None else '—'}\n"
                f"💵 Дебиторка: {recv if recv is not None else '—'}\n"
                f"📈 Реализованная прибыль 30д: {profit if profit is not None else '—'}\n"
            )
        text += f"\n⚠ Требуют внимания: {len(att)}"
        return {
            "ok": True,
            "item": director,
            "message_ru": text,
            "keyboard": self._director_report_keyboard(int(telegram_id)),
        }

    def _director_report_keyboard(self, telegram_id: int) -> list[list[dict[str, str]]]:
        return [
            [
                {"text": "Открыть аналитику", "callback_data": self._bind_callback(telegram_id, "analytics", "")},
                {"text": "Риски", "callback_data": self._bind_callback(telegram_id, "risks", "")},
                {"text": "Cash Flow", "callback_data": self._bind_callback(telegram_id, "cashflow", "")},
            ]
        ]

    async def _tg_analytics(self, org: str, role: str) -> dict[str, Any]:
        director = await self.analytics_director(org, role)
        return {"ok": True, "item": director, "message_ru": str(director.get("summary_ru") or "Нет данных для аналитики.")}

    async def _tg_risks(self, org: str, role: str) -> dict[str, Any]:
        risks = await self.analytics_risks(org, role)
        items = risks.get("items") or []
        lines = [str(r.get("message_ru")) for r in items[:8]]
        body = "Риски\n" + ("\n".join(lines) if lines else "Открытых рисков по записям нет.")
        return {"ok": True, "item": risks, "message_ru": body}

    async def _tg_cashflow(self, org: str, role: str) -> dict[str, Any]:
        cf = await self.analytics_cashflow(org, role)
        if not cf.get("ok"):
            return cf
        gap = cf.get("gap")
        note = cf.get("note_ru") or ""
        if gap:
            msg = gap.get("message_ru") or "⚠ Возможный кассовый разрыв"
        else:
            msg = "Cash Flow: кассовый разрыв не прогнозируется." + (f" {note}" if note else "")
        return {"ok": True, "item": cf, "message_ru": msg}

    async def send_telegram_summary(self, kind: str, organization_id: str | None = None) -> dict[str, Any]:
        kind = "evening" if str(kind).lower().startswith("even") else "morning"
        sent = 0
        orgs = [organization_id] if organization_id else list(getattr(self, "_mem", {}).keys())
        texts = []
        for org in orgs or ["default"]:
            await self.ensure_hydrated(org)
            members = [m for m in self._bag(org)["telegram_members"] if m.get("enabled") is not False and can(m.get("role"), "reports")]
            if not members:
                continue
            report = await self._tg_report(org, "auto_director", 0)
            title = "Утренняя сводка Авто" if kind == "morning" else "Вечерняя сводка Авто"
            text = f"{title}\n{report.get('message_ru')}"
            texts.append(text)
            day = str(self._now())[:10]
            for member in members:
                await self._record_outbox(
                    org,
                    telegram_id=int(member["telegram_id"]),
                    kind=f"summary_{kind}",
                    text=text,
                    dedupe=f"summary:{kind}:{org}:{member['telegram_id']}:{day}",
                )
                sent += 1
        return {"ok": True, "kind": kind, "sent": sent, "message_ru": texts[0] if texts else "Нет сотрудников для сводки"}

    async def notify_telegram_staff(self, organization_id: str, *, title: str, entity_type: str, entity_id: str, vehicle_id: str | None = None) -> None:
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        day = str(self._now())[:10]
        for member in self._bag(org)["telegram_members"]:
            if member.get("enabled") is False:
                continue
            await self._record_outbox(
                org,
                telegram_id=int(member["telegram_id"]),
                kind="event",
                text=title,
                dedupe=f"event:{entity_type}:{entity_id}:{member['telegram_id']}:{day}",
            )
