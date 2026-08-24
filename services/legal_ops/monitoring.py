"""Sprint Lawyer 3.3/3.4 — monitoring engine, enforcement, change center, calendar mappings."""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from services.legal_ops.desk_ops import active_only
from services.legal_ops.providers import (
    diff_states,
    fingerprint_state,
    get_legal_data_providers,
    normalize_external_state,
)
from services.legal_ops.rbac import require
from services.legal_ops.url_safety import validate_source_url

logger = logging.getLogger(__name__)

# Lawyer 3.4 — safe defaults: no high-impact auto actions
DEFAULT_AUTOMATION = {
    "on_hearing": {
        "notify": True,
        "suggest_calendar": True,
        "add_calendar": False,
        "create_task": False,
        "send_ai": False,
    },
    "on_document": {
        "notify": True,
        "auto_ai_analyze": False,
        "suggest_ai": True,
        "create_task": False,
    },
    "on_important": {
        "notify": True,
        "create_task": False,
        "suggest_calendar": True,
        "send_ai": False,
        "add_calendar": False,
    },
}

CHANGE_WORKFLOW = {
    "new": "Новое",
    "viewed": "Просмотрено",
    "needs_action": "Требует действия",
    "closed": "Закрыто",
}

DEFAULT_GOOGLE_SYNC = {
    "direction": "ados_to_google",
    "types": {"hearing": True, "meeting": True, "deadline": True, "task": True, "contract_end": False},
    "selected_calendar_id": "primary",
    "last_sync_at": None,
}

UNCONNECTED_MSG = (
    "Источник не подключен. Для автоматического обновления требуется официальный или лицензированный источник данных."
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now()).isoformat()


def _change_dedupe(*, watchlist_id: str, change_type: str, detail: dict[str, Any]) -> str:
    raw = f"{watchlist_id}|{change_type}|{detail.get('starts_at','')}|{detail.get('title','')}|{detail.get('external_id','')}|{detail.get('to','')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:40]


def _freq_hours(freq: str | None) -> int:
    f = (freq or "12h").lower().strip()
    mapping = {"1h": 1, "6h": 6, "12h": 12, "24h": 24, "daily": 24, "twice_daily": 12}
    return mapping.get(f, 12)


def scrub_secrets(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Never return OAuth tokens / client secrets in API responses."""
    if not payload:
        return {}
    banned = {"refresh_token", "access_token", "client_secret", "id_token", "token", "password", "authorization"}
    out: dict[str, Any] = {}
    for k, v in payload.items():
        lk = str(k).lower()
        if lk in banned or "secret" in lk or "token" in lk:
            out[k] = "[redacted]"
        elif isinstance(v, dict):
            out[k] = scrub_secrets(v)
        else:
            out[k] = v
    return out


class LegalOpsMonitoringMixin:
    def providers_catalog(self) -> dict[str, Any]:
        items = get_legal_data_providers().catalog()
        # Counterparties — honest unavailable (no fake KYC)
        items.append(
            {
                "provider": "counterparties",
                "label_ru": "Контрагенты (внешняя проверка)",
                "status": "UNAVAILABLE",
                "message_ru": UNCONNECTED_MSG,
                "official_source": "Не подключён",
                "automatic_integration": False,
                "ready": False,
                "implemented": True,
            }
        )
        for it in items:
            if it.get("status") in {"UNAVAILABLE", "REQUIRES_CONFIGURATION"} and it.get("provider") != "manual_import":
                it["message_ru"] = it.get("message_ru") or UNCONNECTED_MSG
                it["ui_hint_ru"] = UNCONNECTED_MSG
        return {"ok": True, "items": items}

    def default_monitor_settings(self) -> dict[str, Any]:
        return {
            "timezone": "Europe/Kyiv",
            "cron_morning": "0 9 * * *",
            "cron_evening": "0 18 * * *",
            "google_sync": dict(DEFAULT_GOOGLE_SYNC),
            "automation_defaults": dict(DEFAULT_AUTOMATION),
        }

    async def integration_health(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        gcal = scrub_secrets(self.gcal_status())  # type: ignore[attr-defined]
        providers = {p["provider"]: p for p in self.providers_catalog()["items"]}

        def badge(status: str) -> dict[str, str]:
            raw = status or ""
            s = raw.upper()
            if raw == "connected" or s == "CONNECTED":
                return {"code": "connected", "icon": "green", "status_label_ru": "Подключено"}
            if s == "MANUAL":
                return {"code": "manual", "icon": "yellow", "status_label_ru": "Требуется настройка / ручной режим"}
            if s in {"REQUIRES_CONFIGURATION", "NEEDS_CONFIG", "NEEDS_OAUTH"} or raw in {
                "needs_config",
                "needs_oauth",
            }:
                return {"code": "needs_config", "icon": "yellow", "status_label_ru": "Требуется настройка"}
            if s in {"ERROR", "DEGRADED"} or raw == "ERROR":
                return {"code": "error", "icon": "red", "status_label_ru": "Ошибка"}
            if s in {"UNAVAILABLE", "COMING_SOON"} or raw in {"coming_soon", "unavailable"}:
                return {"code": "off", "icon": "gray", "status_label_ru": "Выключено / недоступно"}
            return {"code": "unknown", "icon": "gray", "status_label_ru": raw or "Неизвестно"}

        # errors last 24h from activity
        cutoff = _now() - timedelta(hours=24)
        acts = self._bag(org).get("activity", [])  # type: ignore[attr-defined]
        err_actions = {
            "GOOGLE_SYNC_FAILED",
            "google_calendar_sync_failed",
            "watchlist_checked",
        }
        errors_24h = []
        for a in acts:
            created = str(a.get("created_at") or "")
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except Exception:
                continue
            if dt < cutoff:
                continue
            action = str(a.get("action") or "")
            if "fail" in action.lower() or action in err_actions and a.get("payload", {}).get("error"):
                errors_24h.append({"action": action, "summary": a.get("summary"), "at": created})
            if action.endswith("_failed") or "FAILED" in action:
                errors_24h.append({"action": action, "summary": a.get("summary"), "at": created})

        g_status = gcal.get("status") or "needs_config"
        g_badge = badge(g_status)
        if g_status == "needs_config":
            g_badge["status_label_ru"] = "Не настроен администратором"
        elif g_status == "needs_oauth":
            g_badge["status_label_ru"] = "Требуется авторизация Google OAuth"

        court = providers.get("ua_edrsr") or {}
        enf = providers.get("ua_enforcement") or {}
        cp = providers.get("counterparties") or {}

        mappings = self._bag(org).get("calendar_mappings", [])  # type: ignore[attr-defined]
        last_sync = None
        for m in mappings:
            ls = m.get("last_synced_at")
            if ls and (last_sync is None or str(ls) > str(last_sync)):
                last_sync = ls

        items = [
            {
                "id": "google_calendar",
                "label_ru": "Google Calendar",
                **g_badge,
                "status_raw": g_status,
                "message_ru": gcal.get("message_ru"),
                "last_success_at": last_sync,
            },
            {
                "id": "court_data",
                "label_ru": "Судебные данные",
                **badge(court.get("status") or "UNAVAILABLE"),
                "status_raw": court.get("status"),
                "message_ru": court.get("message_ru") or UNCONNECTED_MSG,
                "last_success_at": None,
            },
            {
                "id": "enforcement",
                "label_ru": "Исполнительные производства",
                **badge(enf.get("status") or "REQUIRES_CONFIGURATION"),
                "status_raw": enf.get("status"),
                "message_ru": enf.get("message_ru") or UNCONNECTED_MSG,
                "last_success_at": None,
            },
            {
                "id": "counterparties",
                "label_ru": "Контрагенты",
                **badge(cp.get("status") or "UNAVAILABLE"),
                "status_raw": cp.get("status"),
                "message_ru": cp.get("message_ru") or UNCONNECTED_MSG,
                "last_success_at": None,
            },
            {
                "id": "scheduler",
                "label_ru": "Scheduler",
                "code": "connected",
                "icon": "green",
                "status_label_ru": "Подключено",
                "status_raw": "CONNECTED",
                "message_ru": "Jobs legal.monitor.morning / evening в pg_scheduler_engine",
                "last_success_at": None,
            },
        ]

        return {
            "ok": True,
            "title_ru": "СОСТОЯНИЕ ИНТЕГРАЦИЙ",
            "items": items,
            "errors_24h": errors_24h[:50],
            "errors_24h_count": len(errors_24h),
            "google": gcal,
            "providers": list(providers.values()),
        }

    async def get_monitor_settings(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        settings = bag.get("monitor_settings")
        if not settings:
            settings = {"id": str(uuid.uuid4()), "organization_id": org, **self.default_monitor_settings()}
            bag["monitor_settings"] = settings
        return {"ok": True, "item": settings}

    async def update_monitor_settings(
        self, organization_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "edit")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        cur = (await self.get_monitor_settings(org, role))["item"]
        for key in ("timezone", "cron_morning", "cron_evening"):
            if body.get(key):
                cur[key] = str(body[key])
        if isinstance(body.get("google_sync"), dict):
            gs = dict(cur.get("google_sync") or DEFAULT_GOOGLE_SYNC)
            gs.update(body["google_sync"])
            # Bidirectional not silently enabled
            if gs.get("direction") in {"google_to_ados", "bidirectional"}:
                return {
                    "ok": False,
                    "error": "not_supported",
                    "message_ru": "Google → ADOS / двусторонняя синхронизация в Sprint 3.4 не включена (риск конфликтов).",
                }
            cur["google_sync"] = gs
        if isinstance(body.get("automation_defaults"), dict):
            cur["automation_defaults"] = {**DEFAULT_AUTOMATION, **body["automation_defaults"]}
        if isinstance(body.get("payload"), dict):
            cur["payload"] = {**(cur.get("payload") or {}), **scrub_secrets(body["payload"])}
        cur["updated_at"] = _iso()
        saved = await self._persist("monitor_settings", cur)  # type: ignore[attr-defined]
        self._bag(org)["monitor_settings"] = saved  # type: ignore[attr-defined]
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="monitor_settings",
            entity_id=saved.get("id") or org,
            action="monitor_settings_updated",
            summary="Настройки мониторинга обновлены",
            role=role,
        )
        return {"ok": True, "item": saved}

    async def list_watchlist(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        return {"ok": True, "items": active_only(self._bag(org).get("watchlist", []))}  # type: ignore[attr-defined]

    async def add_watchlist(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        case_id = body.get("case_id")
        entity_kind = str(body.get("entity_kind") or body.get("object_type") or "court_case").strip()
        external = str(
            body.get("external_case_number")
            or body.get("identifier")
            or body.get("court_case_number")
            or body.get("production_number")
            or ""
        ).strip()
        title = str(body.get("title") or body.get("name") or "").strip()
        if not external and case_id:
            case = next((c for c in self._bag(org)["cases"] if str(c.get("id")) == str(case_id)), None)  # type: ignore[attr-defined]
            if case:
                external = str(case.get("court_case_number") or case.get("case_number") or "").strip()
                title = title or str(case.get("title") or "")
        if not external and not title:
            return {"ok": False, "error": "validation", "message_ru": "Укажите идентификатор или название объекта мониторинга"}
        if not external:
            external = f"manual-{uuid.uuid4().hex[:10]}"
        url_check = validate_source_url(body.get("source_url") or body.get("url"))
        if not url_check.get("ok"):
            return url_check
        provider = str(body.get("provider") or "manual_import")
        # Block fake auto providers for creation without config — force manual
        if provider in {"ua_edrsr", "ua_enforcement", "counterparties"}:
            return {
                "ok": False,
                "error": "provider_unavailable",
                "message_ru": UNCONNECTED_MSG,
                "provider_status": get_legal_data_providers().get(provider).status(),
            }
        existing = next(
            (
                w
                for w in active_only(self._bag(org).get("watchlist", []))  # type: ignore[attr-defined]
                if str(w.get("external_case_number")) == external and str(w.get("provider")) == provider
            ),
            None,
        )
        if existing:
            return {"ok": True, "item": existing, "duplicate": True, "message_ru": "Уже в мониторинге"}
        freq = str(body.get("check_frequency") or "12h")
        active = body.get("active")
        if active is None:
            active = True
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "case_id": case_id,
            "client_id": body.get("client_id"),
            "entity_kind": entity_kind,
            "external_case_number": external,
            "provider": provider,
            "status": "active" if active else "disabled",
            "active": bool(active),
            "title": title or external,
            "source_url": url_check.get("url"),
            "check_frequency": freq,
            "comment": body.get("comment") or body.get("notes"),
            "counterparty": body.get("counterparty"),
            "decision_ref": body.get("decision_ref") or body.get("decision_reference"),
            "enforcement_id": body.get("enforcement_id"),
            "last_checked_at": None,
            "last_success_at": None,
            "next_check_at": _iso(_now() + timedelta(hours=_freq_hours(freq))),
            "last_error": None,
            "fingerprint": None,
            "normalized_state": None,
            "automation": {**DEFAULT_AUTOMATION, **(body.get("automation") or {})},
            "payload": {
                **(body.get("payload") or {}),
                "source_url": url_check.get("url"),
                "decision_ref": body.get("decision_ref") or body.get("decision_reference"),
            },
            "created_at": _iso(),
        }
        if case_id and external and not str(external).startswith("manual-"):
            await self._patch_mem(org, "case", str(case_id), {"court_case_number": external})  # type: ignore[attr-defined]
        saved = await self._persist("watchlist", item)  # type: ignore[attr-defined]
        self._bag(org).setdefault("watchlist", []).insert(0, saved)  # type: ignore[attr-defined]
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="watchlist",
            entity_id=saved["id"],
            action="WATCH_ITEM_CREATED",
            summary=f"Watch item создан: {saved.get('title') or external}",
            role=role,
            payload={"provider": provider, "case_id": case_id, "entity_kind": entity_kind},
        )
        return {"ok": True, "item": saved}

    async def update_watchlist(
        self, organization_id: str, watchlist_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "edit")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        item = next((w for w in self._bag(org).get("watchlist", []) if str(w.get("id")) == str(watchlist_id)), None)  # type: ignore[attr-defined]
        if not item:
            return {"ok": False, "error": "not_found"}
        patch: dict[str, Any] = {}
        for key in (
            "title",
            "comment",
            "counterparty",
            "decision_ref",
            "check_frequency",
            "case_id",
            "client_id",
            "enforcement_id",
            "entity_kind",
            "automation",
        ):
            if key in body:
                patch[key] = body[key]
        if "source_url" in body or "url" in body:
            url_check = validate_source_url(body.get("source_url") or body.get("url"))
            if not url_check.get("ok"):
                return url_check
            patch["source_url"] = url_check.get("url")
        if "active" in body:
            patch["active"] = bool(body.get("active"))
            patch["status"] = "active" if body.get("active") else "disabled"
        if "identifier" in body or "external_case_number" in body:
            patch["external_case_number"] = str(body.get("identifier") or body.get("external_case_number") or "").strip()
        action = "WATCH_ITEM_UPDATED"
        if patch.get("status") == "disabled" or patch.get("active") is False:
            action = "WATCH_ITEM_DISABLED"
        saved = await self._patch_mem(org, "watchlist", watchlist_id, patch)  # type: ignore[attr-defined]
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="watchlist",
            entity_id=watchlist_id,
            action=action,
            summary=f"Watch item обновлён ({action})",
            role=role,
            payload=scrub_secrets(patch),
        )
        return {"ok": True, "item": saved}

    async def check_watchlist_item(
        self, organization_id: str, watchlist_id: str, body: dict[str, Any] | None = None, role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "ai")
        if denied:
            denied = require(role, "edit")
            if denied:
                return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        body = body or {}
        item = next((w for w in self._bag(org).get("watchlist", []) if str(w.get("id")) == str(watchlist_id)), None)  # type: ignore[attr-defined]
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Запись мониторинга не найдена"}
        if item.get("active") is False or item.get("status") == "disabled":
            return {"ok": False, "error": "disabled", "message_ru": "Watch item отключён"}

        provider = get_legal_data_providers().get(item.get("provider"))
        pstatus = provider.status()
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="watchlist",
            entity_id=watchlist_id,
            action="LEGAL_PROVIDER_CHECK",
            summary=f"Проверка провайдера {item.get('provider')}",
            role=role,
            payload={"provider": item.get("provider"), "status": pstatus.get("status")},
        )

        imported = body.get("imported_state")
        # Prefer last imported snapshot for scheduler / check-now without body (no scrape)
        if not imported and item.get("provider") == "manual_import":
            imported = (item.get("payload") or {}).get("imported_state")
        if not imported and item.get("provider") == "manual_import":
            imported = {
                "external_case_number": item.get("external_case_number"),
                "status": (item.get("normalized_state") or {}).get("status") or "open",
                "notes": item.get("comment") or "",
                "events": (item.get("normalized_state") or {}).get("events")
                or (item.get("payload") or {}).get("events")
                or [],
                "documents": (item.get("normalized_state") or {}).get("documents")
                or (item.get("payload") or {}).get("documents")
                or (
                    [{"title": item.get("decision_ref"), "external_id": item.get("decision_ref"), "url": item.get("source_url")}]
                    if item.get("decision_ref")
                    else []
                ),
                "source_url": item.get("source_url"),
                "counterparty": item.get("counterparty"),
                "title": item.get("title"),
            }
            # Allow body field updates to count as new state
            if body.get("title") or body.get("comment") or body.get("decision_ref") or body.get("counterparty"):
                imported["title"] = body.get("title") or imported.get("title")
                imported["notes"] = body.get("comment") or imported.get("notes")
                imported["counterparty"] = body.get("counterparty") or imported.get("counterparty")
                if body.get("decision_ref"):
                    imported["documents"] = [
                        {"title": body.get("decision_ref"), "external_id": body.get("decision_ref"), "url": item.get("source_url")}
                    ]
        if imported:
            payload = dict(item.get("payload") or {})
            payload["imported_state"] = imported
            # never fetch user URL
            payload["url_fetch"] = False
            item["payload"] = payload

        watch_payload = dict(item)
        if item.get("payload", {}).get("imported_state"):
            watch_payload["imported_state"] = item["payload"]["imported_state"]

        result = provider.check_updates(watch_payload)
        now = _iso()
        hours = _freq_hours(item.get("check_frequency"))
        patch: dict[str, Any] = {"last_checked_at": now, "next_check_at": _iso(_now() + timedelta(hours=hours))}
        changes_saved: list[dict[str, Any]] = []

        if not result.get("ok") and result.get("error"):
            patch["last_error"] = result.get("message_ru") or result.get("error")
            patch["status"] = "error" if pstatus.get("status") == "ERROR" else item.get("status") or "active"
            saved = await self._patch_mem(org, "watchlist", watchlist_id, patch)  # type: ignore[attr-defined]
            return {
                "ok": True,
                "item": saved,
                "provider_status": pstatus,
                "check": result,
                "changes": [],
                "message_ru": result.get("message_ru") or pstatus.get("message_ru") or UNCONNECTED_MSG,
            }

        normalized = result.get("normalized")
        if normalized:
            # include source_url in fingerprint surface via notes
            if item.get("source_url"):
                normalized = {**normalized, "notes": f"{normalized.get('notes') or ''}|url:{item.get('source_url')}"}
            prev_norm = item.get("normalized_state")
            old_fp = item.get("fingerprint")
            fp = result.get("fingerprint") or fingerprint_state(normalized)
            patch["fingerprint"] = fp
            patch["normalized_state"] = normalized
            patch["last_success_at"] = now
            patch["last_error"] = None
            if item.get("active") is not False:
                patch["status"] = "active"
            if item.get("payload", {}).get("imported_state") or imported:
                payload = dict(item.get("payload") or {})
                if imported:
                    payload["imported_state"] = imported
                patch["payload"] = payload

            diffs = diff_states(prev_norm if isinstance(prev_norm, dict) else None, normalized)
            if not prev_norm and not body.get("force_notify_baseline"):
                diffs = []
            for d in diffs:
                ch = await self._record_change(
                    org,
                    watch=item,
                    change_type=d["change_type"],
                    title=d["title"],
                    detail=d.get("detail") or {},
                    provider=str(item.get("provider")),
                    role=role,
                    old_fingerprint=old_fp,
                    new_fingerprint=fp,
                )
                if ch:
                    changes_saved.append(ch)
                    await self._apply_automation(org, item, ch, role=role)
        elif result.get("changed") is False:
            patch["last_success_at"] = now
            patch["last_error"] = None

        saved = await self._patch_mem(org, "watchlist", watchlist_id, patch)  # type: ignore[attr-defined]
        msg = "Актуально" if not changes_saved else f"Найдено {len(changes_saved)} изменения"
        if pstatus.get("status") in {"UNAVAILABLE", "REQUIRES_CONFIGURATION"} and not changes_saved:
            msg = pstatus.get("message_ru") or UNCONNECTED_MSG
        return {
            "ok": True,
            "item": saved,
            "provider_status": pstatus,
            "check": result,
            "changes": changes_saved,
            "message_ru": msg,
        }

    async def _record_change(
        self,
        org: str,
        *,
        watch: dict[str, Any],
        change_type: str,
        title: str,
        detail: dict[str, Any],
        provider: str,
        role: str | None,
        old_fingerprint: str | None = None,
        new_fingerprint: str | None = None,
    ) -> dict[str, Any] | None:
        dedupe = _change_dedupe(watchlist_id=str(watch.get("id")), change_type=change_type, detail=detail)
        existing = next(
            (
                c
                for c in self._bag(org).get("monitor_changes", [])  # type: ignore[attr-defined]
                if c.get("dedupe_key") == dedupe
            ),
            None,
        )
        if existing:
            return None  # duplicate protection
        suggestions: dict[str, Any] = {
            "create_task": False,
            "add_calendar": False,
            "send_ai": False,
            "notify": True,
        }
        summary = f"{title}: {detail.get('title') or detail.get('to') or detail.get('starts_at') or ''}".strip()
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "watchlist_id": watch.get("id"),
            "case_id": watch.get("case_id"),
            "client_id": watch.get("client_id"),
            "enforcement_id": watch.get("enforcement_id"),
            "change_type": change_type,
            "title": title,
            "detail": detail,
            "dedupe_key": dedupe,
            "provider": provider,
            "source_label": get_legal_data_providers().get(provider).status().get("label_ru"),
            "source_reference": watch.get("source_url") or watch.get("decision_ref"),
            "read_at": None,
            "workflow_status": "new",
            "summary": summary,
            "old_fingerprint": old_fingerprint,
            "new_fingerprint": new_fingerprint,
            "suggestions": suggestions,
            "payload": {"counterparty": watch.get("counterparty"), "watch_title": watch.get("title")},
            "created_at": _iso(),
        }
        saved = await self._persist("monitor_change", item)  # type: ignore[attr-defined]
        self._bag(org).setdefault("monitor_changes", []).insert(0, saved)  # type: ignore[attr-defined]
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="monitor_change",
            entity_id=saved["id"],
            action="LEGAL_CHANGE_DETECTED",
            summary=summary,
            role=role,
            payload={"change_type": change_type, "watchlist_id": watch.get("id"), "provider": provider},
        )
        try:
            from services.legal_ops.notifications import emit_legal_change_notification

            await emit_legal_change_notification(self, organization_id=org, change=saved, role=role)
        except Exception as exc:
            logger.debug("legal change notification skipped: %s", exc)
        return saved

    async def _apply_automation(
        self, org: str, watch: dict[str, Any], change: dict[str, Any], role: str | None
    ) -> None:
        auto = watch.get("automation") or DEFAULT_AUTOMATION
        ctype = change.get("change_type")
        suggestions = dict(change.get("suggestions") or {})
        if ctype == "hearing":
            rules = auto.get("on_hearing") or {}
            detail = change.get("detail") or {}
            suggestions["notify"] = bool(rules.get("notify", True))
            suggestions["suggest_calendar"] = bool(rules.get("suggest_calendar", True))
            suggestions["add_calendar"] = False
            suggestions["create_task"] = bool(rules.get("create_task"))
            suggestions["send_ai"] = bool(rules.get("send_ai"))
            if rules.get("suggest_calendar") and detail.get("starts_at"):
                suggestions["calendar_draft"] = {
                    "title": detail.get("title") or change.get("title"),
                    "starts_at": detail.get("starts_at"),
                    "event_type": "hearing",
                }
            # High-impact auto calendar only if explicitly enabled
            if rules.get("add_calendar") and detail.get("starts_at"):
                await self.create_calendar_event(  # type: ignore[attr-defined]
                    org,
                    {
                        "title": detail.get("title") or change.get("title") or "Заседание",
                        "starts_at": detail.get("starts_at"),
                        "case_id": watch.get("case_id"),
                        "client_id": watch.get("client_id"),
                        "event_type": "hearing",
                        "source_kind": "court_monitor",
                        "source_id": change.get("id"),
                        "payload": {"from_change_id": change.get("id"), "origin": "court"},
                    },
                    role,
                )
                suggestions["add_calendar"] = True
            if rules.get("create_task"):
                await self.create_task(  # type: ignore[attr-defined]
                    org,
                    {
                        "title": f"Подготовка к заседанию: {detail.get('title') or ''}",
                        "case_id": watch.get("case_id"),
                        "client_id": watch.get("client_id"),
                        "kind": "deadline",
                        "status": "new",
                        "due_at": detail.get("starts_at"),
                        "payload": {"from_change_id": change.get("id")},
                    },
                    role,
                )
            if rules.get("notify"):
                suggestions["notify"] = True
                suggestions["notification"] = {
                    "title": change.get("title"),
                    "summary": change.get("summary"),
                    "deeplink": f"/workspace/legal?view=monitoring&change={change.get('id')}",
                }
            wf = "needs_action" if suggestions.get("suggest_calendar") or suggestions.get("create_task") else "new"
            await self._patch_mem(org, "monitor_change", str(change["id"]), {"suggestions": suggestions, "workflow_status": wf})  # type: ignore[attr-defined]
            change["suggestions"] = suggestions
            change["workflow_status"] = wf
        if ctype == "document":
            rules = auto.get("on_document") or {}
            suggestions["notify"] = bool(rules.get("notify", True))
            suggestions["suggest_ai"] = bool(rules.get("suggest_ai", True))
            suggestions["send_ai"] = False
            if rules.get("auto_ai_analyze"):
                detail = change.get("detail") or {}
                await self.ai_analyze(  # type: ignore[attr-defined]
                    org,
                    {
                        "action": "summarize",
                        "target_type": "case",
                        "target_id": watch.get("case_id"),
                        "case_id": watch.get("case_id"),
                        "client_id": watch.get("client_id"),
                        "question": f"AI-анализ нового судебного документа: {detail.get('title')}",
                        "text": f"Документ: {detail.get('title')}\nURL: {detail.get('url')}\nИсточник: {change.get('source_label')}",
                    },
                    role,
                )
                suggestions["send_ai"] = True
            await self._patch_mem(  # type: ignore[attr-defined]
                org,
                "monitor_change",
                str(change["id"]),
                {"suggestions": suggestions, "workflow_status": "needs_action" if suggestions.get("suggest_ai") else "new"},
            )
            change["suggestions"] = suggestions

    async def list_monitor_changes(
        self, organization_id: str, role: str | None = None, *, unread_only: bool = False
    ) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        items = active_only(self._bag(org).get("monitor_changes", []))  # type: ignore[attr-defined]
        if unread_only:
            items = [i for i in items if not i.get("read_at")]
        return {"ok": True, "items": items}

    async def monitor_change_action(
        self, organization_id: str, change_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "edit")
        if denied:
            return denied
        if not body.get("confirm") and body.get("action") not in {"mark_read", "open", "set_status"}:
            return {
                "ok": False,
                "error": "confirmation_required",
                "message_ru": "Подтвердите действие (confirm=true)",
            }
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        ch = next((c for c in self._bag(org).get("monitor_changes", []) if str(c.get("id")) == str(change_id)), None)  # type: ignore[attr-defined]
        if not ch:
            return {"ok": False, "error": "not_found"}
        action = str(body.get("action") or "")
        created: dict[str, Any] = {}
        if action in {"mark_read", "open"}:
            saved = await self._patch_mem(  # type: ignore[attr-defined]
                org,
                "monitor_change",
                change_id,
                {"read_at": _iso(), "workflow_status": "viewed"},
            )
            return {
                "ok": True,
                "item": saved,
                "action": action,
                "related": {
                    "case_id": ch.get("case_id"),
                    "client_id": ch.get("client_id"),
                    "counterparty": (ch.get("payload") or {}).get("counterparty"),
                    "enforcement_id": ch.get("enforcement_id"),
                },
            }
        if action == "set_status":
            st = str(body.get("workflow_status") or "")
            if st not in CHANGE_WORKFLOW:
                return {"ok": False, "error": "validation", "message_ru": "Недопустимый статус"}
            saved = await self._patch_mem(org, "monitor_change", change_id, {"workflow_status": st})  # type: ignore[attr-defined]
            return {"ok": True, "item": saved, "action": action}
        if action == "create_task":
            detail = ch.get("detail") or {}
            res = await self.create_task(  # type: ignore[attr-defined]
                org,
                {
                    "title": body.get("title") or f"Изменение: {ch.get('title')}",
                    "case_id": ch.get("case_id"),
                    "client_id": ch.get("client_id"),
                    "due_at": body.get("due_at") or detail.get("starts_at"),
                    "kind": "deadline",
                    "status": "new",
                    "payload": {"from_change_id": change_id},
                },
                role,
            )
            created["task"] = res.get("item")
            await self._patch_mem(org, "monitor_change", change_id, {"workflow_status": "needs_action"})  # type: ignore[attr-defined]
        elif action == "add_calendar":
            detail = ch.get("detail") or {}
            draft = (ch.get("suggestions") or {}).get("calendar_draft") or {}
            starts = body.get("starts_at") or detail.get("starts_at") or draft.get("starts_at")
            if not starts:
                return {"ok": False, "error": "validation", "message_ru": "Укажите starts_at"}
            res = await self.create_calendar_event(  # type: ignore[attr-defined]
                org,
                {
                    "title": body.get("title") or draft.get("title") or ch.get("title") or "Событие из мониторинга",
                    "starts_at": starts,
                    "case_id": ch.get("case_id"),
                    "client_id": ch.get("client_id"),
                    "event_type": body.get("event_type") or draft.get("event_type") or "hearing",
                    "source_kind": "court_monitor",
                    "source_id": change_id,
                    "payload": {"origin": "court", "from_change_id": change_id},
                },
                role,
            )
            created["event"] = res.get("item")
        elif action in {"ai_analyze", "handoff_lawyer"}:
            detail = ch.get("detail") or {}
            if action == "handoff_lawyer":
                res = await self.ai_lawyer_run(  # type: ignore[attr-defined]
                    org,
                    {
                        "mode": body.get("mode") or "consult",
                        "prompt": body.get("prompt") or f"Контекст изменения: {ch.get('summary') or ch.get('title')}",
                        "case_id": ch.get("case_id"),
                        "client_id": ch.get("client_id"),
                        "text": str(detail),
                    },
                    role,
                )
                created["lawyer"] = scrub_secrets(res.get("item") or res.get("reply") or {})
            else:
                res = await self.ai_analyze(  # type: ignore[attr-defined]
                    org,
                    {
                        "action": "summarize",
                        "target_type": "case",
                        "target_id": ch.get("case_id"),
                        "case_id": ch.get("case_id"),
                        "client_id": ch.get("client_id"),
                        "question": body.get("question") or f"Анализ изменения: {ch.get('title')}",
                        "text": str(detail),
                    },
                    role,
                )
                created["analysis"] = scrub_secrets(res.get("item") or res.get("analysis") or {})
        else:
            return {"ok": False, "error": "validation", "message_ru": f"Неизвестное действие: {action}"}
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="monitor_change",
            entity_id=change_id,
            action=f"monitor_change_{action}",
            summary=f"Действие по изменению: {action}",
            role=role,
        )
        return {
            "ok": True,
            "action": action,
            "created": created,
            "change_id": change_id,
            "related": {
                "case_id": ch.get("case_id"),
                "client_id": ch.get("client_id"),
                "counterparty": (ch.get("payload") or {}).get("counterparty"),
                "enforcement_id": ch.get("enforcement_id"),
                "source_reference": ch.get("source_reference"),
                "summary": ch.get("summary"),
                "detected_at": ch.get("created_at"),
                "what_changed": ch.get("detail"),
            },
        }

    async def list_enforcement(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        return {"ok": True, "items": active_only(self._bag(org).get("enforcement", [])), "provider": get_legal_data_providers().enforcement.status()}  # type: ignore[attr-defined]

    async def create_enforcement(
        self, organization_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        number = str(body.get("production_number") or "").strip()
        if not number:
            return {"ok": False, "error": "validation", "message_ru": "Укажите номер производства"}
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "production_number": number,
            "client_id": body.get("client_id"),
            "case_id": body.get("case_id"),
            "debtor": body.get("debtor"),
            "creditor": body.get("creditor"),
            "executor": body.get("executor"),
            "status": body.get("status") or "open",
            "opened_at": body.get("opened_at") or _iso(),
            "last_checked_at": None,
            "notes": body.get("notes"),
            "provider": body.get("provider") or "manual_import",
            "payload": body.get("payload") or {},
            "created_at": _iso(),
        }
        saved = await self._persist("enforcement", item)  # type: ignore[attr-defined]
        self._bag(org).setdefault("enforcement", []).insert(0, saved)  # type: ignore[attr-defined]
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="enforcement",
            entity_id=saved["id"],
            action="enforcement_created",
            summary=f"ИП создано: {number}",
            role=role,
        )
        return {"ok": True, "item": saved}

    async def update_enforcement(
        self, organization_id: str, enforcement_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "edit")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        patch: dict[str, Any] = {}
        for key in ("production_number", "debtor", "creditor", "executor", "status", "notes", "case_id", "client_id"):
            if key in body:
                patch[key] = body[key]
        if not patch:
            return {"ok": False, "error": "validation", "message_ru": "Нет полей для обновления"}
        saved = await self._patch_mem(org, "enforcement", enforcement_id, patch)  # type: ignore[attr-defined]
        if not saved:
            return {"ok": False, "error": "not_found", "message_ru": "Исполнительное производство не найдено"}
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="enforcement",
            entity_id=enforcement_id,
            action="enforcement_updated",
            summary="Исполнительное производство изменено",
            role=role,
            payload={"fields": list(patch.keys())},
        )
        return {"ok": True, "item": saved}

    async def list_notifications(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        items = list(self._bag(org).get("notifications", []))  # type: ignore[attr-defined]
        return {"ok": True, "items": items}

    async def run_monitor_sweep(self, organization_id: str | None = None) -> dict[str, Any]:
        """Scheduler entry: check all active watchlist items for org or all hydrated orgs."""
        results = []
        orgs = [organization_id] if organization_id else list(self._mem.keys())  # type: ignore[attr-defined]
        if not orgs:
            # hydrate default for scheduler smoke
            orgs = ["default"]
        for org in orgs:
            if not org:
                continue
            try:
                await self.ensure_hydrated(org)  # type: ignore[attr-defined]
                for w in active_only(self._bag(org).get("watchlist", [])):  # type: ignore[attr-defined]
                    r = await self.check_watchlist_item(org, str(w["id"]), {}, role="platform_owner")
                    results.append({"organization_id": org, "watchlist_id": w["id"], "changes": len(r.get("changes") or [])})
            except Exception as exc:
                logger.warning("legal monitor sweep failed org=%s: %s", org, exc)
                results.append({"organization_id": org, "error": str(exc)})
        return {"ok": True, "checked": len(results), "results": results}

    # --- Google calendar mapping (ADOS → Google) ---

    async def upsert_calendar_mapping(
        self,
        organization_id: str,
        *,
        internal_event_id: str,
        external_event_id: str,
        provider: str = "google",
        external_calendar_id: str | None = "primary",
        sync_direction: str = "ados_to_google",
    ) -> dict[str, Any]:
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org).setdefault("calendar_mappings", [])  # type: ignore[attr-defined]
        existing = next(
            (
                m
                for m in bag
                if str(m.get("internal_event_id")) == str(internal_event_id) and str(m.get("provider")) == provider
            ),
            None,
        )
        if existing:
            # duplicate prevention: keep same external id
            patch = {
                "external_event_id": existing.get("external_event_id") or external_event_id,
                "external_calendar_id": external_calendar_id or existing.get("external_calendar_id"),
                "last_synced_at": _iso(),
                "sync_version": int(existing.get("sync_version") or 1) + 1,
                "sync_direction": sync_direction,
            }
            idx = bag.index(existing)
            cur = dict(existing)
            cur.update(patch)
            bag[idx] = cur
            await self._persist("calendar_mapping", cur)  # type: ignore[attr-defined]
            return cur
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "internal_event_id": internal_event_id,
            "provider": provider,
            "external_calendar_id": external_calendar_id or "primary",
            "external_event_id": external_event_id,
            "sync_version": 1,
            "last_synced_at": _iso(),
            "sync_direction": sync_direction,
            "payload": {},
            "created_at": _iso(),
        }
        saved = await self._persist("calendar_mapping", item)  # type: ignore[attr-defined]
        bag.insert(0, saved)
        return saved

    async def sync_event_with_mapping(
        self, organization_id: str, event_id: str, role: str | None = None
    ) -> dict[str, Any]:
        """ADOS → Google sync using mapping table; never creates duplicate external ids."""
        denied = require(role, "sync")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        settings = (await self.get_monitor_settings(org, role)).get("item") or {}
        gs = settings.get("google_sync") or DEFAULT_GOOGLE_SYNC
        if gs.get("direction") not in {"ados_to_google", "bidirectional"}:
            return {
                "ok": False,
                "error": "direction",
                "message_ru": "В Sprint 3.3 надёжно поддерживается ADOS → Google. Google → ADOS / bidirectional — ограничение.",
            }
        event = next((e for e in self._bag(org)["calendar"] if str(e.get("id")) == str(event_id)), None)  # type: ignore[attr-defined]
        if not event:
            return {"ok": False, "error": "not_found"}
        et = str(event.get("event_type") or "other")
        types = gs.get("types") or {}
        if et in types and not types.get(et, True):
            return {"ok": False, "error": "filtered", "message_ru": f"Тип {et} отключён в настройках синхронизации"}

        from services.legal_ops.calendar_integration import get_calendar_integration

        adapter = get_calendar_integration().google
        mapping = next(
            (
                m
                for m in self._bag(org).get("calendar_mappings", [])  # type: ignore[attr-defined]
                if str(m.get("internal_event_id")) == str(event_id) and m.get("provider") == "google"
            ),
            None,
        )
        payload = dict(event)
        if mapping:
            payload["gcal_event_id"] = mapping.get("external_event_id")
            payload["external_event_id"] = mapping.get("external_event_id")
            res = adapter.update_event(payload)
        else:
            res = adapter.create_event(payload)
        if not res.get("ok"):
            await self._activity(  # type: ignore[attr-defined]
                organization_id=org,
                entity_type="calendar",
                entity_id=event_id,
                action="GOOGLE_SYNC_FAILED",
                summary=res.get("message_ru") or "Google sync failed",
                role=role,
                payload={"error": res.get("sync_status"), "message_ru": res.get("message_ru")},
            )
            return {"ok": False, "sync": scrub_secrets(res), "message_ru": res.get("message_ru")}
        eid = res.get("external_event_id") or res.get("gcal_event_id")
        mapping_row = await self.upsert_calendar_mapping(
            org,
            internal_event_id=event_id,
            external_event_id=str(eid),
            external_calendar_id=gs.get("selected_calendar_id") or "primary",
            sync_direction="ados_to_google",
        )
        await self._patch_mem(  # type: ignore[attr-defined]
            org,
            "calendar",
            event_id,
            {
                "gcal_event_id": eid,
                "external_event_id": eid,
                "external_provider": "google",
                "sync_status": res.get("sync_status") or "synced",
            },
        )
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="calendar",
            entity_id=event_id,
            action="GOOGLE_SYNC",
            summary="Синхронизация Google Calendar (ADOS → Google)",
            role=role,
            payload={"external_event_id": eid, "mapping_id": mapping_row.get("id")},
        )
        return {"ok": True, "sync": scrub_secrets(res), "mapping": mapping_row}

    async def disconnect_google(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "sync")
        if denied:
            return denied
        from services.legal_ops import google_calendar as gcal
        import services.legal_ops.calendar_integration as ci

        gcal.clear_org_refresh_token(organization_id)
        ci._INT = None
        await self._activity(  # type: ignore[attr-defined]
            organization_id=organization_id,
            entity_type="integration",
            entity_id="google_calendar",
            action="GOOGLE_DISCONNECTED",
            summary="Google Calendar отключён",
            role=role,
        )
        return {"ok": True, **scrub_secrets(self.gcal_status())}  # type: ignore[attr-defined]
