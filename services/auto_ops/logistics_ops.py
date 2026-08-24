"""AUTO 1.7 logistics operations — providers, tracking fallback, vehicle history.

Mixin for AutoOpsService. Honest provider status: env-name configured or not.
Never live AIS. Never returns secret values.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from services.auto_ops.logistics_catalog import (
    EVENT_SOURCE_LABELS,
    PROVIDER_TYPE_IDS,
    confirmation_for_source,
    normalize_event_source,
)
from services.auto_ops.rbac import can, normalize_role, require

UNAVAILABLE_RU = "Автоматическое отслеживание недоступно"


def _str(value: Any) -> str:
    return str(value or "").strip()


class AutoOpsLogisticsOpsMixin:
    """Tracking providers + chronological vehicle logistics history."""

    def _public_provider(self, row: dict[str, Any]) -> dict[str, Any]:
        env_name = _str(row.get("api_key_env"))
        configured = bool(env_name and os.environ.get(env_name))
        enabled = bool(row.get("enabled"))
        status = "disabled"
        if enabled and configured:
            status = "ready"
        elif enabled:
            status = "unavailable"
        out = {
            **row,
            "api_key_env": env_name or None,
            "api_key_configured": configured,
            "status": status,
            "status_ru": {
                "ready": "Готов",
                "unavailable": UNAVAILABLE_RU,
                "disabled": "Выключен",
            }.get(status, status),
        }
        out.pop("api_key", None)
        out.pop("secret", None)
        out.pop("token", None)
        return out

    async def list_logistics_providers(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        items = self._scoped_rows(org, self._bag(org).get("logistics_providers") or [], query)
        return {
            "ok": True,
            "items": [self._public_provider(p) for p in items],
            "total": len(items),
            "live_ais": False,
            "unavailable_ru": UNAVAILABLE_RU,
            "note_ru": "Секрет API-ключа не отдаётся. Хранится только имя переменной окружения.",
        }

    async def upsert_logistics_provider(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None, provider_id: str | None = None) -> dict[str, Any]:
        if not can(role, "admin"):
            return require(role, "admin") or {"ok": False, "error": "forbidden"}
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        ptype = _str(body.get("type") or body.get("provider_type") or "other").lower()
        if ptype not in PROVIDER_TYPE_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип провайдера", "field": "type"}
        bag = self._bag(org)["logistics_providers"]
        existing = self._find(org, "logistics_providers", provider_id) if provider_id else None
        item = dict(existing or {})
        if not existing:
            item.update(
                {
                    "id": str(uuid.uuid4()),
                    "organization_id": org,
                    "tenant_id": org,
                    "workspace_id": _str(body.get("workspace_id")) or org,
                    "created_at": self._now(),
                }
            )
        item["name"] = _str(body.get("name") or body.get("provider") or item.get("name") or ptype)
        item["type"] = ptype
        item["url"] = _str(body.get("url")) or None
        if "api_key_env" in body or "api_key_environment" in body:
            item["api_key_env"] = _str(body.get("api_key_env") or body.get("api_key_environment")) or None
        if "enabled" in body:
            item["enabled"] = bool(body.get("enabled"))
        elif "enabled" not in item:
            item["enabled"] = False
        item["updated_at"] = self._now()
        item["updated_by"] = actor_id or normalize_role(role)
        item.pop("api_key", None)
        if existing:
            existing.update(item)
            await self._persist_update("logistics_provider", str(item["id"]), item)
            saved = existing
        else:
            saved = await self._persist("logistics_provider", item)
            bag.insert(0, saved)
        await self._audit(
            organization_id=org,
            action="provider_updated" if existing else "provider_created",
            entity_type="logistics_provider",
            entity_id=str(saved["id"]),
            role=role,
            actor_id=actor_id,
            new_value={"name": saved.get("name"), "type": saved.get("type"), "enabled": saved.get("enabled")},
        )
        return {"ok": True, "item": self._public_provider(saved)}

    async def check_logistics_provider(self, organization_id: str, provider_id: str, role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        row = self._find(org, "logistics_providers", provider_id)
        if not row:
            return {"ok": False, "error": "not_found", "message_ru": "Провайдер не найден"}
        env_name = _str(row.get("api_key_env"))
        configured = bool(env_name and os.environ.get(env_name))
        enabled = bool(row.get("enabled"))
        ok = enabled and configured
        error = None
        if not enabled:
            error = "Провайдер выключен"
        elif not env_name:
            error = "Не задано имя переменной окружения для ключа"
        elif not configured:
            error = f"Переменная {env_name} не задана"
        row["last_check_at"] = self._now()
        row["last_check_ok"] = ok
        row["last_error"] = None if ok else error
        row["updated_at"] = self._now()
        await self._persist_update(
            "logistics_provider",
            provider_id,
            {"last_check_at": row["last_check_at"], "last_check_ok": ok, "last_error": row["last_error"], "updated_at": row["updated_at"]},
        )
        pub = self._public_provider(row)
        return {
            "ok": True,
            "item": pub,
            "available": ok,
            "live_ais": False,
            "message_ru": "Конфигурация проверена." if ok else UNAVAILABLE_RU,
            "error": error,
        }

    async def shipment_tracking(self, organization_id: str, shipment_id: str, role: str | None, *, fetch: bool = False) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        ship = self._find(org, "shipments", shipment_id)
        if not ship:
            return {"ok": False, "error": "not_found", "message_ru": "Перевозка не найдена"}
        providers = [p for p in self._bag(org).get("logistics_providers") or [] if str(p.get("organization_id") or org) == org]
        chosen = None
        pid = _str(ship.get("provider_id"))
        if pid:
            chosen = next((p for p in providers if str(p.get("id")) == pid), None)
        if chosen is None:
            chosen = next((p for p in providers if p.get("enabled")), None)
        available = False
        last_payload = None
        error = None
        source_url = _str(ship.get("tracking_url")) or (chosen and _str(chosen.get("url"))) or None
        if chosen:
            env_name = _str(chosen.get("api_key_env"))
            available = bool(chosen.get("enabled") and env_name and os.environ.get(env_name))
            last_payload = chosen.get("last_payload") if fetch else None
            if fetch and not available:
                error = UNAVAILABLE_RU
            if fetch and available:
                last_payload = chosen.get("last_payload") or {
                    "mode": "configured",
                    "live_ais": False,
                    "note_ru": "Живой AIS не подключён. Показаны последние сохранённые данные источника, если они есть.",
                    "checked_at": chosen.get("last_check_at"),
                }
                chosen["last_payload"] = last_payload
                chosen["last_check_at"] = self._now()
                chosen["last_check_ok"] = True
                chosen["last_error"] = None
        else:
            error = UNAVAILABLE_RU
        return {
            "ok": True,
            "available": available,
            "live_ais": False,
            "message_ru": None if available else UNAVAILABLE_RU,
            "error": error,
            "source_url": source_url,
            "provider": self._public_provider(chosen) if chosen else None,
            "last": last_payload if fetch else (chosen.get("last_payload") if chosen else None),
            "manual_event_allowed": True,
        }

    async def vehicle_logistics_history(self, organization_id: str, vehicle_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        if not self._find(org, "vehicles", vehicle_id):
            return {"ok": False, "error": "not_found", "message_ru": "Автомобиль не найден"}
        shipments = [s for s in self._bag(org)["shipments"] if str(s.get("vehicle_id")) == str(vehicle_id)]
        ship_ids = {str(s.get("id")) for s in shipments}
        items: list[dict[str, Any]] = []
        for ev in self._bag(org)["logistics_events"]:
            if str(ev.get("shipment_id") or "") not in ship_ids:
                continue
            src = normalize_event_source(ev.get("source"))
            items.append(
                {
                    "kind": "event",
                    "id": ev.get("id"),
                    "at": ev.get("created_at"),
                    "title": ev.get("description") or ev.get("event_type"),
                    "event_type": ev.get("event_type"),
                    "source": src,
                    "source_ru": EVENT_SOURCE_LABELS.get(src, src),
                    "confirmation": ev.get("confirmation") or confirmation_for_source(src),
                    "location": ev.get("location"),
                    "shipment_id": ev.get("shipment_id"),
                }
            )
        wanted_actions = {
            "shipment_created",
            "vehicle_linked",
            "container_assigned",
            "container_changed",
            "vessel_changed",
            "eta_changed",
            "event_added",
            "status_changed",
            "expense_allocated",
            "carrier_changed",
            "document_linked",
            "location_updated",
            "delivery_completed",
        }
        for a in self._bag(org)["audit"]:
            if a.get("action") not in wanted_actions:
                continue
            eid = str(a.get("entity_id") or "")
            if eid not in ship_ids and eid != str(vehicle_id):
                nv = a.get("new_value") or {}
                if str(nv.get("vehicle_id") or "") != str(vehicle_id) and str(nv.get("shipment_id") or "") not in ship_ids:
                    continue
            items.append(
                {
                    "kind": "audit",
                    "id": a.get("id"),
                    "at": a.get("created_at"),
                    "title": a.get("summary") or a.get("action"),
                    "action": a.get("action"),
                    "source": "SYSTEM",
                    "source_ru": EVENT_SOURCE_LABELS["SYSTEM"],
                    "confirmation": "CONFIRMED",
                    "shipment_id": eid if eid in ship_ids else None,
                }
            )
        items.sort(key=lambda r: str(r.get("at") or ""), reverse=False)
        return {"ok": True, "items": items, "total": len(items), "vehicle_id": vehicle_id}
