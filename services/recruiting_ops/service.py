"""Recruiting Ops service — durable ATS desk (Sprint Recruiting 1.0).

Org-scoped memory bags hydrated from and persisted to Postgres
(`recruiting_ops_records`). Memory fallback is DEV/test only.
Production Vanguard ingest never reports success for a memory-only lead.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from repositories.recruiting_ops_repository import RecruitingOpsRepository, record_to_dict
from services.recruiting_ops.projects import (
    belongs_to_project,
    canonical_vanguard_org,
    get_project,
    infer_project_key,
    project_catalog,
    resolve_project_key,
    status_payload,
    vanguard_org_aliases,
    vanguard_read_org_keys,
    vanguard_website_url,
    STATUS_CONNECTED,
    STATUS_DEGRADED,
    STATUS_DISCONNECTED,
    STATUS_NOT_CONFIGURED,
    STATUS_UNKNOWN,
    VANGUARD_PROJECT_KEY,
)
from services.recruiting_ops.rbac import can, normalize_role, require, require_provider_admin, roles_catalog
from services.recruiting_ops.runtime import is_production_runtime, memory_fallback_allowed
from services.recruiting_ops.shared_store import get_store
from services.recruiting_ops.tracking_worker import get_tracking_worker

logger = logging.getLogger(__name__)

KINDS = (
    "lead",
    "candidate",
    "vacancy",
    "campaign",
    "task",
    "communication",
    "activity",
    "tracking",
    "idempotency",
    "ad_account",
    "ad_set",
    "creative",
    "audience",
    "ads_metrics",
    "provider_connection",
    "automation_rule",
    "automation_run",
    "ai_recommendation",
    "campaign_write",
    "outbound_message",
    "email_suppression",
    "whatsapp_message",
    "whatsapp_phone_map",
    "campaign_spend",
    "provider_mapping",
    "provider_sync_run",
)

LEAD_STATUSES = ("new", "qualified", "converted", "lost")
PIPELINE_STAGES = ("NEW", "QUALIFIED", "INTERVIEW", "APPROVED", "HIRED", "REJECTED")
TASK_STATUSES = ("open", "done", "cancelled")
COMM_CHANNELS = ("TELEGRAM", "WHATSAPP", "EMAIL", "PHONE", "MANUAL")
CAMPAIGN_CHANNELS = (
    "Google",
    "Meta",
    "Instagram",
    "TikTok",
    "Telegram",
    "YouTube",
    "Organic",
    "Referral",
    "Direct",
    "Other",
)
TASK_TEMPLATES = (
    "Позвонить",
    "Написать",
    "Провести интервью",
    "Проверить анкету",
    "Отправить приглашение",
)

VISITS_UNAVAILABLE = {
    "available": False,
    "count": None,
    "message_ru": "Нет данных о посещениях",
    "reason": "vanguard_not_connected",
}

class PersistUnavailable(RuntimeError):
    """Raised when production storage failed and memory must not be treated as success."""


VANGUARD_CONTRACT = {
    "status": "ingest_ready",
    "connected": False,
    "integration": "vanguard_website",
    "message_ru": "Inbound HMAC endpoint готов. Сайт Vanguard в этом репозитории отсутствует — форму нужно подключить отдельно.",
    "inbound": {
        "method": "POST",
        "path": "/api/recruiting-ops/v1/vanguard/leads",
        "auth": "hmac-sha256",
        "headers": [
            "X-Vanguard-Signature",
            "X-Vanguard-Timestamp",
            "X-Vanguard-Nonce",
        ],
        "signature_message": "{timestamp}.{nonce}.{raw_body}",
        "secret_location": "server_env:VANGUARD_INGEST_SECRET",
        "secret_frontend_exposure": False,
        "required": ["first_name|name", "email|phone"],
        "optional": [
            "last_name",
            "source",
            "campaign_id",
            "vacancy_id",
            "vacancy",
            "external_id",
            "reference",
            "project_key",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "utm_term",
            "age",
            "contact_consent",
            "country",
            "preferred_language",
            "program_of_interest",
            "unit_of_interest",
            "application_message",
            "gclid",
            "fbclid",
            "click_id",
            "notes",
        ],
        "example": {
            "first_name": "Иван",
            "last_name": "Петров",
            "phone": "+380501112233",
            "email": "ivan@example.com",
            "age": 24,
            "contact_consent": True,
            "source": "vanguard-global",
            "project_key": "vanguard",
            "vacancy_id": "vac-1",
            "external_id": "vg-1001",
            "utm_source": "vanguard",
            "utm_medium": "website",
            "utm_campaign": "career",
            "utm_content": "hero",
            "utm_term": "intern",
            "gclid": "gclid-example",
            "fbclid": "fbclid-example",
            "click_id": "click-example",
        },
        "duplicate_policy": "same external_id + same vacancy → handled as duplicate; different vacancy → new lead",
    },
    "channels_prepared": list(COMM_CHANNELS),
    "ads_apis": {
        "meta": "not_connected",
        "google": "not_connected",
        "tiktok": "not_connected",
    },
    "messaging_apis": {
        "telegram": "not_connected",
        "whatsapp": "not_connected",
        "email": "not_connected",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _org(organization_id: str | None, tenant_id: str | None = None) -> str:
    return (organization_id or tenant_id or "default").strip() or "default"


def _txt(value: Any) -> str:
    return str(value or "").strip()


def _stage(value: Any, default: str = "NEW") -> str:
    raw = _txt(value).upper().replace(" ", "_")
    aliases = {
        "SCREENING": "NEW",
        "NEW_LEAD": "NEW",
        "QUALIFIED_LEAD": "QUALIFIED",
        "INTERVIEWING": "INTERVIEW",
        "OFFER": "APPROVED",
        "HIRE": "HIRED",
        "REJECT": "REJECTED",
    }
    raw = aliases.get(raw, raw)
    return raw if raw in PIPELINE_STAGES else default


def _lead_status(value: Any, default: str = "new") -> str:
    raw = _txt(value).lower()
    return raw if raw in LEAD_STATUSES else default


def _task_status(value: Any, default: str = "open") -> str:
    raw = _txt(value).lower()
    aliases = {"todo": "open", "pending": "open", "completed": "done", "complete": "done"}
    raw = aliases.get(raw, raw)
    return raw if raw in TASK_STATUSES else default


def _channel(value: Any) -> str:
    raw = _txt(value).upper()
    return raw if raw in COMM_CHANNELS else "MANUAL"


def _parse_date(value: Any) -> str | None:
    text = _txt(value)
    return text or None


def _date_only(value: Any) -> str:
    text = _txt(value)
    if not text:
        return ""
    return text[:10]


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


class RecruitingOpsService:
    """Org-scoped recruiting desk with Postgres persistence + memory fallback."""

    def __init__(self) -> None:
        self._mem: dict[str, dict[str, list[dict[str, Any]]]] = {}
        self._hydrated: set[str] = set()
        self._lifecycle_migrated: set[str] = set()
        self._hydrate_locks: dict[str, asyncio.Lock] = {}
        self._convert_locks: dict[str, asyncio.Lock] = {}
        self._identity_locks: dict[str, asyncio.Lock] = {}
        self._merge_locks: dict[str, asyncio.Lock] = {}
        self._ingest_log: dict[str, Any] = {
            "last_success_at": None,
            "last_error_at": None,
            "last_error": None,
            "last_check_at": None,
            "last_successful_check_at": None,
        }

    def _bag(self, org: str) -> dict[str, list[dict[str, Any]]]:
        if org not in self._mem:
            self._mem[org] = {k: [] for k in KINDS}
        bag = self._mem[org]
        for kind in KINDS:
            bag.setdefault(kind, [])
        return bag

    async def ensure_hydrated(self, organization_id: str) -> None:
        org = _org(organization_id)
        if org in self._hydrated:
            return
        lock = self._hydrate_locks.setdefault(org, asyncio.Lock())
        async with lock:
            if org in self._hydrated:
                return
            loaded = False
            try:
                from database.session import get_session

                async with get_session() as session:
                    repo = RecruitingOpsRepository(session)
                    bag = self._bag(org)
                    for kind in KINDS:
                        rows = await repo.list_kind(org, kind)
                        db_items = [record_to_dict(r) for r in rows]
                        merged: dict[str, dict[str, Any]] = {str(item.get("id")): item for item in bag[kind] if item.get("id")}
                        for row in db_items:
                            merged[str(row.get("id"))] = row
                        bag[kind] = list(merged.values())
                loaded = True
            except Exception as exc:
                logger.warning("recruiting_ops hydrate skipped org=%s: %s", org, exc)
            if loaded:
                self._hydrated.add(org)
            from services.recruiting_ops.tracking_worker import get_tracking_worker

            get_tracking_worker().ensure_loop(self.process_tracking_retries)
            if org not in self._lifecycle_migrated:
                self._lifecycle_migrated.add(org)
                if os.environ.get("PYTEST_CURRENT_TEST"):
                    get_tracking_worker().sync_with(self._bag(org).get("tracking") or [])
                else:
                    await self._recover_tracking_unlocked(org)
            else:
                get_tracking_worker().sync_with(self._bag(org).get("tracking") or [])
            self._sync_runtime_connections(org)
            self._index_whatsapp_phone_maps()

    def _owner_read(self, role: str | None) -> bool:
        return normalize_role(role) in {"platform_owner", "owner"}

    def _read_orgs(self, organization_id: str, role: str | None) -> list[str]:
        requested = _org(organization_id)
        orgs = [requested] if requested else []
        if self._owner_read(role) and requested.lower() in set(vanguard_read_org_keys()):
            for alias in vanguard_org_aliases():
                if alias not in orgs:
                    orgs.append(alias)
        return orgs

    def _collect_kind(self, orgs: list[str], kind: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        for org in orgs:
            for item in self._bag(org).get(kind) or []:
                item_id = str(item.get("id") or "")
                if item_id and item_id in seen:
                    continue
                if item_id:
                    seen.add(item_id)
                out.append(item)
        out.sort(key=lambda item: str(item.get("created_at") or item.get("submitted_at") or ""), reverse=True)
        return out

    async def _locate(
        self,
        organization_id: str,
        kind: str,
        item_id: str,
        role: str | None,
    ) -> tuple[str, dict[str, Any] | None]:
        for org in self._read_orgs(organization_id, role):
            await self.ensure_hydrated(org)
            found = self._find(org, kind, item_id)
            if found:
                return org, found
        return _org(organization_id), None

    async def _reader_items(
        self,
        organization_id: str,
        kind: str,
        role: str | None,
    ) -> tuple[str, list[str], list[dict[str, Any]]]:
        orgs = self._read_orgs(organization_id, role)
        for org in orgs:
            await self.ensure_hydrated(org)
        items = self._collect_kind(orgs, kind)
        logger.info(
            "RECRUITING_READ_SCOPE requested=%s orgs=%s kind=%s count=%s role=%s",
            _org(organization_id),
            ",".join(orgs),
            kind,
            len(items),
            normalize_role(role),
        )
        return _org(organization_id), orgs, items

    async def _persist(self, kind: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = RecruitingOpsRepository(session)
                row = await repo.insert(kind, data)
                flags = {
                    "storage": "postgres",
                    "durable": True,
                    "persistence_mode": "POSTGRES",
                }
                await repo.update(row, flags)
                saved = record_to_dict(row)
                saved.update(flags)
                return saved
        except Exception as exc:
            if not memory_fallback_allowed():
                logger.error("recruiting_ops persist %s failed in production: %s", kind, exc)
                raise PersistUnavailable(str(exc)) from exc
            logger.warning("recruiting_ops persist %s failed (NON_DURABLE_DEVELOPMENT_MODE): %s", kind, exc)
            data["storage"] = "memory"
            data["durable"] = False
            data["persistence_mode"] = "NON_DURABLE_DEVELOPMENT_MODE"
            return data

    async def _persist_patch(self, org: str, item_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = RecruitingOpsRepository(session)
                row = await repo.get(org, item_id)
                if row:
                    await repo.update(row, patch)
                    return record_to_dict(row)
        except Exception as exc:
            if not memory_fallback_allowed():
                logger.error("recruiting_ops patch persist failed in production: %s", exc)
                raise PersistUnavailable(str(exc)) from exc
            logger.warning("recruiting_ops patch persist skipped (NON_DURABLE_DEVELOPMENT_MODE): %s", exc)
        return None

    def _find(self, org: str, kind: str, item_id: str) -> dict[str, Any] | None:
        for item in self._bag(org)[kind]:
            if str(item.get("id")) == str(item_id):
                return item
        return None

    def _replace(self, org: str, kind: str, item: dict[str, Any]) -> None:
        items = self._bag(org)[kind]
        for idx, existing in enumerate(items):
            if str(existing.get("id")) == str(item.get("id")):
                items[idx] = item
                return
        items.insert(0, item)

    async def _activity(
        self,
        *,
        organization_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        summary: str,
        role: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        org = _org(organization_id)
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "actor_role": normalize_role(role),
            "summary": summary,
            "payload": payload or {},
            "project_key": infer_project_key(
                project_key=_txt((payload or {}).get("project_key")),
                source=_txt((payload or {}).get("source")),
            ),
            "data_mode": "REAL",
            "created_at": _now(),
            "status": "recorded",
        }
        try:
            saved = await self._persist("activity", item)
        except PersistUnavailable:
            logger.error("recruiting_ops activity persist failed in production")
            item["storage"] = "unpersisted"
            item["durable"] = False
            saved = item
        self._bag(org)["activity"].insert(0, saved)
        return saved

    def roles(self) -> list[dict[str, Any]]:
        return roles_catalog()

    def catalogs(self) -> dict[str, Any]:
        from services.recruiting_ops.ads_economics import CAMPAIGN_SOURCES
        from services.recruiting_ops.ads_foundation import ads_foundation

        return {
            "ok": True,
            "lead_statuses": list(LEAD_STATUSES),
            "pipeline_stages": list(PIPELINE_STAGES),
            "task_statuses": list(TASK_STATUSES),
            "task_templates": list(TASK_TEMPLATES),
            "communication_channels": list(COMM_CHANNELS),
            "campaign_channels": list(CAMPAIGN_CHANNELS),
            "projects": project_catalog(),
            "tracking_events": [
                "page_view",
                "application_open",
                "application_start",
                "application_submit",
                "application_success",
            ],
            "data_modes": ["REAL", "DEMO", "NON_DURABLE_DEVELOPMENT_MODE", "LIVE", "MOCK"],
            "ads": ads_foundation(),
            "campaign_statuses": ["DRAFT", "READY", "ACTIVE", "PAUSED", "COMPLETED", "FAILED"],
            "providers": ["meta", "google", "tiktok", "telegram", "whatsapp", "email"],
            "campaign_sources": list(CAMPAIGN_SOURCES),
        }

    def vanguard_contract(self) -> dict[str, Any]:
        from services.recruiting_ops.ingest_auth import resolve_ingest_secret

        return {
            "ok": True,
            **VANGUARD_CONTRACT,
            "data_mode": "REAL",
            "ingest_secret_configured": bool(resolve_ingest_secret()),
            "production": is_production_runtime(),
            "memory_fallback_allowed": memory_fallback_allowed(),
        }

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "sprint": "recruiting_1.12",
            "vanguard": {
                "connected": False,
                "status": "ingest_ready",
                "inbound": "/api/recruiting-ops/v1/vanguard/leads",
            },
            "visits_available": False,
            "production": is_production_runtime(),
            "memory_fallback_allowed": memory_fallback_allowed(),
            "roles": self.roles(),
            "rate_limit_store": get_store().describe(),
            "replay_store": get_store().describe(),
            "tracking_worker": get_tracking_worker().snapshot(),
            "tracking_health": self.tracking_diagnostics(),
            "ads": {"connected": False, "message_ru": "Провайдер не подключен"},
            "telegram": {"frozen": True, "status": "DISABLED", "blocks_readiness": False},
            "whatsapp": self._whatsapp_health_payload(),
        }

    def _whatsapp_health_payload(self) -> dict[str, Any]:
        from services.recruiting_ops.secret_store import get_secret_store
        from services.recruiting_ops.whatsapp_ops import env_readiness

        store = get_secret_store()
        env = env_readiness(
            store_present={
                "access_token": bool(store.get("whatsapp", "access_token")),
                "phone_number_id": bool(store.get("whatsapp", "phone_number_id")),
                "verify_token": bool(store.get("whatsapp", "verify_token")),
                "app_secret": bool(store.get("whatsapp", "app_secret")),
                "business_account_id": bool(store.get("whatsapp", "business_account_id")),
            }
        )
        return {
            "health_sends_message": False,
            "approval_required": True,
            "env_status": env["status"],
            "status": env["status"],
            "present": env["present"],
            "missing": env["missing"],
            "alias_used": env["alias_used"],
            "message_ru": env["message_ru"],
            "live_verified": False,
        }

    def tracking_diagnostics(self) -> dict[str, Any]:
        from services.recruiting_ops.tracking_health import build_tracking_diagnostics

        org = _org(os.getenv("VANGUARD_ORGANIZATION_ID") or "ados")
        events = self._bag(org).get("tracking") or []
        return build_tracking_diagnostics(events)

    async def recover_tracking_records(self, organization_id: str | None = None) -> dict[str, Any]:
        org = _org(organization_id or os.getenv("VANGUARD_ORGANIZATION_ID") or "ados")
        await self.ensure_hydrated(org)
        return await self._recover_tracking_unlocked(org)

    async def _recover_tracking_unlocked(self, org: str) -> dict[str, Any]:
        from services.recruiting_ops.tracking_lifecycle import migration_patch, should_recover_to_delivered

        recovered: list[str] = []
        inspected: list[dict[str, Any]] = []
        before = {"RETRYING": 0, "DELIVERED": 0, "WAITING_PROVIDER": 0, "DEAD_LETTER": 0, "PENDING": 0, "empty": 0}
        after: dict[str, int] = {}
        for item in list(self._bag(org).get("tracking") or []):
            status = _txt(item.get("delivery_status"))
            before[status if status in before else ("empty" if not status else status)] = before.get(
                status if status in before else ("empty" if not status else status), 0
            ) + 1
            patch = migration_patch(item)
            if patch is None and should_recover_to_delivered(item):
                patch = {
                    "delivery_status": "DELIVERED",
                    "delivery_class": "delivered",
                    "recovery_reason": "persisted_in_postgres",
                    "destination": item.get("destination") or "recruiting_db",
                    "durable": True,
                    "storage": item.get("storage") or "postgres",
                    "persistence_mode": "POSTGRES",
                }
            inspected.append(
                {
                    "id": item.get("id"),
                    "delivery_status": status,
                    "durable": bool(item.get("durable")),
                    "storage": item.get("storage"),
                    "destination": item.get("destination") or "recruiting_db",
                    "will_recover": bool(patch),
                }
            )
            if not patch:
                continue
            persisted = await self._persist_patch(org, str(item.get("id")), patch)
            if persisted:
                item.update(persisted)
            else:
                item.update(patch)
            recovered.append(str(item.get("id")))
        for item in self._bag(org).get("tracking") or []:
            st = _txt(item.get("delivery_status")) or "empty"
            after[st] = after.get(st, 0) + 1
        from services.recruiting_ops.tracking_worker import get_tracking_worker

        get_tracking_worker().sync_with(self._bag(org).get("tracking") or [])
        return {
            "ok": True,
            "recovered": len(recovered),
            "ids": recovered,
            "inspected": inspected,
            "deleted": 0,
            "before": before,
            "after": after,
        }

    async def infrastructure_diagnostics(self) -> dict[str, Any]:
        from services.recruiting_ops.ops_diagnostics import build_ops_diagnostics

        return await build_ops_diagnostics(self)

    def _ok(self, **extra: Any) -> dict[str, Any]:
        return {"ok": True, "data_mode": "REAL", **extra}

    def _hours_old(self, value: Any) -> float | None:
        raw = _txt(value)
        if not raw:
            return None
        try:
            stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - stamp).total_seconds() / 3600.0
        except ValueError:
            return None

    def _recruiter_directory(self, *groups: list[dict[str, Any]]) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        seen: set[str] = set()
        for group in groups:
            for row in group:
                name = _txt(row.get("assignee"))
                key = name.lower()
                if not name or key in seen:
                    continue
                seen.add(key)
                items.append({"id": name, "label": name})
        return items

    def _attention_items(
        self,
        leads: list[dict[str, Any]],
        candidates: list[dict[str, Any]],
        overdue: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        summary: list[dict[str, Any]] = []
        items: list[dict[str, Any]] = []
        if overdue:
            summary.append({"kind": "overdue_tasks", "count": len(overdue), "message_ru": f"Просрочено задач: {len(overdue)}"})
            for task in overdue[:8]:
                items.append(
                    {
                        "kind": "overdue_task",
                        "entity_type": "task",
                        "entity_id": _txt(task.get("id")),
                        "name": _txt(task.get("title")) or "Задача",
                        "message_ru": f"Просрочена задача: {task.get('title') or task.get('id')}",
                    }
                )
        for lead in leads:
            status = _lead_status(lead.get("status"))
            if status == "converted":
                continue
            name = _txt(lead.get("name")) or "Лид"
            lead_id = _txt(lead.get("id"))
            if not _txt(lead.get("assignee")):
                items.append(
                    {
                        "kind": "unassigned",
                        "entity_type": "lead",
                        "entity_id": lead_id,
                        "name": name,
                        "message_ru": f"Лид без ответственного: {name}",
                    }
                )
            if not _txt(lead.get("vacancy_id") or lead.get("vacancy")):
                items.append(
                    {
                        "kind": "no_vacancy",
                        "entity_type": "lead",
                        "entity_id": lead_id,
                        "name": name,
                        "message_ru": f"Лид без вакансии: {name}",
                    }
                )
            age_h = self._hours_old(lead.get("submitted_at") or lead.get("created_at"))
            if status == "new" and age_h is not None and age_h >= 24:
                items.append(
                    {
                        "kind": "stale_new",
                        "entity_type": "lead",
                        "entity_id": lead_id,
                        "name": name,
                        "message_ru": f"Новый лид старше 24 часов: {name}",
                    }
                )
        waiting = [c for c in candidates if _stage(c.get("pipeline_stage")) in {"NEW", "QUALIFIED"}]
        for cand in waiting[:8]:
            items.append(
                {
                    "kind": "awaiting_interview",
                    "entity_type": "candidate",
                    "entity_id": _txt(cand.get("id")),
                    "name": _txt(cand.get("name")) or "Кандидат",
                    "message_ru": f"Кандидат ожидает интервью: {cand.get('name') or cand.get('id')}",
                }
            )
        unassigned = [l for l in leads if not _txt(l.get("assignee")) and _lead_status(l.get("status")) != "converted"]
        if unassigned:
            summary.append({"kind": "unassigned_leads", "count": len(unassigned), "message_ru": f"Лиды без рекрутера: {len(unassigned)}"})
        no_vacancy = [
            l
            for l in leads
            if not _txt(l.get("vacancy_id") or l.get("vacancy")) and _lead_status(l.get("status")) != "converted"
        ]
        if no_vacancy:
            summary.append({"kind": "leads_without_vacancy", "count": len(no_vacancy), "message_ru": f"Лиды без вакансии: {len(no_vacancy)}"})
        if waiting:
            summary.append({"kind": "awaiting_interview", "count": len(waiting), "message_ru": f"Кандидаты ожидают интервью: {len(waiting)}"})
        return summary, items

    async def dashboard(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.recruiting_ops.identity import is_merged_candidate

        org, orgs, leads = await self._reader_items(organization_id, "lead", role)
        candidates = [c for c in self._collect_kind(orgs, "candidate") if not is_merged_candidate(c)]
        vacancies = self._collect_kind(orgs, "vacancy")
        tasks = self._collect_kind(orgs, "task")
        bag = {kind: self._collect_kind(orgs, kind) for kind in ("lead", "candidate", "vacancy", "task", "campaign")}
        overdue, upcoming = self._task_buckets(tasks)
        attention, attention_items = self._attention_items(leads, candidates, overdue)
        new_leads = [l for l in leads if _lead_status(l.get("status")) == "new"]
        qualified = [l for l in leads if _lead_status(l.get("status")) in {"qualified", "converted"}]
        interviews = [c for c in candidates if _stage(c.get("pipeline_stage")) == "INTERVIEW"]
        hired = [c for c in candidates if _stage(c.get("pipeline_stage")) == "HIRED"]
        return self._ok(
            cards={
                "leads": len(leads),
                "candidates": len(candidates),
                "vacancies": len(vacancies),
                "overdue_tasks": len(overdue),
                "next_tasks": len(upcoming),
                "new_leads": len(new_leads),
                "qualified": len(qualified),
                "interviews": len(interviews),
                "hired": len(hired),
            },
            overdue_tasks=overdue[:10],
            next_tasks=upcoming[:10],
            attention=attention,
            attention_items=attention_items[:20],
            recruiters=self._recruiter_directory(leads, candidates, tasks),
            visits=VISITS_UNAVAILABLE,
            vanguard=self.vanguard_contract(),
            projects=self._project_summaries(org, bag),
            read_organization_id=org,
            read_organization_ids=orgs,
        )

    def _task_buckets(self, tasks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        today = _today()
        open_tasks = [t for t in tasks if _task_status(t.get("status")) == "open"]
        overdue = [t for t in open_tasks if _date_only(t.get("due_date")) and _date_only(t.get("due_date")) < today]
        upcoming = [
            t
            for t in open_tasks
            if not _date_only(t.get("due_date")) or _date_only(t.get("due_date")) >= today
        ]
        overdue.sort(key=lambda t: _date_only(t.get("due_date")) or "")
        upcoming.sort(key=lambda t: _date_only(t.get("due_date")) or "9999-12-31")
        return overdue, upcoming

    async def analytics(self, organization_id: str, role: str | None = None, *, project: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        orgs = self._read_orgs(organization_id, role)
        for read_org in orgs:
            await self.ensure_hydrated(read_org)
        bag = {kind: self._collect_kind(orgs, kind) for kind in ("lead", "candidate", "vacancy", "campaign", "tracking")}
        key = _txt(project).lower()
        leads = list(bag["lead"])
        candidates = list(bag["candidate"])
        if key:
            leads = [item for item in leads if belongs_to_project(item, key)]
            candidates = [item for item in candidates if belongs_to_project(item, key)]
        from services.recruiting_ops.attribution import production_cohort

        cohort = production_cohort(leads, candidates)
        leads = list(cohort["leads"])
        candidates = list(cohort["candidates"] or [])
        vacancies = {str(v.get("id")): _txt(v.get("title")) or str(v.get("id")) for v in bag["vacancy"]}
        campaigns = {str(c.get("id")): _txt(c.get("name")) or str(c.get("id")) for c in bag["campaign"]}

        def _count_by(items: list[dict[str, Any]], key: str, labels: dict[str, str] | None = None) -> list[dict[str, Any]]:
            tallies: dict[str, int] = {}
            for item in items:
                raw = _txt(item.get(key)) or "—"
                tallies[raw] = tallies.get(raw, 0) + 1
            out = []
            for raw, count in sorted(tallies.items(), key=lambda x: (-x[1], x[0])):
                out.append(
                    {
                        "id": raw,
                        "label": (labels or {}).get(raw, raw),
                        "count": count,
                    }
                )
            return out

        stages = {stage: 0 for stage in PIPELINE_STAGES}
        from services.recruiting_ops.identity import is_merged_candidate

        active_candidates = [cand for cand in candidates if not is_merged_candidate(cand)]
        for cand in active_candidates:
            stages[_stage(cand.get("pipeline_stage"))] = stages.get(_stage(cand.get("pipeline_stage")), 0) + 1

        qualified_leads = [l for l in leads if _lead_status(l.get("status")) in {"qualified", "converted"}]
        interviews = stages["INTERVIEW"] + stages["APPROVED"] + stages["HIRED"]
        approved = stages["APPROVED"] + stages["HIRED"]
        hired = stages["HIRED"]

        return self._ok(
            visits=VISITS_UNAVAILABLE,
            funnel={
                "visits": None,
                "leads": len(leads),
                "qualified": len(qualified_leads),
                "interviews": interviews,
                "approved": approved,
                "hired": hired,
            },
            pipeline_stages=stages,
            by_source=_count_by(leads, "source"),
            by_campaign=_count_by(leads, "campaign_id", campaigns),
            by_vacancy=_count_by(leads + candidates, "vacancy_id", vacancies),
            project=key or None,
            traffic={
                "production_only": True,
                "excluded_test_leads": cohort["excluded_test_leads"],
                "excluded_test_candidates": cohort["excluded_test_candidates"],
            },
        )

    async def list_kind(
        self,
        organization_id: str,
        kind: str,
        role: str | None = None,
        *,
        project: str | None = None,
    ) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        orgs = self._read_orgs(organization_id, role)
        for read_org in orgs:
            await self.ensure_hydrated(read_org)
        items = self._collect_kind(orgs, kind)
        logger.info(
            "RECRUITING_READ_SCOPE requested=%s orgs=%s kind=%s count=%s role=%s",
            org,
            ",".join(orgs),
            kind,
            len(items),
            normalize_role(role),
        )
        key = _txt(project).lower()
        if key:
            items = self._filter_project_items(org, kind, items, key)
        extra: dict[str, Any] = {}
        if kind == "task":
            overdue, upcoming = self._task_buckets(items)
            extra = {"overdue_tasks": overdue, "next_tasks": upcoming}
        if kind == "candidate":
            from services.recruiting_ops.identity import annotate_duplicate_flags, is_merged_candidate

            items = [self._with_application_links(item) for item in items if not is_merged_candidate(item)]
            items = annotate_duplicate_flags(items)
            extra = {"pipeline": self._pipeline_groups(items)}
        return self._ok(items=items, project=key or None, **extra)

    def _filter_project_items(
        self,
        org: str,
        kind: str,
        items: list[dict[str, Any]],
        project_key: str,
    ) -> list[dict[str, Any]]:
        if kind in {"lead", "candidate", "campaign", "ad_account", "ad_set", "creative", "audience", "ads_metrics"}:
            return [item for item in items if belongs_to_project(item, project_key)]
        if kind in {"communication", "task"}:
            bag = self._bag(org)
            related_ids = {
                _txt(row.get("id"))
                for row in bag["lead"] + bag["candidate"]
                if belongs_to_project(row, project_key)
            }
            return [
                item
                for item in items
                if belongs_to_project(item, project_key)
                or _txt(item.get("lead_id")) in related_ids
                or _txt(item.get("candidate_id")) in related_ids
            ]
        if kind == "activity":
            bag = self._bag(org)
            entity_ids = {
                _txt(row.get("id"))
                for row in bag["lead"] + bag["candidate"] + bag["campaign"] + bag["vacancy"]
                if belongs_to_project(row, project_key)
            }
            return [
                item
                for item in items
                if belongs_to_project(item, project_key)
                or _txt(item.get("entity_id")) in entity_ids
                or project_key in _txt(item.get("action")).lower()
            ]
        if kind == "vacancy":
            bag = self._bag(org)
            related_ids = {
                _txt(row.get("vacancy_id"))
                for row in bag["lead"] + bag["candidate"] + bag["campaign"]
                if belongs_to_project(row, project_key) and _txt(row.get("vacancy_id"))
            }
            return [
                item
                for item in items
                if belongs_to_project(item, project_key) or _txt(item.get("id")) in related_ids
            ]
        return [item for item in items if belongs_to_project(item, project_key)]

    def _pipeline_groups(self, candidates: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        from services.recruiting_ops.identity import is_merged_candidate

        groups = {stage: [] for stage in PIPELINE_STAGES}
        for cand in candidates:
            if is_merged_candidate(cand):
                continue
            groups.setdefault(_stage(cand.get("pipeline_stage")), []).append(cand)
        return groups

    async def create_lead(
        self,
        organization_id: str,
        body: dict[str, Any],
        role: str | None = None,
        *,
        require_durable: bool | None = None,
    ) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        first = _txt(body.get("first_name"))
        last = _txt(body.get("last_name"))
        name = _txt(body.get("name") or body.get("full_name") or " ".join(p for p in (first, last) if p))
        if not name:
            return {"ok": False, "error": "validation", "message_ru": "Укажите имя лида"}
        from services.recruiting_ops.ingest_fields import parse_application_fields

        app_fields, app_error = parse_application_fields(body)
        if app_error:
            return app_error
        org = _org(organization_id, body.get("tenant_id"))
        await self.ensure_hydrated(org)
        vacancy = _txt(body.get("vacancy_id") or body.get("vacancy")) or None
        item = {
            "id": str(body.get("id") or uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "name": name,
            "first_name": first or None,
            "last_name": last or None,
            "phone": app_fields.get("phone") if app_fields else _txt(body.get("phone")),
            "email": _txt(body.get("email")),
            "source": _txt(body.get("source")) or "manual",
            "project_key": infer_project_key(
                source=_txt(body.get("source")) or "manual",
                project_key=_txt(body.get("project_key")) or None,
            ),
            "campaign_id": _txt(body.get("campaign_id")) or None,
            "vacancy_id": vacancy,
            "vacancy": _txt(body.get("vacancy")) or vacancy,
            "external_id": _txt(body.get("external_id") or body.get("reference") or body.get("reference_id") or body.get("idempotency_key")) or None,
            "idempotency_key": _txt(body.get("idempotency_key") or body.get("external_id")) or None,
            "assignee": _txt(body.get("assignee")) or None,
            "status": _lead_status(body.get("status"), "new"),
            "notes": _txt(body.get("notes")),
            "utm_source": _txt(body.get("utm_source")) or None,
            "utm_medium": _txt(body.get("utm_medium")) or None,
            "utm_campaign": _txt(body.get("utm_campaign")) or None,
            "utm_content": _txt(body.get("utm_content")) or None,
            "utm_term": _txt(body.get("utm_term")) or None,
            "country": _txt(body.get("country")) or None,
            "preferred_language": _txt(body.get("preferred_language") or body.get("language")) or None,
            "unit_of_interest": _txt(body.get("unit_of_interest") or body.get("unit")) or None,
            "program_of_interest": _txt(body.get("program_of_interest") or body.get("program") or body.get("vacancy")) or None,
            "application_message": _txt(body.get("application_message") or body.get("message") or body.get("reason") or body.get("notes")) or None,
            "submitted_at": _txt(body.get("submitted_at")) or _now(),
            "visitor_id": _txt(body.get("visitor_id")) or None,
            "session_id": _txt(body.get("session_id")) or None,
            "referrer": _txt(body.get("referrer")) or None,
            "landing_page": _txt(body.get("landing_page")) or None,
            "candidate_id": None,
            "data_mode": "REAL",
            "created_at": _now(),
            "updated_at": _now(),
        }
        from services.recruiting_ops.attribution import TEST_TRAFFIC_CLASS, classify_traffic, touch_payload

        item.update(touch_payload(body))
        if app_fields:
            item.update(app_fields)
        explicit = _txt(body.get("traffic_class")).upper()
        item["traffic_class"] = (
            TEST_TRAFFIC_CLASS
            if classify_traffic(item) == TEST_TRAFFIC_CLASS or explicit in {TEST_TRAFFIC_CLASS, "E2E"}
            else "PRODUCTION"
        )
        must_be_durable = is_production_runtime() if require_durable is None else require_durable
        try:
            saved = await self._persist("lead", item)
        except PersistUnavailable:
            return {
                "ok": False,
                "error": "storage_unavailable",
                "message_ru": "Не удалось сохранить лид в PostgreSQL. Заявка не принята.",
            }
        if must_be_durable and not saved.get("durable"):
            return {
                "ok": False,
                "error": "storage_unavailable",
                "message_ru": "Не удалось сохранить лид в PostgreSQL. Заявка не принята.",
            }
        self._bag(org)["lead"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="lead",
            entity_id=str(saved["id"]),
            action="lead_created",
            summary=f"Лид создан: {name}",
            role=role,
            payload={
                "source": saved.get("source"),
                "vacancy_id": saved.get("vacancy_id"),
                "external_id": saved.get("external_id"),
                "utm_source": saved.get("utm_source"),
                "utm_campaign": saved.get("utm_campaign"),
            },
        )
        return self._ok(item=saved)

    def _identity_keys(self, *values: Any) -> set[str]:
        keys = {_txt(value) for value in values}
        keys.discard("")
        return keys

    def _vacancy_same(self, item: dict[str, Any], vacancy_id: str | None) -> bool:
        stored = _txt(item.get("vacancy_id") or item.get("vacancy"))
        incoming = _txt(vacancy_id)
        if stored or incoming:
            return stored == incoming
        return True

    def _find_duplicate(
        self,
        org: str,
        *,
        external_id: str | None,
        vacancy_id: str | None,
        email: str | None = None,
        program: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any] | None:
        incoming_ids = self._identity_keys(external_id, idempotency_key)
        if incoming_ids:
            for item in self._bag(org)["lead"]:
                stored_ids = self._identity_keys(item.get("external_id"), item.get("idempotency_key"))
                if incoming_ids & stored_ids and self._vacancy_same(item, vacancy_id):
                    return item
            return None
        email_n = _txt(email).lower()
        prog = _txt(program or vacancy_id)
        if email_n and prog:
            for item in self._bag(org)["lead"]:
                if _txt(item.get("email")).lower() != email_n:
                    continue
                if _txt(item.get("program_of_interest") or item.get("vacancy_id") or item.get("vacancy")) == prog:
                    return item
        return None

    async def ingest_vanguard_lead(self, body: dict[str, Any]) -> dict[str, Any]:
        first = _txt(body.get("first_name"))
        last = _txt(body.get("last_name"))
        name = _txt(body.get("name") or body.get("full_name") or " ".join(p for p in (first, last) if p))
        email = _txt(body.get("email"))
        phone = _txt(body.get("phone"))
        if not name:
            self._note_ingest_error("validation", "Укажите имя лида")
            return {"ok": False, "error": "validation", "message_ru": "Укажите имя лида"}
        if not email and not phone:
            self._note_ingest_error("validation", "Укажите email или телефон")
            return {"ok": False, "error": "validation", "message_ru": "Укажите email или телефон"}
        from services.recruiting_ops.ingest_fields import fill_missing_application_fields, parse_application_fields

        app_fields, app_error = parse_application_fields(body)
        if app_error:
            self._note_ingest_error("validation", app_error.get("message_ru") or "")
            return app_error
        org = _org(
            body.get("organization_id") or canonical_vanguard_org(),
            body.get("tenant_id"),
        )
        await self.ensure_hydrated(org)
        vacancy = _txt(body.get("vacancy_id") or body.get("vacancy")) or None
        external_id = (
            _txt(body.get("external_id") or body.get("reference") or body.get("reference_id") or body.get("idempotency_key"))
            or None
        )
        idempotency_key = _txt(body.get("idempotency_key") or external_id) or None
        self._ingest_log["last_check_at"] = _now()
        existing = self._find_duplicate(
            org,
            external_id=external_id,
            vacancy_id=vacancy,
            email=email,
            program=_txt(body.get("program_of_interest") or body.get("program")),
            idempotency_key=idempotency_key,
        )
        if existing:
            from services.recruiting_ops.attribution import preserve_first_touch

            patch = preserve_first_touch(existing, body)
            patch.update(fill_missing_application_fields(existing, app_fields or {}))
            patch["updated_at"] = _now()
            existing.update(patch)
            persisted = await self._persist_patch(org, str(existing["id"]), patch)
            if persisted:
                existing = persisted
                self._replace(org, "lead", existing)
            await self._activity(
                organization_id=org,
                entity_type="lead",
                entity_id=str(existing["id"]),
                action="vanguard_lead_duplicate",
                summary=f"Повторная заявка Vanguard: {existing.get('name')}",
                role="platform_owner",
                payload={"external_id": external_id, "vacancy_id": vacancy, "last_touch_source": patch.get("last_touch_source")},
            )
            self._note_ingest_success()
            logger.info(
                "VANGUARD_INGEST_DUPLICATE org=%s durable=%s lead_id=%s project_key=%s source=%s",
                org,
                existing.get("durable"),
                existing.get("id"),
                existing.get("project_key"),
                existing.get("source"),
            )
            return self._ok(item=existing, duplicate=True, already_exists=True)
        payload = dict(body)
        payload["name"] = name
        payload["first_name"] = first
        payload["last_name"] = last
        payload["source"] = _txt(body.get("source")) or "vanguard"
        payload["project_key"] = VANGUARD_PROJECT_KEY
        payload["vacancy_id"] = vacancy
        payload["external_id"] = external_id
        payload["idempotency_key"] = idempotency_key
        created = await self.create_lead(
            org,
            payload,
            "platform_owner",
            require_durable=is_production_runtime(),
        )
        if created.get("ok") and created.get("item"):
            item = created["item"]
            await self._activity(
                organization_id=org,
                entity_type="lead",
                entity_id=str(item["id"]),
                action="vanguard_lead_ingested",
                summary=f"Заявка Vanguard: {item.get('name')}",
                role="platform_owner",
                payload={
                    "source": item.get("source"),
                    "vacancy_id": item.get("vacancy_id"),
                    "external_id": item.get("external_id"),
                    "utm_source": item.get("utm_source"),
                    "utm_medium": item.get("utm_medium"),
                    "utm_campaign": item.get("utm_campaign"),
                    "durable": item.get("durable"),
                    "storage": item.get("storage"),
                    "project_key": VANGUARD_PROJECT_KEY,
                    "source": "vanguard",
                },
            )
            self._note_ingest_success()
            logger.info(
                "VANGUARD_INGEST_PERSISTED org=%s durable=%s lead_id=%s project_key=%s source=%s",
                org,
                item.get("durable"),
                item.get("id"),
                item.get("project_key"),
                item.get("source"),
            )
        else:
            self._note_ingest_error(str(created.get("error") or "ingest_failed"), str(created.get("message_ru") or ""))
        return created

    async def record_vanguard_event(self, body: dict[str, Any]) -> dict[str, Any]:
        from services.recruiting_ops.tracking import sanitize_tracking_body, validate_tracking

        event = sanitize_tracking_body(body)
        err = validate_tracking(event)
        if err:
            return {"ok": False, "error": "validation", "message_ru": err, "delivery_status": "FAILED"}
        org = _org(os.getenv("VANGUARD_ORGANIZATION_ID") or "ados", body.get("tenant_id"))
        await self.ensure_hydrated(org)
        event["id"] = str(body.get("id") or event.get("event_id") or uuid.uuid4())
        event["event_id"] = event.get("event_id") or event["id"]
        event["organization_id"] = org
        event["created_at"] = event.get("timestamp") or _now()
        event["data_mode"] = "REAL"
        dest = _txt(body.get("destination") or event.get("destination") or "recruiting_db").lower() or "recruiting_db"
        event["destination"] = dest
        from services.recruiting_ops.tracking_adapters import (
            PROVIDER_DESTINATIONS,
            TEST_DESTINATIONS,
            classify_unconfigured_provider,
            deliver_via_test_adapter,
        )
        from services.recruiting_ops.tracking_lifecycle import WAITING_PROVIDER, provider_is_configured

        if dest in TEST_DESTINATIONS:
            event = deliver_via_test_adapter(event)
        elif dest in PROVIDER_DESTINATIONS and not provider_is_configured(dest):
            event = classify_unconfigured_provider(event)
        else:
            event["delivery_status"] = "PENDING"
        if event.get("event_id"):
            for existing in self._bag(org)["tracking"]:
                if _txt(existing.get("event_id")) == event["event_id"]:
                    existing.setdefault("delivery_status", existing.get("delivery_status") or "DELIVERED")
                    return self._ok(item=existing, duplicate=True, delivery_status=existing.get("delivery_status") or "DELIVERED")
        saved: dict[str, Any] | None = None
        try:
            saved = await self._persist("tracking", event)
        except PersistUnavailable:
            queued = get_tracking_worker().enqueue({**event, "organization_id": org})
            logger.warning("vanguard tracking queued for worker event_id=%s", event.get("event_id"))
            return {
                "ok": False,
                "error": "tracking_retrying",
                "delivery_status": queued.get("delivery_status") or "RETRYING",
                "message_ru": "Событие в повторной доставке",
                "item": queued,
            }
        if dest in PROVIDER_DESTINATIONS and not provider_is_configured(dest):
            saved["delivery_status"] = WAITING_PROVIDER
            saved["delivery_class"] = "waiting_provider"
            saved["provider_status"] = "NOT_CONFIGURED"
        elif dest in TEST_DESTINATIONS:
            saved["delivery_status"] = saved.get("delivery_status") or "DELIVERED"
            saved["delivery_class"] = saved.get("delivery_class") or "delivered"
            saved["adapter"] = saved.get("adapter") or "test"
        else:
            saved["delivery_status"] = "DELIVERED"
            saved["delivery_class"] = "delivered"
            saved["destination"] = saved.get("destination") or "recruiting_db"
        patched = await self._persist_patch(
            org,
            str(saved.get("id")),
            {
                "delivery_status": saved["delivery_status"],
                "delivery_class": saved.get("delivery_class"),
                "destination": saved.get("destination") or dest,
                "durable": True,
                "storage": saved.get("storage") or "postgres",
                "persistence_mode": "POSTGRES",
                "recovery_reason": saved.get("recovery_reason"),
                "provider_status": saved.get("provider_status"),
                "adapter": saved.get("adapter"),
                "message_ru": saved.get("message_ru"),
            },
        )
        if patched:
            saved.update(patched)
        self._bag(org)["tracking"].insert(0, saved)
        if saved.get("delivery_status") == WAITING_PROVIDER:
            get_tracking_worker().enqueue(saved)
        return self._ok(item=saved, delivery_status=saved["delivery_status"])

    async def process_tracking_retries(self) -> dict[str, Any]:
        async def _persist(event: dict[str, Any]) -> dict[str, Any]:
            org = _org(str(event.get("organization_id") or os.getenv("VANGUARD_ORGANIZATION_ID") or "ados"))
            item_id = str(event.get("id") or "")
            if item_id:
                patched = await self._persist_patch(
                    org,
                    item_id,
                    {
                        "delivery_status": "DELIVERED",
                        "delivery_class": "delivered",
                        "durable": True,
                        "storage": "postgres",
                        "persistence_mode": "POSTGRES",
                        "attempt": event.get("attempt"),
                        "last_error": None,
                    },
                )
                if patched:
                    return patched
            return await super_persist(event)

        async def super_persist(event: dict[str, Any]) -> dict[str, Any]:
            return await self._persist("tracking", event)

        done = await get_tracking_worker().tick(_persist)
        org = _org(os.getenv("VANGUARD_ORGANIZATION_ID") or "ados")
        await self.ensure_hydrated(org)
        for item in done:
            if item.get("delivery_status") == "DELIVERED":
                self._replace(org, "tracking", item)
            elif item.get("delivery_status") == "DEAD_LETTER":
                await self._persist_patch(
                    org,
                    str(item.get("id") or ""),
                    {
                        "delivery_status": "DEAD_LETTER",
                        "dead_letter_reason": item.get("dead_letter_reason"),
                        "last_error": item.get("last_error"),
                        "attempt": item.get("attempt"),
                        "message_ru": item.get("message_ru"),
                    },
                )
                self._replace(org, "tracking", item)
        return self._ok(items=done, worker=get_tracking_worker().snapshot())

    def _idempotency_hit(self, org: str, key: str) -> dict[str, Any] | None:
        if not key:
            return None
        for row in self._bag(org)["idempotency"]:
            if _txt(row.get("key")) == key:
                lead_id = _txt(row.get("lead_id"))
                lead = self._find(org, "lead", lead_id) if lead_id else None
                return lead or row
        return None

    async def _store_idempotency(self, org: str, key: str, lead: dict[str, Any]) -> None:
        if not key or not lead:
            return
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "key": key,
            "lead_id": lead.get("id"),
            "reference": lead.get("external_id") or lead.get("reference"),
            "project_key": VANGUARD_PROJECT_KEY,
            "created_at": _now(),
        }
        try:
            saved = await self._persist("idempotency", item)
        except PersistUnavailable:
            saved = item
        self._bag(org)["idempotency"].insert(0, saved)

    async def submit_vanguard_application(self, body: dict[str, Any]) -> dict[str, Any]:
        from services.recruiting_ops.references import new_vanguard_reference

        first = _txt(body.get("first_name"))
        last = _txt(body.get("last_name"))
        name = _txt(body.get("name") or body.get("full_name") or " ".join(p for p in (first, last) if p))
        email = _txt(body.get("email")).lower()
        if not name or not email:
            return {"ok": False, "error": "validation", "message_ru": "Укажите имя и email"}
        org = _org(os.getenv("VANGUARD_ORGANIZATION_ID") or "ados", body.get("tenant_id"))
        await self.ensure_hydrated(org)
        idem_key = _txt(body.get("idempotency_key"))
        hit = self._idempotency_hit(org, idem_key)
        if hit and hit.get("id"):
            ref = _txt(hit.get("external_id") or hit.get("reference"))
            return self._ok(item=hit, duplicate=True, already_exists=True, reference=ref, application_received=True)
        reference = _txt(body.get("external_id") or body.get("reference")) or new_vanguard_reference()
        submitted_at = _txt(body.get("submitted_at")) or _now()
        try:
            await self.record_vanguard_event(
                {
                    **body,
                    "event_type": "application_submit",
                    "event_id": _txt(body.get("event_id")) or str(uuid.uuid4()),
                    "timestamp": submitted_at,
                    "page": _txt(body.get("page") or body.get("landing_page")) or "/vanguard",
                }
            )
        except Exception:
            logger.warning("vanguard apply tracking submit skipped")
        payload = dict(body)
        payload["first_name"] = first
        payload["last_name"] = last
        payload["name"] = name
        payload["email"] = email
        payload["source"] = "vanguard"
        payload["project_key"] = VANGUARD_PROJECT_KEY
        payload["external_id"] = reference
        payload["reference"] = reference
        payload["submitted_at"] = submitted_at
        payload["program_of_interest"] = _txt(body.get("program_of_interest") or body.get("program"))
        payload["unit_of_interest"] = _txt(body.get("unit_of_interest") or body.get("unit"))
        payload["application_message"] = _txt(body.get("application_message") or body.get("message") or body.get("reason"))
        payload["vacancy"] = payload["program_of_interest"] or _txt(body.get("vacancy"))
        ingested = await self.ingest_vanguard_lead(payload)
        if ingested.get("ok") and ingested.get("item"):
            await self._store_idempotency(org, idem_key, ingested["item"])
            try:
                await self.record_vanguard_event(
                    {
                        **body,
                        "event_type": "application_success",
                        "event_id": str(uuid.uuid4()),
                        "timestamp": _now(),
                        "page": "/vanguard",
                    }
                )
            except Exception:
                logger.warning("vanguard apply tracking success skipped")
        return {
            **ingested,
            "reference": reference if ingested.get("ok") else ingested.get("reference") or reference,
            "application_received": bool(ingested.get("ok")),
        }

    async def update_lead(
        self,
        organization_id: str,
        lead_id: str,
        body: dict[str, Any],
        role: str | None = None,
        action: str = "update",
    ) -> dict[str, Any]:
        denied = require(role, action)
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        located_org, item = await self._locate(organization_id, "lead", lead_id, role)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Лид не найден"}
        org = located_org
        patch = dict(body)
        if "status" in patch:
            requested = _lead_status(patch.get("status"), item.get("status") or "new")
            current = _lead_status(item.get("status"), "new")
            if requested == "converted" and action != "convert":
                return {
                    "ok": False,
                    "error": "validation",
                    "message_ru": "Конвертация лида — только через /convert.",
                }
            if current == "converted" and action != "convert" and requested != "converted":
                return {
                    "ok": False,
                    "error": "validation",
                    "message_ru": "Сконвертированный лид нельзя вернуть через смену статуса.",
                }
            patch["status"] = requested
        if "name" in patch:
            name = _txt(patch.get("name"))
            if not name:
                return {"ok": False, "error": "validation", "message_ru": "Укажите имя лида"}
            patch["name"] = name
        if "notes_append" in patch:
            extra = _txt(patch.pop("notes_append"))
            if extra:
                existing = _txt(item.get("notes"))
                patch["notes"] = f"{existing}\n{extra}".strip() if existing else extra
        patch["updated_at"] = _now()
        item.update(patch)
        persisted = await self._persist_patch(org, lead_id, patch)
        if persisted:
            item = persisted
            self._replace(org, "lead", item)
        else:
            self._replace(org, "lead", item)
        return self._ok(item=item)

    async def assign_lead(self, organization_id: str, lead_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        if "assignee" not in body and "recruiter" not in body:
            return {"ok": False, "error": "validation", "message_ru": "Укажите рекрутера"}
        assignee = _txt(body.get("assignee") or body.get("recruiter")) or None
        result = await self.update_lead(organization_id, lead_id, {"assignee": assignee}, role, "update")
        if result.get("ok"):
            await self._activity(
                organization_id=_org(organization_id),
                entity_type="lead",
                entity_id=lead_id,
                action="lead_assigned" if assignee else "lead_unassigned",
                summary=f"Лид назначен рекрутеру: {assignee}" if assignee else "Ответственный снят",
                role=role,
            )
        return result

    async def add_note(self, organization_id: str, lead_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        note = _txt(body.get("notes") or body.get("note") or body.get("text"))
        if not note:
            return {"ok": False, "error": "validation", "message_ru": "Укажите текст заметки"}
        result = await self.update_lead(organization_id, lead_id, {"notes_append": note}, role, "update")
        if result.get("ok"):
            await self._activity(
                organization_id=_org(organization_id),
                entity_type="lead",
                entity_id=lead_id,
                action="note_added",
                summary=note,
                role=role,
            )
        return result

    async def qualify_lead(self, organization_id: str, lead_id: str, role: str | None = None) -> dict[str, Any]:
        result = await self.update_lead(organization_id, lead_id, {"status": "qualified"}, role, "qualify")
        if result.get("ok"):
            await self._activity(
                organization_id=_org(organization_id),
                entity_type="lead",
                entity_id=lead_id,
                action="lead_qualified",
                summary="Лид квалифицирован",
                role=role,
            )
        return result

    def _candidate_for_lead(self, organization_id: str, lead_id: str, role: str | None) -> dict[str, Any] | None:
        lid = _txt(lead_id)
        if not lid:
            return None
        from services.recruiting_ops.identity import is_merged_candidate, linked_lead_ids

        for org in self._read_orgs(organization_id, role):
            for item in self._bag(org).get("candidate") or []:
                if is_merged_candidate(item):
                    continue
                if lid in linked_lead_ids(item) or _txt(item.get("lead_id")) == lid:
                    return item
            lead = self._find(org, "lead", lid)
            if lead and lead.get("candidate_id"):
                found = self._find(org, "candidate", str(lead["candidate_id"]))
                if found:
                    return self._resolved_candidate(org, found)
        return None

    def _candidate_for_identity(self, organization_id: str, person: dict[str, Any], role: str | None) -> dict[str, Any] | None:
        from services.recruiting_ops.identity import identity_decision

        for org in self._read_orgs(organization_id, role):
            for item in self._bag(org).get("candidate") or []:
                from services.recruiting_ops.identity import identity_decision, is_merged_candidate

                if is_merged_candidate(item):
                    continue
                if identity_decision(person, item) == "match":
                    return item
        return None

    def _with_application_links(self, candidate: dict[str, Any]) -> dict[str, Any]:
        from services.recruiting_ops.identity import linked_lead_ids

        item = dict(candidate)
        ids = linked_lead_ids(item)
        apps = [app for app in (item.get("applications") or []) if isinstance(app, dict)]
        if ids and not apps:
            apps = [{"lead_id": lid} for lid in ids]
        item["lead_ids"] = ids
        item["applications"] = apps
        if ids and not item.get("lead_id"):
            item["lead_id"] = ids[0]
        return item

    def _application_snapshot(self, lead: dict[str, Any]) -> dict[str, Any]:
        from services.recruiting_ops.identity import application_snapshot

        return application_snapshot(lead)

    async def _attach_lead_to_candidate(
        self,
        organization_id: str,
        lead: dict[str, Any],
        candidate: dict[str, Any],
        role: str | None,
        *,
        already_converted: bool = False,
    ) -> dict[str, Any]:
        from services.recruiting_ops.attribution import preserve_first_touch
        from services.recruiting_ops.identity import linked_lead_ids

        org = _org(organization_id)
        lead_id = _txt(lead.get("id"))
        candidate = self._with_application_links(candidate)
        ids = linked_lead_ids(candidate)
        apps = list(candidate.get("applications") or [])
        if lead_id and lead_id not in ids:
            ids.append(lead_id)
            apps.append(self._application_snapshot(lead))
        patch = preserve_first_touch(candidate, lead)
        patch.update(
            {
                "lead_id": ids[0] if ids else candidate.get("lead_id"),
                "lead_ids": ids,
                "applications": apps,
                "updated_at": _now(),
            }
        )
        if not _txt(candidate.get("phone")) and lead.get("phone"):
            patch["phone"] = lead.get("phone")
        if not _txt(candidate.get("email")) and lead.get("email"):
            patch["email"] = lead.get("email")
        extra_notes = _txt(lead.get("notes"))
        if extra_notes:
            existing_notes = _txt(candidate.get("notes"))
            if extra_notes not in existing_notes:
                patch["notes"] = f"{existing_notes}\n{extra_notes}".strip() if existing_notes else extra_notes
        candidate.update(patch)
        persisted = await self._persist_patch(org, str(candidate["id"]), patch)
        if persisted:
            candidate = persisted
        candidate = self._with_application_links(candidate)
        self._replace(org, "candidate", candidate)
        patched_lead = await self.update_lead(
            org,
            lead_id,
            {"status": "converted", "candidate_id": candidate["id"]},
            role,
            "convert",
        )
        lead_out = patched_lead.get("item") or lead
        await self._activity(
            organization_id=org,
            entity_type="candidate",
            entity_id=str(candidate["id"]),
            action="application_linked" if not already_converted else "lead_converted",
            summary=f"Заявка связана с кандидатом: {lead.get('name')}",
            role=role,
            payload={"lead_id": lead_id, "application_count": len(ids)},
        )
        return self._ok(
            item=candidate,
            lead=lead_out,
            already_converted=already_converted,
            identity_linked=not already_converted,
            duplicate=True,
        )

    async def set_lead_status(
        self,
        organization_id: str,
        lead_id: str,
        body: dict[str, Any],
        role: str | None = None,
    ) -> dict[str, Any]:
        status = _lead_status(body.get("status"), "")
        if status not in {"new", "qualified", "lost"}:
            return {
                "ok": False,
                "error": "validation",
                "message_ru": "Допустимые статусы: new, qualified, lost. Конвертация — только через /convert.",
            }
        located_org, lead = await self._locate(organization_id, "lead", lead_id, role)
        if not lead:
            return {"ok": False, "error": "not_found", "message_ru": "Лид не найден"}
        if _lead_status(lead.get("status")) == "converted":
            return {
                "ok": False,
                "error": "validation",
                "message_ru": "Сконвертированный лид нельзя вернуть через смену статуса.",
            }
        action = "qualify" if status == "qualified" else "update"
        result = await self.update_lead(organization_id, lead_id, {"status": status}, role, action)
        if result.get("ok"):
            await self._activity(
                organization_id=_org(organization_id),
                entity_type="lead",
                entity_id=lead_id,
                action="lead_status_changed",
                summary=f"Статус лида: {status}",
                role=role,
                payload={"status": status},
            )
        return result

    async def assign_lead_vacancy(
        self,
        organization_id: str,
        lead_id: str,
        body: dict[str, Any],
        role: str | None = None,
    ) -> dict[str, Any]:
        vacancy_id = _txt(body.get("vacancy_id") or body.get("vacancy"))
        if not vacancy_id:
            return {"ok": False, "error": "validation", "message_ru": "Укажите вакансию"}
        located_org, vacancy = await self._locate(organization_id, "vacancy", vacancy_id, role)
        if not vacancy:
            return {"ok": False, "error": "not_found", "message_ru": "Вакансия не найдена"}
        result = await self.update_lead(
            organization_id,
            lead_id,
            {
                "vacancy_id": vacancy_id,
                "vacancy": _txt(vacancy.get("title") or vacancy.get("name")) or vacancy_id,
            },
            role,
            "update",
        )
        if result.get("ok"):
            await self._activity(
                organization_id=located_org,
                entity_type="lead",
                entity_id=lead_id,
                action="lead_vacancy_assigned",
                summary=f"Вакансия назначена: {vacancy.get('title') or vacancy_id}",
                role=role,
                payload={"vacancy_id": vacancy_id},
            )
        return result

    async def convert_lead(self, organization_id: str, lead_id: str, body: dict[str, Any] | None = None, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "convert")
        if denied:
            return denied
        from services.recruiting_ops.identity import identity_lock_key

        lead_lock = self._convert_locks.setdefault(str(lead_id), asyncio.Lock())
        async with lead_lock:
            located_org, lead = await self._locate(organization_id, "lead", lead_id, role)
            if not lead:
                return {"ok": False, "error": "not_found", "message_ru": "Лид не найден"}
            org = located_org
            ident_key = identity_lock_key(org, lead.get("email"), lead.get("phone"))
            ident_lock = self._identity_locks.setdefault(ident_key, asyncio.Lock())
            async with ident_lock:
                existing = self._candidate_for_lead(organization_id, lead_id, role)
                if existing:
                    if _txt(lead.get("candidate_id")) != _txt(existing.get("id")) or _lead_status(lead.get("status")) != "converted":
                        return await self._attach_lead_to_candidate(org, lead, existing, role, already_converted=True)
                    return self._ok(
                        item=self._with_application_links(existing),
                        lead=lead,
                        already_converted=True,
                        duplicate=True,
                    )
                matched = self._candidate_for_identity(organization_id, lead, role)
                if matched:
                    return await self._attach_lead_to_candidate(org, lead, matched, role, already_converted=False)
                body = body or {}
                stage = _stage(body.get("pipeline_stage") or ("QUALIFIED" if lead.get("status") == "qualified" else "NEW"))
                from services.recruiting_ops.ingest_fields import application_fields_from_lead

                candidate_body = {
                    "name": lead.get("name"),
                    "email": lead.get("email"),
                    "campaign_id": lead.get("campaign_id"),
                    "vacancy_id": body.get("vacancy_id") or lead.get("vacancy_id"),
                    "assignee": body.get("assignee") or lead.get("assignee"),
                    "lead_id": lead_id,
                    "lead_ids": [lead_id],
                    "applications": [self._application_snapshot(lead)],
                    "pipeline_stage": stage,
                    "notes": lead.get("notes"),
                    **application_fields_from_lead(lead),
                }
                created = await self.create_candidate(org, candidate_body, role)
                if not created.get("ok"):
                    return created
                candidate = self._with_application_links(created["item"])
                patched = await self.update_lead(
                    org,
                    lead_id,
                    {"status": "converted", "candidate_id": candidate["id"]},
                    role,
                    "convert",
                )
                await self._activity(
                    organization_id=org,
                    entity_type="lead",
                    entity_id=lead_id,
                    action="lead_converted",
                    summary=f"Лид преобразован в кандидата: {lead.get('name')}",
                    role=role,
                    payload={"candidate_id": candidate["id"], "pipeline_stage": stage},
                )
                return self._ok(item=candidate, lead=patched.get("item") or lead)

    async def create_candidate(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        name = _txt(body.get("name") or body.get("full_name"))
        if not name:
            return {"ok": False, "error": "validation", "message_ru": "Укажите имя кандидата"}
        from services.recruiting_ops.ingest_fields import parse_application_fields

        app_fields, app_error = parse_application_fields(body)
        if app_error:
            return app_error
        org = _org(organization_id, body.get("tenant_id"))
        await self.ensure_hydrated(org)
        existing_for_lead = self._candidate_for_lead(org, _txt(body.get("lead_id")), role)
        if existing_for_lead:
            return self._ok(item=self._with_application_links(existing_for_lead), already_converted=True, duplicate=True)
        matched = self._candidate_for_identity(org, body, role)
        if matched:
            lead_id = _txt(body.get("lead_id"))
            lead = self._find(org, "lead", lead_id) if lead_id else None
            if lead:
                return await self._attach_lead_to_candidate(org, lead, matched, role)
            return self._ok(item=self._with_application_links(matched), duplicate=True, identity_linked=True)
        lead_id = _txt(body.get("lead_id")) or None
        lead_ids = [str(x) for x in (body.get("lead_ids") or ([lead_id] if lead_id else [])) if x]
        applications = body.get("applications") if isinstance(body.get("applications"), list) else []
        if lead_id and not applications:
            applications = [self._application_snapshot({**body, "id": lead_id})]
        item = {
            "id": str(body.get("id") or uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "name": name,
            "phone": (app_fields or {}).get("phone") or _txt(body.get("phone")) or None,
            "email": _txt(body.get("email")),
            "source": _txt(body.get("source")) or None,
            "project_key": infer_project_key(
                source=_txt(body.get("source")) or None,
                project_key=_txt(body.get("project_key")) or None,
            ),
            "campaign_id": _txt(body.get("campaign_id")) or None,
            "vacancy_id": _txt(body.get("vacancy_id")) or None,
            "assignee": _txt(body.get("assignee")) or None,
            "lead_id": lead_id,
            "lead_ids": lead_ids,
            "applications": applications,
            "pipeline_stage": _stage(body.get("pipeline_stage")),
            "notes": _txt(body.get("notes")),
            "status": _stage(body.get("pipeline_stage")),
            "data_mode": "REAL",
            "created_at": _now(),
            "updated_at": _now(),
        }
        if app_fields:
            item.update(app_fields)
        from services.recruiting_ops.attribution import TEST_TRAFFIC_CLASS, classify_traffic

        for key in (
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "utm_term",
            "country",
            "preferred_language",
            "unit_of_interest",
            "program_of_interest",
            "application_message",
            "external_id",
            "idempotency_key",
            "submitted_at",
        ):
            if key not in body:
                continue
            value = body.get(key)
            item[key] = _txt(value) or None if isinstance(value, str) or value is None else value
        explicit = _txt(item.get("traffic_class") or body.get("traffic_class")).upper()
        item["traffic_class"] = (
            TEST_TRAFFIC_CLASS
            if classify_traffic(item) == TEST_TRAFFIC_CLASS or explicit in {TEST_TRAFFIC_CLASS, "E2E"}
            else "PRODUCTION"
        )
        saved = await self._persist("candidate", item)
        self._bag(org)["candidate"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="candidate",
            entity_id=str(saved["id"]),
            action="candidate_created",
            summary=f"Кандидат в воронке: {name}",
            role=role,
            payload={"pipeline_stage": saved.get("pipeline_stage")},
        )
        return self._ok(item=self._with_application_links(saved))

    async def move_candidate(
        self,
        organization_id: str,
        candidate_id: str,
        body: dict[str, Any],
        role: str | None = None,
    ) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        located_org, item = await self._locate(organization_id, "candidate", candidate_id, role)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Кандидат не найден"}
        org = located_org
        from_stage = _stage(item.get("pipeline_stage") or item.get("status") or "NEW")
        stage = _stage(body.get("pipeline_stage") or body.get("stage") or body.get("status"), from_stage)
        patch = {"pipeline_stage": stage, "status": stage, "updated_at": _now()}
        if body.get("assignee"):
            patch["assignee"] = _txt(body.get("assignee"))
        if body.get("notes"):
            patch["notes"] = _txt(body.get("notes"))
        if from_stage != stage or body.get("assignee") or body.get("notes"):
            item.update(patch)
            try:
                persisted = await self._persist_patch(org, candidate_id, patch)
            except PersistUnavailable:
                return {
                    "ok": False,
                    "error": "storage_unavailable",
                    "message_ru": "Не удалось сохранить этап воронки в PostgreSQL.",
                }
            if persisted:
                item = persisted
            elif not memory_fallback_allowed():
                return {
                    "ok": False,
                    "error": "storage_unavailable",
                    "message_ru": "Не удалось сохранить этап воронки в PostgreSQL.",
                }
            self._replace(org, "candidate", item)
        if from_stage != stage:
            await self._activity(
                organization_id=org,
                entity_type="candidate",
                entity_id=candidate_id,
                action="pipeline_moved",
                summary=f"Кандидат перемещён: {from_stage} → {stage}",
                role=role,
                payload={"from_stage": from_stage, "to_stage": stage, "pipeline_stage": stage},
            )
        if stage == "INTERVIEW":
            await self._ensure_interview_scheduled(org, item, role, from_stage=from_stage)
        return self._ok(item=self._with_application_links(item))

    async def assign_candidate(
        self,
        organization_id: str,
        candidate_id: str,
        body: dict[str, Any],
        role: str | None = None,
    ) -> dict[str, Any]:
        if "assignee" not in body and "recruiter" not in body:
            return {"ok": False, "error": "validation", "message_ru": "Укажите рекрутера"}
        denied = require(role, "update")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        located_org, item = await self._locate(organization_id, "candidate", candidate_id, role)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Кандидат не найден"}
        org = located_org
        assignee = _txt(body.get("assignee") or body.get("recruiter")) or None
        patch = {"assignee": assignee, "updated_at": _now()}
        item.update(patch)
        try:
            persisted = await self._persist_patch(org, candidate_id, patch)
        except PersistUnavailable:
            return {
                "ok": False,
                "error": "storage_unavailable",
                "message_ru": "Не удалось сохранить ответственного в PostgreSQL.",
            }
        if persisted:
            item = persisted
        elif not memory_fallback_allowed():
            return {
                "ok": False,
                "error": "storage_unavailable",
                "message_ru": "Не удалось сохранить ответственного в PostgreSQL.",
            }
        self._replace(org, "candidate", item)
        await self._activity(
            organization_id=org,
            entity_type="candidate",
            entity_id=candidate_id,
            action="candidate_assigned" if assignee else "candidate_unassigned",
            summary=f"Кандидат назначен рекрутеру: {assignee}" if assignee else "Ответственный снят",
            role=role,
            payload={"assignee": assignee},
        )
        return self._ok(item=self._with_application_links(item))

    async def schedule_interview(
        self,
        organization_id: str,
        candidate_id: str,
        body: dict[str, Any] | None = None,
        role: str | None = None,
    ) -> dict[str, Any]:
        payload = dict(body or {})
        payload.setdefault("pipeline_stage", "INTERVIEW")
        moved = await self.move_candidate(organization_id, candidate_id, payload, role)
        if not moved.get("ok"):
            return moved
        return self._ok(item=moved.get("item"), interview_scheduled=True)

    async def _ensure_interview_scheduled(
        self,
        org: str,
        candidate: dict[str, Any],
        role: str | None,
        *,
        from_stage: str,
    ) -> dict[str, Any] | None:
        candidate_id = _txt(candidate.get("id"))
        existing = [
            task
            for task in self._bag(org).get("task") or []
            if _txt(task.get("candidate_id")) == candidate_id
            and "интервью" in _txt(task.get("title")).lower()
            and _task_status(task.get("status")) == "open"
        ]
        task = existing[0] if existing else None
        if not task:
            created = await self.create_task(
                org,
                {
                    "title": "Провести интервью",
                    "candidate_id": candidate_id,
                    "lead_id": _txt(candidate.get("lead_id")) or None,
                    "assignee": _txt(candidate.get("assignee")) or None,
                    "project_key": _txt(candidate.get("project_key")) or None,
                },
                role,
            )
            task = created.get("item") if created.get("ok") else None
        already = any(
            _txt(row.get("action")) == "interview_scheduled" and _txt(row.get("entity_id")) == candidate_id
            for row in self._bag(org).get("activity") or []
        )
        if already:
            return task
        await self._activity(
            organization_id=org,
            entity_type="candidate",
            entity_id=candidate_id,
            action="interview_scheduled",
            summary="Интервью назначено",
            role=role,
            payload={"from_stage": from_stage, "to_stage": "INTERVIEW", "task_id": _txt((task or {}).get("id")) or None},
        )
        return task

    async def _persist_merge_batch(self, org: str, patches: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]] | None:
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = RecruitingOpsRepository(session)
                saved: list[dict[str, Any]] = []
                for item_id, patch in patches:
                    row = await repo.get(org, item_id)
                    if row is None:
                        raise PersistUnavailable(f"missing {item_id}")
                    await repo.update(row, patch)
                    saved.append(record_to_dict(row))
                return saved
        except PersistUnavailable:
            raise
        except Exception as exc:
            if not memory_fallback_allowed():
                logger.error("recruiting_ops merge persist failed in production: %s", exc)
                raise PersistUnavailable(str(exc)) from exc
            logger.warning("recruiting_ops merge persist skipped (NON_DURABLE_DEVELOPMENT_MODE): %s", exc)
            return None

    def _resolved_candidate(self, org: str, item: dict[str, Any] | None) -> dict[str, Any] | None:
        from services.recruiting_ops.identity import is_merged_candidate

        if not item:
            return None
        if is_merged_candidate(item):
            target = _txt(item.get("merged_into"))
            if target:
                found = self._find(org, "candidate", target)
                if found and not is_merged_candidate(found):
                    return found
        return item

    async def merge_candidates(
        self,
        organization_id: str,
        candidate_id: str,
        body: dict[str, Any] | None = None,
        role: str | None = None,
    ) -> dict[str, Any]:
        denied = require(role, "merge")
        if denied:
            return denied
        from services.recruiting_ops.identity import (
            build_merge_preview,
            is_merged_candidate,
            linked_lead_ids,
            merge_application_snapshots,
            merge_safety,
            merge_text,
            union_ids,
        )

        body = body or {}
        duplicate_id = _txt(body.get("duplicate_candidate_id") or body.get("source_candidate_id"))
        canonical_id = _txt(candidate_id)
        if not duplicate_id:
            return {"ok": False, "error": "validation", "message_ru": "Укажите кандидата-дубль для объединения."}
        if duplicate_id == canonical_id:
            return {"ok": False, "error": "validation", "message_ru": "Нельзя объединить кандидата с самим собой."}
        preview_only = bool(body.get("preview") or body.get("dry_run"))
        force = bool(body.get("force"))
        reason = _txt(body.get("reason"))
        pair_key = "|".join(sorted((canonical_id, duplicate_id)))
        lock = self._merge_locks.setdefault(pair_key, asyncio.Lock())
        async with lock:
            located_org, canonical = await self._locate(organization_id, "candidate", canonical_id, role)
            if not canonical:
                return {"ok": False, "error": "not_found", "message_ru": "Кандидат не найден"}
            org = located_org
            _, duplicate = await self._locate(organization_id, "candidate", duplicate_id, role)
            if not duplicate:
                return {"ok": False, "error": "not_found", "message_ru": "Кандидат-дубль не найден"}
            if _org(canonical.get("organization_id") or org) != _org(duplicate.get("organization_id") or org):
                return {"ok": False, "error": "not_found", "message_ru": "Кандидат-дубль не найден"}
            canonical = self._with_application_links(canonical)
            duplicate = self._with_application_links(duplicate)

            if is_merged_candidate(duplicate) and _txt(duplicate.get("merged_into")) in {canonical_id, _txt(canonical.get("merged_into"))}:
                live = self._resolved_candidate(org, canonical) or canonical
                return self._ok(
                    item=self._with_application_links(live),
                    already_merged=True,
                    duplicate=True,
                    preview=build_merge_preview(live, live),
                )
            if is_merged_candidate(canonical) and _txt(canonical.get("merged_into")) == duplicate_id:
                live = self._resolved_candidate(org, duplicate) or duplicate
                return self._ok(
                    item=self._with_application_links(live),
                    already_merged=True,
                    duplicate=True,
                    preview=build_merge_preview(live, live),
                )
            if is_merged_candidate(canonical) or is_merged_candidate(duplicate):
                live = self._resolved_candidate(org, canonical) or self._resolved_candidate(org, duplicate)
                if live:
                    return self._ok(item=self._with_application_links(live), already_merged=True, duplicate=True)

            safety = merge_safety(canonical, duplicate)
            preview = build_merge_preview(canonical, duplicate)
            comparison = {
                "canonical": self._with_application_links(canonical),
                "duplicate": self._with_application_links(duplicate),
            }
            if preview_only:
                return self._ok(
                    item=self._with_application_links(canonical),
                    preview=preview,
                    comparison=comparison,
                    safety=safety,
                    force_required=safety != "match",
                )
            if safety != "match":
                if not force:
                    return {
                        "ok": False,
                        "error": "conflict",
                        "safety": safety,
                        "preview": preview,
                        "comparison": comparison,
                        "message_ru": "Идентичность неоднозначна. Объединение требует подтверждения владельца.",
                    }
                if not can(role, "admin"):
                    return {
                        "ok": False,
                        "error": "forbidden",
                        "safety": safety,
                        "preview": preview,
                        "comparison": comparison,
                        "message_ru": "Только владелец может принудительно объединить неоднозначные профили.",
                    }

            now = _now()
            apps = merge_application_snapshots(canonical.get("applications"), duplicate.get("applications"))
            lead_ids = union_ids(linked_lead_ids(canonical), linked_lead_ids(duplicate))
            have = {_txt(app.get("lead_id")) for app in apps}
            for lid in lead_ids:
                if lid and lid not in have:
                    apps.append({"lead_id": lid})
                    have.add(lid)
            history = list(canonical.get("pipeline_history") or []) + list(duplicate.get("pipeline_history") or [])
            history.append(
                {
                    "action": "candidate_merged",
                    "from_stage": duplicate.get("pipeline_stage"),
                    "to_stage": preview["pipeline_stage"],
                    "duplicate_candidate_id": duplicate_id,
                    "at": now,
                }
            )
            assignees = union_ids([canonical.get("assignee")], [duplicate.get("assignee")])
            vacancy_ids = union_ids(
                [canonical.get("vacancy_id")],
                [duplicate.get("vacancy_id")],
                canonical.get("vacancy_ids"),
                duplicate.get("vacancy_ids"),
            )
            canonical_patch = {
                "lead_id": lead_ids[0] if lead_ids else canonical.get("lead_id"),
                "lead_ids": lead_ids,
                "applications": apps,
                "pipeline_stage": preview["pipeline_stage"],
                "status": preview["pipeline_stage"],
                "assignee": preview["assignee"],
                "assignee_history": assignees,
                "vacancy_id": vacancy_ids[0] if vacancy_ids else canonical.get("vacancy_id"),
                "vacancy_ids": vacancy_ids,
                "vacancy": _txt(
                    canonical.get("vacancy")
                    or duplicate.get("vacancy")
                    or ((preview.get("vacancies") or [None])[0])
                ),
                "notes": merge_text(canonical.get("notes"), duplicate.get("notes")),
                "pipeline_history": history,
                "merged_from": union_ids(canonical.get("merged_from"), [duplicate_id]),
                "email": canonical.get("email") or duplicate.get("email"),
                "phone": canonical.get("phone") or duplicate.get("phone"),
                "name": canonical.get("name") or duplicate.get("name"),
                "updated_at": now,
            }
            duplicate_patch = {
                "merged": True,
                "merged_into": canonical_id,
                "merged_at": now,
                "status": "MERGED",
                "pipeline_stage": preview["pipeline_stage"],
                "updated_at": now,
            }
            lead_patches: list[tuple[str, dict[str, Any]]] = []
            for lid in lead_ids:
                lead = self._find(org, "lead", lid)
                if lead:
                    lead_patches.append((lid, {"candidate_id": canonical_id, "updated_at": now}))

            patches = [(canonical_id, canonical_patch), (duplicate_id, duplicate_patch), *lead_patches]
            try:
                persisted = await self._persist_merge_batch(org, patches)
            except PersistUnavailable:
                return {
                    "ok": False,
                    "error": "storage_unavailable",
                    "message_ru": "Не удалось сохранить объединение в PostgreSQL.",
                }

            if persisted:
                by_id = {str(row.get("id")): row for row in persisted}
                canonical = self._with_application_links(by_id.get(canonical_id) or {**canonical, **canonical_patch})
                duplicate = by_id.get(duplicate_id) or {**duplicate, **duplicate_patch}
            else:
                canonical.update(canonical_patch)
                duplicate.update(duplicate_patch)
                canonical = self._with_application_links(canonical)
            self._replace(org, "candidate", canonical)
            self._replace(org, "candidate", duplicate)
            for lid, patch in lead_patches:
                lead = self._find(org, "lead", lid)
                if lead:
                    lead.update(patch)
                    self._replace(org, "lead", lead)

            await self._activity(
                organization_id=org,
                entity_type="candidate",
                entity_id=canonical_id,
                action="candidate_merged",
                summary=f"Кандидаты объединены: {canonical.get('name')}",
                role=role,
                payload={
                    "duplicate_candidate_id": duplicate_id,
                    "reason": reason,
                    "force": force,
                    "safety": safety,
                    "application_count": len(apps),
                    "lead_ids": lead_ids,
                    "pipeline_stage": preview["pipeline_stage"],
                },
            )
            return self._ok(
                item=canonical,
                already_merged=False,
                preview=preview,
                comparison=comparison,
                safety=safety,
                merged_candidate_id=duplicate_id,
            )

    async def create_vacancy(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        title = _txt(body.get("title") or body.get("name"))
        if not title:
            return {"ok": False, "error": "validation", "message_ru": "Укажите название вакансии"}
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = {
            "id": str(body.get("id") or uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "title": title,
            "department": _txt(body.get("department")),
            "location": _txt(body.get("location")),
            "status": _txt(body.get("status")) or "open",
            "project_key": infer_project_key(project_key=_txt(body.get("project_key")) or None),
            "notes": _txt(body.get("notes")),
            "data_mode": "REAL",
            "created_at": _now(),
            "updated_at": _now(),
        }
        saved = await self._persist("vacancy", item)
        self._bag(org)["vacancy"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="vacancy",
            entity_id=str(saved["id"]),
            action="vacancy_created",
            summary=f"Вакансия: {title}",
            role=role,
        )
        return self._ok(item=saved)

    async def update_vacancy(
        self,
        organization_id: str,
        vacancy_id: str,
        body: dict[str, Any],
        role: str | None = None,
    ) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        located_org, item = await self._locate(organization_id, "vacancy", vacancy_id, role)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Вакансия не найдена"}
        org = located_org
        patch: dict[str, Any] = {"updated_at": _now()}
        if "title" in body or "name" in body:
            title = _txt(body.get("title") or body.get("name"))
            if not title:
                return {"ok": False, "error": "validation", "message_ru": "Укажите название вакансии"}
            patch["title"] = title
        for key in ("department", "location", "status", "notes", "project_key"):
            if key in body:
                patch[key] = _txt(body.get(key)) or None
        if "project_key" in patch:
            patch["project_key"] = infer_project_key(project_key=patch.get("project_key"))
        item.update(patch)
        persisted = await self._persist_patch(org, vacancy_id, patch)
        if persisted:
            item = persisted
            self._replace(org, "vacancy", item)
        else:
            self._replace(org, "vacancy", item)
        await self._activity(
            organization_id=org,
            entity_type="vacancy",
            entity_id=vacancy_id,
            action="vacancy_updated",
            summary=f"Вакансия обновлена: {item.get('title')}",
            role=role,
        )
        return self._ok(item=item)

    async def create_campaign(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        name = _txt(body.get("name") or body.get("title"))
        if not name:
            return {"ok": False, "error": "validation", "message_ru": "Укажите название кампании"}
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = {
            "id": str(body.get("id") or uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "name": name,
            "source": _txt(body.get("source")) or "manual",
            "project_key": infer_project_key(
                source=_txt(body.get("source")) or "manual",
                project_key=_txt(body.get("project_key")) or None,
            ),
            "channel": _txt(body.get("channel")) or None,
            "medium": _txt(body.get("medium") or body.get("utm_medium")) or None,
            "campaign_code": _txt(body.get("campaign_code") or body.get("utm_campaign")) or None,
            "landing_url": _txt(body.get("landing_url") or body.get("landing_page")) or None,
            "utm_url": _txt(body.get("utm_url")) or None,
            "start_date": _txt(body.get("start_date") or body.get("start_at")) or None,
            "end_date": _txt(body.get("end_date") or body.get("end_at")) or None,
            "budget": body.get("budget") if body.get("budget") is not None else body.get("planned_budget"),
            "spend": body.get("spend"),
            "impressions": None,
            "clicks": None,
            "ads_provider": None,
            "ads_api": "not_connected",
            "vacancy_id": _txt(body.get("vacancy_id")) or None,
            "status": _txt(body.get("status")) or "active",
            "notes": _txt(body.get("notes") or body.get("comment")),
            "country": _txt(body.get("country")) or None,
            "program": _txt(body.get("program") or body.get("program_of_interest")) or None,
            "utm_source": _txt(body.get("utm_source")) or None,
            "utm_medium": _txt(body.get("utm_medium")) or None,
            "utm_campaign": _txt(body.get("utm_campaign") or body.get("campaign_code")) or None,
            "utm_content": _txt(body.get("utm_content")) or None,
            "utm_term": _txt(body.get("utm_term")) or None,
            "origin": "INTERNAL",
            "data_mode": "REAL",
            "created_by": _txt(body.get("created_by") or role) or None,
            "created_at": _now(),
            "updated_at": _now(),
        }
        from services.recruiting_ops.campaign_model import normalize_campaign

        domain = normalize_campaign(body)
        domain["lifecycle_status"] = domain.get("status")
        domain.pop("status", None)
        item.update(domain)
        if not item.get("name"):
            item["name"] = name
        saved = await self._persist("campaign", item)
        self._bag(org)["campaign"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="campaign",
            entity_id=str(saved["id"]),
            action="campaign_created",
            summary=f"Кампания: {name}",
            role=role,
        )
        return self._ok(item=saved)

    async def update_campaign(self, organization_id: str, campaign_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "campaign", campaign_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Кампания не найдена"}
        patch: dict[str, Any] = {"updated_at": _now()}
        for field in (
            "name",
            "channel",
            "source",
            "medium",
            "campaign_code",
            "landing_url",
            "utm_url",
            "start_date",
            "end_date",
            "budget",
            "spend",
            "status",
            "notes",
            "vacancy_id",
            "project_key",
            "impressions",
            "clicks",
            "country",
            "program",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "utm_term",
            "comment",
            "planned_budget",
        ):
            if field in body:
                patch[field] = body.get(field)
        from services.recruiting_ops.campaign_model import normalize_campaign

        domain = normalize_campaign(body, existing=item)
        domain["lifecycle_status"] = domain.get("status")
        if "status" in body:
            domain["status"] = body.get("status")
        else:
            domain.pop("status", None)
        patch.update({k: v for k, v in domain.items() if k in body or k in {"lifecycle_status", "status_label_ru", "sync_state", "utm", "provider", "external_id"}})
        if "project_key" in patch:
            patch["project_key"] = infer_project_key(source=_txt(patch.get("source") or item.get("source")), project_key=_txt(patch.get("project_key")))
        patch["ads_api"] = "not_connected"
        item.update(patch)
        persisted = await self._persist_patch(org, campaign_id, patch)
        if persisted:
            item = persisted
        self._replace(org, "campaign", item)
        await self._activity(
            organization_id=org,
            entity_type="campaign",
            entity_id=campaign_id,
            action="campaign_updated",
            summary=f"Кампания обновлена: {item.get('name')}",
            role=role,
        )
        return self._ok(item=item)

    def _campaign_spend_entries(self, orgs: list[str], campaign_id: str | None = None) -> list[dict[str, Any]]:
        rows = []
        for item in self._collect_kind(orgs, "campaign_spend"):
            if campaign_id and _txt(item.get("campaign_id")) != _txt(campaign_id):
                continue
            rows.append(item)
        return rows

    async def record_manual_spend(self, organization_id: str, campaign_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        from services.recruiting_ops.ads_economics import _num

        org = _org(organization_id)
        await self.ensure_hydrated(org)
        campaign = self._find(org, "campaign", campaign_id)
        if not campaign:
            return {"ok": False, "error": "not_found", "message_ru": "Кампания не найдена"}
        amount = _num(body.get("amount") if body.get("amount") is not None else body.get("spend"))
        if amount is None or amount < 0:
            return {"ok": False, "error": "validation", "message_ru": "Укажите сумму расхода"}
        item = {
            "id": str(body.get("id") or uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "campaign_id": campaign_id,
            "amount": amount,
            "currency": _txt(body.get("currency") or campaign.get("currency") or "EUR") or "EUR",
            "spent_on": _txt(body.get("spent_on") or body.get("date") or body.get("period")) or _today(),
            "period_start": _txt(body.get("period_start") or body.get("date") or body.get("spent_on")) or None,
            "period_end": _txt(body.get("period_end")) or None,
            "comment": _txt(body.get("comment") or body.get("notes")),
            "entered_by": _txt(body.get("entered_by") or role) or None,
            "source": "OPERATOR_MANUAL",
            "label_ru": "Расход внесён оператором",
            "provider_synced": False,
            "data_mode": "REAL",
            "created_at": _now(),
            "updated_at": _now(),
        }
        saved = await self._persist("campaign_spend", item)
        self._bag(org)["campaign_spend"].insert(0, saved)
        from services.recruiting_ops.ads_economics import sum_manual_spend

        total = sum_manual_spend(self._campaign_spend_entries([org], campaign_id))
        patch = {"spend": total, "spend_source": "OPERATOR_MANUAL", "updated_at": _now()}
        persisted = await self._persist_patch(org, campaign_id, patch)
        if persisted:
            campaign = persisted
            self._replace(org, "campaign", campaign)
        else:
            campaign.update(patch)
            self._replace(org, "campaign", campaign)
        await self._activity(
            organization_id=org,
            entity_type="campaign",
            entity_id=campaign_id,
            action="manual_spend_recorded",
            summary=f"Расход внесён оператором: {amount} {item['currency']}",
            role=role,
            payload={"amount": amount, "currency": item["currency"], "spend_id": saved["id"], "provider_synced": False},
        )
        return self._ok(item=saved, campaign=campaign)

    async def campaign_detail(
        self,
        organization_id: str,
        campaign_id: str,
        role: str | None = None,
        *,
        date_range: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        orgs = self._read_orgs(organization_id, role)
        for read_org in orgs:
            await self.ensure_hydrated(read_org)
        campaign = self._find(org, "campaign", campaign_id)
        if not campaign:
            for read_org in orgs:
                campaign = self._find(read_org, "campaign", campaign_id)
                if campaign:
                    break
        if not campaign:
            return {"ok": False, "error": "not_found", "message_ru": "Кампания не найдена"}
        from services.recruiting_ops.ads_economics import (
            campaign_matches_lead,
            count_stages,
            funnel_economics,
            item_in_window,
            recruiter_attribution,
            public_date_range,
            resolve_date_window,
            sum_manual_spend,
        )
        from services.recruiting_ops.attribution import production_cohort

        window = resolve_date_window(preset=date_range, date_from=date_from, date_to=date_to)
        key = _txt(campaign.get("project_key")) or VANGUARD_PROJECT_KEY
        leads = [item for item in self._collect_kind(orgs, "lead") if belongs_to_project(item, key)]
        cands = [item for item in self._collect_kind(orgs, "candidate") if belongs_to_project(item, key)]
        cohort = production_cohort(leads, cands)
        camp_leads = [item for item in cohort["leads"] if campaign_matches_lead(campaign, item) and item_in_window(item, window)]
        lead_ids = {_txt(item.get("id")) for item in camp_leads}
        camp_cands = [
            item
            for item in cohort["candidates"]
            if (
                campaign_matches_lead(campaign, item)
                or _txt(item.get("lead_id")) in lead_ids
                or lead_ids.intersection({_txt(x) for x in (item.get("lead_ids") or [])})
            )
            and item_in_window(item, window)
        ]
        spends = [item for item in self._campaign_spend_entries(orgs, campaign_id) if item_in_window(item, window)]
        spend = sum_manual_spend(spends)
        if spend is None and campaign.get("spend") is not None and window.get("preset") == "30d":
            spend = campaign.get("spend")
        stages = count_stages(camp_cands)
        qualified_leads = [item for item in camp_leads if _txt(item.get("status")).lower() in {"qualified", "converted"}]
        economics = funnel_economics(
            impressions=None,
            clicks=None,
            applications=len(camp_leads),
            qualified=max(len(qualified_leads), stages["qualified"]),
            interviews=stages["interviews"],
            approved=stages["approved"],
            hired=stages["hired"],
            spend=spend,
        )
        return self._ok(
            item=campaign,
            campaign=campaign,
            funnel=economics,
            recruiters=recruiter_attribution(camp_cands),
            spend_entries=spends,
            spend_source="OPERATOR_MANUAL" if spends else ("CAMPAIGN_FIELD" if spend is not None else "UNAVAILABLE"),
            date_range=public_date_range(window),
            traffic={"production_only": True},
            origin_label_ru=campaign.get("origin_label_ru") or "Внутренняя кампания — рекламный кабинет не подключён.",
        )

    async def upsert_ads_entity(self, organization_id: str, kind: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.recruiting_ops.ads_control import normalize_ads_entity

        org = _org(organization_id)
        await self.ensure_hydrated(org)
        parsed = normalize_ads_entity(kind, body, project_key=VANGUARD_PROJECT_KEY)
        if not parsed.get("ok"):
            return parsed
        item = {
            "id": str(body.get("id") or uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "kind": kind,
            "data_mode": "REAL",
            "created_at": _now(),
            "updated_at": _now(),
            **parsed["item"],
        }
        saved = await self._persist(kind, item)
        self._bag(org)[kind].insert(0, saved)
        return self._ok(item=saved)

    async def ads_control_center(
        self,
        organization_id: str,
        project_key: str,
        role: str | None = None,
        *,
        date_range: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        orgs = self._read_orgs(organization_id, role)
        for read_org in orgs:
            await self.ensure_hydrated(read_org)
        spec = get_project(project_key) or {"project_key": project_key}
        key = spec.get("project_key") or VANGUARD_PROJECT_KEY
        leads = [item for item in self._collect_kind(orgs, "lead") if belongs_to_project(item, key)]
        cands = [item for item in self._collect_kind(orgs, "candidate") if belongs_to_project(item, key)]
        events = [item for item in self._collect_kind(orgs, "tracking") if belongs_to_project(item, key)]
        from services.recruiting_ops.ads_economics import (
            item_in_window,
            normalize_source,
            provider_connect_panel,
            resolve_date_window,
            source_economics,
            sum_manual_spend,
        )
        from services.recruiting_ops.attribution import production_cohort, source_analytics

        window = resolve_date_window(preset=date_range, date_from=date_from, date_to=date_to)
        cohort = production_cohort(leads, cands, events)
        leads = [item for item in cohort["leads"] if item_in_window(item, window)]
        cands = [item for item in (cohort["candidates"] or []) if item_in_window(item, window)]
        events = [item for item in (cohort["events"] or []) if item_in_window(item, window)]
        campaigns = self._campaign_metrics(org, key, leads, cands, events, orgs=orgs, window=window)
        from services.recruiting_ops.ads_control import control_center

        payload = control_center(project_key=key, campaigns=campaigns)
        payload["source_analytics"] = source_analytics(leads, cands)
        payload["funnel"] = self._marketing_funnel(org, key, leads, cands, {})
        payload["attribution"] = self._attribution_snapshot(leads, events)
        payload["traffic"] = {
            "production_only": True,
            "excluded_test_leads": cohort["excluded_test_leads"],
            "excluded_test_candidates": cohort["excluded_test_candidates"],
            "excluded_test_events": cohort["excluded_test_events"],
        }
        payload["entities"] = {kind: list(self._bag(org).get(kind) or []) for kind in ("ad_account", "ad_set", "creative", "audience", "ads_metrics")}
        from services.recruiting_ops.provider_connections import connection_center_payload, provider_health_snapshot
        from services.recruiting_ops.provider_health import monitor_snapshot

        connections = self._bag(org).get("provider_connection") or []
        live_provider = any(
            str(item.get("status") or "").upper() == "CONNECTED"
            and str(item.get("mode") or "").upper() != "MOCK"
            and (item.get("live_verified") or item.get("mocked_http"))
            for item in connections
        )
        from services.recruiting_ops.ads_economics import count_stages, ratio

        qualified = [item for item in leads if _txt(item.get("status")).lower() in {"qualified", "converted"}]
        stages = count_stages(cands)
        interviews = stages["interviews"]
        hires = stages["hired"]
        approved = stages["approved"]
        from services.recruiting_ops.provider_metrics import aggregate_live_metrics

        live_rows = [item for item in self._bag(org).get("ads_metrics") or [] if item.get("source") == "LIVE"]
        live_agg = aggregate_live_metrics(live_rows)
        impressions = live_agg["impressions"] if live_provider else None
        clicks = live_agg["clicks"] if live_provider else None
        operator_spend = sum_manual_spend([item for item in self._campaign_spend_entries(orgs) if item_in_window(item, window)])
        from services.recruiting_ops.provider_layer import default_spend_policy, fx_normalize, resolve_spend

        spend_resolved = resolve_spend(
            manual=operator_spend,
            provider=live_agg.get("spend") if live_provider else None,
            policy=default_spend_policy(connected=live_provider),
            connected=live_provider,
        )
        spend = spend_resolved["amount"]
        spend_source = (
            "LIVE"
            if spend_resolved.get("origin") == "PROVIDER"
            else ("OPERATOR_MANUAL" if spend_resolved.get("origin") == "MANUAL" else "UNAVAILABLE")
        )
        apps = len(leads)
        payload["sections"] = ["overview", "providers", "campaigns", "leads", "funnel", "attribution", "source_analytics", "automation", "ai_optimization", "diagnostics"]
        payload["date_range"] = {"preset": window["preset"], "from": window["from"], "to": window["to"]}
        payload["kpis"] = {
            "spend": spend,
            "applications": apps,
            "cpl": ratio(spend, float(apps)) if spend is not None and apps else None,
            "qualified": max(len(qualified), stages["qualified"]),
            "interviews": interviews,
            "approved": approved,
            "hired": hires,
            "cost_per_hire": ratio(spend, float(hires)) if spend is not None and hires else None,
        }
        payload["overview"] = {
            "connected_providers": sum(1 for item in connections if str(item.get("status") or "").upper() == "CONNECTED"),
            "active_campaigns": len([c for c in campaigns if str(c.get("status") or "").upper() in {"ACTIVE", "active"}]),
            "spend": spend,
            "impressions": impressions,
            "clicks": clicks,
            "ctr": live_agg.get("ctr") if live_provider else None,
            "cpc": live_agg.get("cpc") if live_provider else None,
            "leads": apps,
            "applications": apps,
            "qualified_candidates": max(len(qualified), stages["qualified"]),
            "interviews": interviews,
            "approved": approved,
            "hires": hires,
            "cost_per_lead": ratio(spend, float(apps)) if spend is not None and apps else None,
            "cost_per_qualified_candidate": ratio(spend, float(max(len(qualified), stages["qualified"]))) if spend is not None and (qualified or stages["qualified"]) else None,
            "cost_per_interview": ratio(spend, float(interviews)) if spend is not None and interviews else None,
            "cost_per_hire": ratio(spend, float(hires)) if spend is not None and hires else None,
            "live_provider_metrics": bool(live_provider and not live_agg.get("no_live_data")),
            "no_live_data": True if not live_provider else bool(live_agg.get("no_live_data")),
            "message_ru": "Нет живых данных" if not live_provider or live_agg.get("no_live_data") else None,
            "data_source": {
                "providers": "LIVE" if live_provider else "UNAVAILABLE",
                "spend": spend_source,
                "impressions": "LIVE" if impressions is not None else "UNAVAILABLE",
                "clicks": "LIVE" if clicks is not None else "UNAVAILABLE",
                "leads": "INTERNAL",
                "qualified_candidates": "INTERNAL",
                "interviews": "INTERNAL",
                "hires": "INTERNAL",
                "cost_per_lead": "CALCULATED" if spend is not None and apps else "UNAVAILABLE",
                "cost_per_qualified_candidate": "CALCULATED" if spend is not None and (qualified or stages["qualified"]) else "UNAVAILABLE",
                "cost_per_interview": "CALCULATED" if spend is not None and interviews else "UNAVAILABLE",
                "cost_per_hire": "CALCULATED" if spend is not None and hires else "UNAVAILABLE",
            },
        }
        spend_by_source: dict[str, float] = {}
        for camp in campaigns:
            src = normalize_source(camp.get("source") or camp.get("utm_source"))
            amount = camp.get("spend")
            if amount is None:
                continue
            spend_by_source[src] = round(spend_by_source.get(src, 0.0) + float(amount), 6)
        payload["source_economics"] = source_economics(leads, cands, spend_by_source)
        payload["provider_connect"] = provider_connect_panel(connections)
        payload["spend_policy"] = {
            **spend_resolved,
            "fx": fx_normalize(spend, source_currency=None, reporting_currency="EUR"),
            "origins": {"manual": operator_spend, "provider": live_agg.get("spend") if live_provider else None},
        }
        payload["provider_health"] = {**provider_health_snapshot(connections), **{"monitor": monitor_snapshot(connections)}}
        payload["title_ru"] = "РЕКЛАМА VANGUARD"
        payload["internal_only"] = True
        payload["provider_connections"] = connection_center_payload(connections)
        payload["automation"] = {"items": list(self._bag(org).get("automation_rule") or []), "approval_required_default": True}
        payload["ai_optimization"] = {"items": list(self._bag(org).get("ai_recommendation") or []), "advisory_only": True, "live_write_access": False}
        payload["campaign_writes"] = {"items": list(self._bag(org).get("campaign_write") or []), "approval_required": True}
        payload["outbound_messages"] = {"items": list(self._bag(org).get("outbound_message") or []), "approval_required": True}
        return self._ok(**payload)

    async def create_task(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        title = _txt(body.get("title"))
        if not title:
            return {"ok": False, "error": "validation", "message_ru": "Укажите задачу"}
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = {
            "id": str(body.get("id") or uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "title": title,
            "lead_id": _txt(body.get("lead_id")) or None,
            "candidate_id": _txt(body.get("candidate_id")) or None,
            "project_key": infer_project_key(
                source=_txt(body.get("source")),
                project_key=_txt(body.get("project_key")) or None,
            ),
            "assignee": _txt(body.get("assignee")) or None,
            "due_date": _parse_date(body.get("due_date") or body.get("due_at")),
            "status": _task_status(body.get("status"), "open"),
            "notes": _txt(body.get("notes")),
            "data_mode": "REAL",
            "created_at": _now(),
            "updated_at": _now(),
        }
        if not item["project_key"] and item["lead_id"]:
            lead = self._find(org, "lead", item["lead_id"])
            item["project_key"] = resolve_project_key(lead) or None
        if not item["project_key"] and item["candidate_id"]:
            cand = self._find(org, "candidate", item["candidate_id"])
            item["project_key"] = resolve_project_key(cand) or None
        saved = await self._persist("task", item)
        self._bag(org)["task"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="task",
            entity_id=str(saved["id"]),
            action="task_created",
            summary=f"Задача: {title}",
            role=role,
            payload={"project_key": item.get("project_key")},
        )
        return self._ok(item=saved)

    async def complete_task(self, organization_id: str, task_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "task", task_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Задача не найдена"}
        patch = {"status": "done", "updated_at": _now()}
        item.update(patch)
        persisted = await self._persist_patch(org, task_id, patch)
        if persisted:
            item = persisted
        self._replace(org, "task", item)
        await self._activity(
            organization_id=org,
            entity_type="task",
            entity_id=task_id,
            action="task_completed",
            summary=f"Задача закрыта: {item.get('title')}",
            role=role,
        )
        return self._ok(item=item)

    async def log_communication(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        text = _txt(body.get("body") or body.get("notes") or body.get("text") or body.get("summary"))
        if not text:
            return {"ok": False, "error": "validation", "message_ru": "Укажите текст коммуникации"}
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        channel = _channel(body.get("channel"))
        from services.recruiting_ops.provider_readiness import messaging_readiness

        channel_key = channel.lower()
        ready = messaging_readiness()["channels"].get(channel_key) or {}
        item = {
            "id": str(body.get("id") or uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "channel": channel,
            "body": text,
            "lead_id": _txt(body.get("lead_id")) or None,
            "candidate_id": _txt(body.get("candidate_id")) or None,
            "project_key": infer_project_key(
                source=_txt(body.get("source")),
                project_key=_txt(body.get("project_key")) or None,
            ),
            "sent": False,
            "journal_only": True,
            "delivery": "manual_log_only",
            "status": "logged",
            "provider_status": ready.get("status") or "NOT_CONFIGURED",
            "data_mode": "REAL",
            "created_at": _now(),
            "updated_at": _now(),
        }
        if not item["project_key"] and item["lead_id"]:
            lead = self._find(org, "lead", item["lead_id"])
            item["project_key"] = resolve_project_key(lead) or None
        if not item["project_key"] and item["candidate_id"]:
            cand = self._find(org, "candidate", item["candidate_id"])
            item["project_key"] = resolve_project_key(cand) or None
        saved = await self._persist("communication", item)
        self._bag(org)["communication"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="communication",
            entity_id=str(saved["id"]),
            action="communication_logged",
            summary=text,
            role=role,
            payload={"channel": channel, "sent": False, "project_key": item.get("project_key")},
        )
        return self._ok(item=saved)

    def _note_ingest_success(self) -> None:
        self._ingest_log["last_success_at"] = _now()
        self._ingest_log["last_check_at"] = self._ingest_log["last_success_at"]
        self._ingest_log["last_successful_check_at"] = self._ingest_log["last_success_at"]

    def _note_ingest_error(self, error: str, message: str) -> None:
        self._ingest_log["last_error_at"] = _now()
        self._ingest_log["last_error"] = {"error": error, "message_ru": message or error}
        self._ingest_log["last_check_at"] = self._ingest_log["last_error_at"]

    def _project_summaries(self, org: str, bag: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        out = []
        for spec in project_catalog():
            key = spec["project_key"]
            leads = [item for item in bag["lead"] if belongs_to_project(item, key)]
            cands = [item for item in bag["candidate"] if belongs_to_project(item, key)]
            last_lead = leads[0] if leads else None
            url = vanguard_website_url() if key == VANGUARD_PROJECT_KEY else None
            out.append(
                {
                    **spec,
                    "organization_id": org,
                    "leads": len(leads),
                    "candidates": len(cands),
                    "active_vacancies": self._active_vacancy_count(org, key),
                    "last_application_at": (last_lead or {}).get("created_at"),
                    "new_leads": len([item for item in leads if _lead_status(item.get("status")) == "new"]),
                    "website_status": status_payload(STATUS_UNKNOWN if not url else STATUS_CONNECTED),
                    "integration_status": status_payload(STATUS_UNKNOWN),
                }
            )
        return out

    def _active_vacancy_count(self, org: str, project_key: str) -> int:
        items = self._filter_project_items(org, "vacancy", list(self._bag(org)["vacancy"]), project_key)
        return len([item for item in items if _txt(item.get("status")).lower() in {"", "open", "active"}])

    async def list_projects(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        orgs = self._read_orgs(organization_id, role)
        for read_org in orgs:
            await self.ensure_hydrated(read_org)
        bag = {kind: self._collect_kind(orgs, kind) for kind in KINDS}
        items = []
        for summary in self._project_summaries(org, bag):
            integration = await self.project_integration(org, summary["project_key"], role)
            items.append(
                {
                    **summary,
                    "website_status": integration.get("website_status"),
                    "integration_status": integration.get("overall"),
                    "last_sync_at": integration.get("last_check_at"),
                    "public_url": integration.get("website", {}).get("public_url"),
                }
            )
        return self._ok(items=items)

    async def project_overview(self, organization_id: str, project_key: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        spec = get_project(project_key)
        if not spec:
            return {"ok": False, "error": "not_found", "message_ru": "Проект не найден"}
        org = _org(organization_id)
        orgs = self._read_orgs(organization_id, role)
        for read_org in orgs:
            await self.ensure_hydrated(read_org)
        key = spec["project_key"]
        leads_all = [item for item in self._collect_kind(orgs, "lead") if belongs_to_project(item, key)]
        cands_all = [item for item in self._collect_kind(orgs, "candidate") if belongs_to_project(item, key)]
        from services.recruiting_ops.attribution import production_cohort, source_analytics

        cohort = production_cohort(leads_all, cands_all)
        leads = list(cohort["leads"])
        cands = list(cohort["candidates"] or [])
        today = _today()
        today_leads = [item for item in leads if _date_only(item.get("created_at") or item.get("submitted_at")) == today]
        converted = [item for item in leads if _lead_status(item.get("status")) == "converted"]
        conversion = round(len(converted) / len(leads), 4) if leads else None
        last_lead = leads[0] if leads else None
        analytics = await self.analytics(org, role, project=key)
        stages = analytics.get("pipeline_stages") if analytics.get("ok") else {}
        integration = await self.project_integration(org, key, role)
        traffic = self._traffic_snapshot(org, key)
        funnel = self._marketing_funnel(org, key, leads, cands, stages if isinstance(stages, dict) else {})
        attribution = self._attribution_snapshot(leads, traffic["events"])

        campaigns = self._campaign_metrics(org, key, leads, cands, traffic["events"])
        comms = [item for item in self._collect_kind(orgs, "communication") if belongs_to_project(item, key)]
        activity = await self.list_activity(org, role, project=key)
        website = (integration.get("website") if integration.get("ok") else {}) or {}
        return self._ok(
            project=spec,
            relationship=[
                {"id": "website", "label_ru": "Сайт Vanguard"},
                {"id": "recruiting", "label_ru": "Рекрутинг"},
                {"id": "leads", "label_ru": "Лиды"},
                {"id": "candidates", "label_ru": "Кандидаты"},
            ],
            website_url=website.get("public_url") or website.get("site_path"),
            website_health=integration.get("website_status"),
            integration_health=integration.get("integration_status"),
            last_successful_connection=integration.get("last_success_at"),
            cards={
                "website_url": website.get("public_url") or website.get("site_path"),
                "website_health": integration.get("website_status"),
                "integration_health": integration.get("integration_status"),
                "last_successful_connection": integration.get("last_success_at"),
                "last_application_at": (last_lead or {}).get("submitted_at") or (last_lead or {}).get("created_at"),
                "applications_today": len(today_leads),
                "applications_7d": self._count_since(leads, 7),
                "applications_30d": self._count_since(leads, 30),
                "leads": len(leads),
                "candidates": len(cands),
                "new_leads": len([item for item in leads if _lead_status(item.get("status")) == "new"]),
                "active_vacancies": self._active_vacancy_count(org, key),
                "lead_to_candidate": conversion,
                "conversion_rate": conversion,
            },
            traffic={
                **traffic,
                "production_only": True,
                "excluded_test_leads": cohort["excluded_test_leads"],
                "excluded_test_candidates": cohort["excluded_test_candidates"],
            },
            attribution=attribution,
            source_analytics=source_analytics(leads, cands),
            recruiting={
                "new_leads": len([item for item in leads if _lead_status(item.get("status")) == "new"]),
                "qualified_leads": len([item for item in leads if _lead_status(item.get("status")) in {"qualified", "converted"}]),
                "candidates": len(cands),
                "interviews": (stages or {}).get("INTERVIEW", 0),
                "accepted": (stages or {}).get("APPROVED", 0) + (stages or {}).get("HIRED", 0),
                "rejected": (stages or {}).get("REJECTED", 0),
            },
            marketing={"campaigns": campaigns, "funnel": funnel, "ads_apis": {"meta": "not_connected", "google": "not_connected", "tiktok": "not_connected"}},
            funnel=funnel,
            recent_leads=leads_all[:10],
            recent_communications=comms[:10],
            recent_activity=(activity.get("items") or [])[:15] if activity.get("ok") else [],
            pipeline=stages,
        )

    def _count_since(self, items: list[dict[str, Any]], days: int) -> int:
        from datetime import timedelta

        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
        return len(
            [
                item
                for item in items
                if (_date_only(item.get("submitted_at") or item.get("created_at") or item.get("timestamp")) or "") >= cutoff
            ]
        )

    def _pct(self, part: int, whole: int) -> float | None:
        if whole <= 0:
            return None
        return round(part / whole, 4)

    def _traffic_snapshot(self, org: str, project_key: str) -> dict[str, Any]:
        from services.recruiting_ops.attribution import is_test_traffic

        events = [
            item
            for item in self._bag(org).get("tracking") or []
            if belongs_to_project(item, project_key) and not is_test_traffic(item)
        ]
        by_type: dict[str, int] = {}
        visitors: set[str] = set()
        sessions: set[str] = set()
        for event in events:
            kind = _txt(event.get("event_type"))
            by_type[kind] = by_type.get(kind, 0) + 1
            if event.get("visitor_id"):
                visitors.add(_txt(event.get("visitor_id")))
            if event.get("session_id"):
                sessions.add(_txt(event.get("session_id")))
        return {
            "visits": by_type.get("page_view", 0) if events else None,
            "unique_visitors": len(visitors) if events else None,
            "sessions": len(sessions) if events else None,
            "application_opens": by_type.get("application_open", 0) if events else None,
            "application_starts": by_type.get("application_start", 0) if events else None,
            "completed_applications": by_type.get("application_success", 0) if events else None,
            "events": events,
            "has_data": bool(events),
        }

    def _attribution_snapshot(self, leads: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:
        rows = leads or events
        if not rows:
            return {
                "source": None,
                "medium": None,
                "campaign": None,
                "content": None,
                "referrer": None,
                "landing_page": None,
                "utm": None,
                "by_source": [],
                "has_data": False,
                "quality": "UNKNOWN",
                "fabricated": False,
            }
        def _top(key: str) -> str | None:
            counts: dict[str, int] = {}
            for row in rows:
                raw = _txt(row.get(key))
                if raw:
                    counts[raw] = counts.get(raw, 0) + 1
            if not counts:
                return None
            return sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0][0]

        from services.recruiting_ops.attribution import source_analytics

        by_source = []
        source_counts: dict[str, int] = {}
        for row in rows:
            raw = _txt(row.get("utm_source") or row.get("source"))
            if raw:
                source_counts[raw] = source_counts.get(raw, 0) + 1
        by_source = [{"source": name, "count": count} for name, count in sorted(source_counts.items(), key=lambda x: (-x[1], x[0]))]

        return {
            "source": _top("utm_source") or _top("source"),
            "medium": _top("utm_medium") or _top("medium"),
            "campaign": _top("utm_campaign") or _top("campaign_code"),
            "content": _top("utm_content"),
            "referrer": _top("referrer"),
            "landing_page": _top("landing_page"),
            "first_touch": {
                "source": _top("first_touch_source") or _top("utm_source"),
                "medium": _top("first_touch_medium"),
                "campaign": _top("first_touch_campaign"),
            },
            "last_touch": {
                "source": _top("last_touch_source") or _top("utm_source"),
                "medium": _top("last_touch_medium"),
                "campaign": _top("last_touch_campaign"),
            },
            "utm": {
                "utm_source": _top("utm_source"),
                "utm_medium": _top("utm_medium"),
                "utm_campaign": _top("utm_campaign"),
                "utm_content": _top("utm_content"),
                "utm_term": _top("utm_term"),
            },
            "by_source": by_source,
            "source_analytics": source_analytics(leads, []),
            "has_data": True,
            "quality": "UTM_MATCH" if _top("utm_campaign") or _top("utm_source") else "UNKNOWN",
            "join_keys": ["utm_campaign", "utm_source", "campaign_code"],
            "fabricated": False,
        }

    def _marketing_funnel(
        self,
        org: str,
        project_key: str,
        leads: list[dict[str, Any]],
        cands: list[dict[str, Any]],
        stages: dict[str, Any],
    ) -> dict[str, Any]:
        traffic = self._traffic_snapshot(org, project_key)
        visit = traffic["visits"]
        open_n = traffic["application_opens"]
        start_n = traffic["application_starts"]
        submitted = traffic["completed_applications"]
        lead_n = len(leads)
        qualified = len([item for item in leads if _lead_status(item.get("status")) in {"qualified", "converted"}])
        cand_n = len(cands)
        interview = int(stages.get("INTERVIEW") or 0)
        accepted = int(stages.get("APPROVED") or 0) + int(stages.get("HIRED") or 0)
        rejected = int(stages.get("REJECTED") or 0)
        steps = [
            {"id": "visit", "label_ru": "Визит", "count": visit},
            {"id": "application_open", "label_ru": "Открытие заявки", "count": open_n},
            {"id": "application_start", "label_ru": "Старт заявки", "count": start_n},
            {"id": "application_submitted", "label_ru": "Заявка отправлена", "count": submitted if submitted is not None else lead_n},
            {"id": "lead", "label_ru": "Лид", "count": lead_n},
            {"id": "qualified", "label_ru": "Квалификация", "count": qualified},
            {"id": "candidate", "label_ru": "Кандидат", "count": cand_n},
            {"id": "interview", "label_ru": "Интервью", "count": interview},
            {"id": "accepted", "label_ru": "Принят", "count": accepted},
            {"id": "rejected", "label_ru": "Отказ", "count": rejected},
        ]
        prev = None
        for step in steps:
            count = step["count"]
            step["conversion"] = self._pct(int(count or 0), int(prev)) if prev and count is not None else None
            if count is not None:
                prev = count
        return {"steps": steps, "has_tracking": bool(traffic["has_data"])}

    def _campaign_metrics(
        self,
        org: str,
        project_key: str,
        leads: list[dict[str, Any]],
        cands: list[dict[str, Any]],
        events: list[dict[str, Any]],
        *,
        orgs: list[str] | None = None,
        window: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        from services.recruiting_ops.ads_control import campaign_costs
        from services.recruiting_ops.ads_economics import (
            campaign_matches_lead,
            count_stages,
            funnel_economics,
            item_in_window,
            normalize_source,
            provider_backed,
            source_label,
            sum_manual_spend,
        )

        read_orgs = orgs or [org]
        out = []
        seen: set[str] = set()
        camps = []
        for read_org in read_orgs:
            for camp in self._bag(read_org)["campaign"]:
                cid = _txt(camp.get("id"))
                if cid in seen:
                    continue
                seen.add(cid)
                camps.append(camp)
        for camp in camps:
            if not belongs_to_project(camp, project_key) and _txt(camp.get("source")).lower() not in {"vanguard", "instagram", "meta", "facebook", "google", "tiktok", "organic", "direct", "referral"}:
                continue
            camp_leads = [item for item in leads if campaign_matches_lead(camp, item)]
            lead_ids = {_txt(item.get("id")) for item in camp_leads}
            camp_cands = [
                item
                for item in cands
                if campaign_matches_lead(camp, item)
                or _txt(item.get("lead_id")) in lead_ids
                or lead_ids.intersection({_txt(x) for x in (item.get("lead_ids") or [])})
            ]
            visits = [item for item in events if campaign_matches_lead(camp, item)]
            spend_rows = [item for item in self._campaign_spend_entries(read_orgs, _txt(camp.get("id"))) if not window or item_in_window(item, window)]
            spend = sum_manual_spend(spend_rows)
            if spend is None:
                spend = camp.get("spend")
            stages = count_stages(camp_cands)
            qualified_leads = [item for item in camp_leads if _txt(item.get("status")).lower() in {"qualified", "converted"}]
            costs = campaign_costs(
                spend=spend,
                impressions=None,
                clicks=None,
                applications=len(camp_leads),
                leads=len(camp_leads),
                candidates=len(camp_cands),
            )
            economics = funnel_economics(
                impressions=None,
                clicks=None,
                applications=len(camp_leads),
                qualified=max(len(qualified_leads), stages["qualified"]),
                interviews=stages["interviews"],
                approved=stages["approved"],
                hired=stages["hired"],
                spend=spend,
            )
            src = normalize_source(camp.get("source") or camp.get("utm_source"))
            item = dict(camp)
            item["visits"] = len(visits) if visits else None
            item["applications"] = len(camp_leads)
            item["leads"] = len(camp_leads)
            item["candidates"] = len(camp_cands)
            item["qualified"] = economics["qualified"]
            item["interviews"] = economics["interviews"]
            item["approved"] = economics["approved"]
            item["hired"] = economics["hired"]
            item["conversion"] = economics["conversion"]
            item["cost_per_hire"] = economics["cost_per_hire"]
            item["source"] = src
            item["source_label_ru"] = source_label(src)
            item["provider_backed"] = provider_backed(src)
            item["provider_status"] = "NOT_CONFIGURED" if provider_backed(src) else None
            item["provider_status_label_ru"] = "НЕ ПОДКЛЮЧЕНО" if provider_backed(src) else None
            item["spend_source"] = "OPERATOR_MANUAL" if spend_rows else ("CAMPAIGN_FIELD" if spend is not None else "UNAVAILABLE")
            item["spend_label_ru"] = "Расход внесён оператором" if spend_rows else None
            item["origin"] = camp.get("origin") or "INTERNAL"
            item["origin_label_ru"] = camp.get("origin_label_ru") or "Внутренняя кампания — рекламный кабинет не подключён."
            item["funnel"] = economics
            item["spend_entries"] = spend_rows
            item.update(costs)
            out.append(item)
        return out

    async def project_integration(self, organization_id: str, project_key: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        spec = get_project(project_key)
        if not spec:
            return {"ok": False, "error": "not_found", "message_ru": "Проект не найден"}
        return await self._run_integration_check(spec)

    async def check_project_integration(self, organization_id: str, project_key: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        spec = get_project(project_key)
        if not spec:
            return {"ok": False, "error": "not_found", "message_ru": "Проект не найден"}
        return await self._run_integration_check(spec, probe_website=True)

    async def _run_integration_check(self, spec: dict[str, Any], *, probe_website: bool = False) -> dict[str, Any]:
        from services.recruiting_ops.ingest_auth import resolve_ingest_secret

        org = _org(os.getenv("VANGUARD_ORGANIZATION_ID") or "ados")
        await self.ensure_hydrated(org)
        self._ingest_log["last_check_at"] = _now()
        url = vanguard_website_url()
        website_code, website_reason = STATUS_NOT_CONFIGURED, "Публичный URL сайта не настроен (VANGUARD_WEBSITE_URL)."
        if url:
            website_code, website_reason = STATUS_CONNECTED, "URL сайта задан."
            if probe_website:
                website_code, website_reason = await self._probe_website(url)
        secret = resolve_ingest_secret()
        if secret:
            endpoint_code, endpoint_reason = STATUS_CONNECTED, "HMAC ingest secret настроен на сервере."
        elif is_production_runtime():
            endpoint_code, endpoint_reason = STATUS_DISCONNECTED, "VANGUARD_INGEST_SECRET не задан в production."
        else:
            endpoint_code, endpoint_reason = STATUS_DEGRADED, "Production secret не задан; используется DEV fallback secret."
        recruiting_code, recruiting_reason = STATUS_CONNECTED, "Recruiting API отвечает."
        db_code, db_reason = await self._storage_probe_reason()
        if not os.environ.get("PYTEST_CURRENT_TEST"):
            await self.recover_tracking_records()
        tracking_diag = self.tracking_diagnostics()
        tracking_code, tracking_reason = tracking_diag["code"], tracking_diag.get("reason_ru") or ""
        website_status = status_payload(website_code, reason_ru=website_reason)
        integ_codes = [endpoint_code, recruiting_code, db_code]
        if STATUS_DISCONNECTED in integ_codes:
            overall_code = STATUS_DISCONNECTED
        elif STATUS_DEGRADED in integ_codes:
            overall_code = STATUS_DEGRADED
        else:
            overall_code = STATUS_CONNECTED
        overall_reason = "; ".join(
            part
            for part in (endpoint_reason, recruiting_reason, db_reason)
            if part
        )
        stages = [
            {"id": "website", "label_ru": "Сайт Vanguard", "code": website_status["code"], "status_label_ru": website_status["label_ru"], "reason_ru": website_reason},
            {"id": "vanguard_endpoint", "label_ru": "Серверный endpoint Vanguard", "code": endpoint_code, "status_label_ru": status_payload(endpoint_code)["label_ru"], "reason_ru": endpoint_reason},
            {"id": "recruiting_api", "label_ru": "Recruiting API", "code": recruiting_code, "status_label_ru": status_payload(recruiting_code)["label_ru"], "reason_ru": recruiting_reason},
            {"id": "database", "label_ru": "База данных", "code": db_code, "status_label_ru": status_payload(db_code)["label_ru"], "reason_ru": db_reason, "ui_state": status_payload(db_code)["ui_state"]},
            {"id": "tracking", "label_ru": "Трекинг", "code": tracking_code, "status_label_ru": status_payload(tracking_code)["label_ru"], "reason_ru": tracking_reason, "ui_state": status_payload(tracking_code)["ui_state"]},
        ]
        if overall_code == STATUS_CONNECTED:
            self._ingest_log["last_successful_check_at"] = self._ingest_log.get("last_check_at")
        last_lead = None
        org_id = os.getenv("VANGUARD_ORGANIZATION_ID") or "ados"
        bag = self._bag(_org(org_id))
        leads = [item for item in bag["lead"] if belongs_to_project(item, spec["project_key"])]
        if leads:
            last_lead = leads[0]
        diagnostics = {
            "website": status_payload(website_code, reason_ru=website_reason),
            "integration": status_payload(overall_code, reason_ru=overall_reason),
            "database": status_payload(db_code, reason_ru=db_reason),
            "tracking": {**status_payload(tracking_code, reason_ru=tracking_reason), **{k: tracking_diag.get(k) for k in ("delivered", "retrying", "failed", "provider_not_configured", "oldest_pending", "last_delivery")}},
            "last_application": (last_lead or {}).get("submitted_at") or (last_lead or {}).get("created_at"),
            "last_synchronization": self._ingest_log.get("last_success_at"),
            "last_successful_health_check": self._ingest_log.get("last_successful_check_at"),
            "last_checked": self._ingest_log.get("last_check_at"),
            "failure_reason": (self._ingest_log.get("last_error") or {}).get("message_ru") if overall_code != STATUS_CONNECTED else None,
        }
        return self._ok(
            project=spec,
            overall=status_payload(overall_code, reason_ru=overall_reason),
            website_status=website_status,
            integration_status=status_payload(overall_code, reason_ru=overall_reason),
            tracking_status=status_payload(tracking_code, reason_ru=tracking_reason),
            database_status=status_payload(db_code, reason_ru=db_reason),
            diagnostics=diagnostics,
            stages=stages,
            website={
                "name": spec["name"],
                "public_url": url,
                "site_path": "/vanguard",
                "environment": "production" if is_production_runtime() else "development",
            },
            last_success_at=self._ingest_log.get("last_success_at"),
            last_successful_check_at=self._ingest_log.get("last_successful_check_at"),
            last_error=self._ingest_log.get("last_error"),
            last_error_at=self._ingest_log.get("last_error_at"),
            last_check_at=self._ingest_log.get("last_check_at"),
        )

    def _tracking_health_reason(self) -> tuple[str, str]:
        diag = self.tracking_diagnostics()
        return str(diag.get("code") or STATUS_UNKNOWN), str(diag.get("reason_ru") or "")

    def _connections(self, org: str) -> list[dict[str, Any]]:
        return list(self._bag(org).get("provider_connection") or [])

    def _sync_runtime_connections(self, org: str) -> None:
        from services.recruiting_ops.provider_connections import PROVIDERS, set_runtime_connected

        rows = {str(item.get("provider") or ""): item for item in self._connections(org)}
        for provider in PROVIDERS:
            if provider == "telegram":
                set_runtime_connected(provider, False)
                continue
            row = rows.get(provider) or {}
            connected = str(row.get("status") or "").upper() == "CONNECTED" and row.get("enabled") is not False
            set_runtime_connected(provider, connected)

    def _index_whatsapp_phone_maps(self) -> None:
        from services.recruiting_ops.whatsapp_ops import default_vanguard_org, env_value, register_phone_org

        env_phone = env_value("WHATSAPP_PHONE_NUMBER_ID")
        if env_phone:
            register_phone_org(env_phone, default_vanguard_org())
        for org, bag in self._mem.items():
            for item in bag.get("whatsapp_phone_map") or []:
                phone = _txt(item.get("phone_number_id"))
                if phone:
                    register_phone_org(phone, _txt(item.get("organization_id") or org))

    async def _persist_whatsapp_phone_map(self, org: str, phone_number_id: str) -> None:
        from services.recruiting_ops.whatsapp_ops import register_phone_org

        pnid = _txt(phone_number_id)
        if not pnid:
            return
        register_phone_org(pnid, org)
        existing = next(
            (item for item in self._bag(org).get("whatsapp_phone_map") or [] if _txt(item.get("phone_number_id")) == pnid),
            None,
        )
        payload = {
            "organization_id": org,
            "tenant_id": org,
            "phone_number_id": pnid,
            "project_key": VANGUARD_PROJECT_KEY,
            "status": "active",
            "updated_at": _now(),
        }
        if existing:
            existing.update(payload)
            persisted = await self._persist_patch(org, str(existing["id"]), payload)
            if persisted:
                self._replace(org, "whatsapp_phone_map", persisted)
            else:
                self._replace(org, "whatsapp_phone_map", existing)
            return
        payload["id"] = str(uuid.uuid4())
        payload["created_at"] = _now()
        saved = await self._persist("whatsapp_phone_map", payload)
        self._bag(org).setdefault("whatsapp_phone_map", []).insert(0, saved)
        default_org = _org(os.getenv("VANGUARD_ORGANIZATION_ID") or "ados")
        if default_org != org:
            mirror = dict(payload)
            mirror["id"] = str(uuid.uuid4())
            mirrored = await self._persist("whatsapp_phone_map", {**mirror, "organization_id": org, "tenant_id": org})
            self._bag(default_org).setdefault("whatsapp_phone_map", []).insert(0, mirrored)

    async def resolve_whatsapp_org(self, phone_number_id: str) -> str | None:
        from services.recruiting_ops.whatsapp_ops import org_for_phone_number_id

        cached = org_for_phone_number_id(phone_number_id)
        if cached:
            return cached
        self._index_whatsapp_phone_maps()
        cached = org_for_phone_number_id(phone_number_id)
        if cached:
            return cached
        default_org = _org(os.getenv("VANGUARD_ORGANIZATION_ID") or "ados")
        await self.ensure_hydrated(default_org)
        self._index_whatsapp_phone_maps()
        return org_for_phone_number_id(phone_number_id)

    async def provider_connection_center(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        self._sync_runtime_connections(org)
        from services.recruiting_ops.provider_connections import connection_center_payload, wizard_spec

        payload = connection_center_payload(self._connections(org))
        payload["wizards"] = {key: wizard_spec(key) for key in ("meta", "google", "tiktok", "telegram", "whatsapp", "email")}
        from services.recruiting_ops.provider_registry import provider_registry

        payload["registry"] = provider_registry(self._connections(org))["items"]
        return payload

    async def provider_wizard(self, provider: str) -> dict[str, Any]:
        from services.recruiting_ops.provider_connections import wizard_spec

        return wizard_spec(provider)

    async def configure_provider(self, organization_id: str, provider: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require_provider_admin(role, provider, "configure")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        key = _txt(provider).lower()
        from services.recruiting_ops.provider_connections import PROVIDERS, WIZARD_FIELDS, default_connection
        from services.recruiting_ops.secret_store import get_secret_store, public_secret_audit

        if key not in PROVIDERS:
            return {"ok": False, "error": "not_found", "message_ru": "Неизвестный провайдер"}
        store = get_secret_store()
        public: dict[str, Any] = {}
        scopes = body.get("scopes") if isinstance(body.get("scopes"), list) else []
        if _txt(body.get("scopes")):
            scopes = [part.strip() for part in _txt(body.get("scopes")).split(",") if part.strip()]
        for field in WIZARD_FIELDS[key]:
            fid = field["id"]
            if fid not in body or body.get(fid) in (None, ""):
                continue
            if field.get("secret"):
                store.put(key, fid, str(body.get(fid)), scopes=list(scopes) if isinstance(scopes, list) else [], organization_id=org)
                await self._activity(
                    organization_id=org,
                    entity_type="provider_connection",
                    entity_id=key,
                    action="credential_metadata_changed",
                    summary=f"Метаданные секрета {key}.{fid} обновлены",
                    role=role,
                    payload=public_secret_audit("put", key, fid),
                )
            else:
                public[fid] = body.get(fid)
                if key == "whatsapp" and fid in {"phone_number_id", "business_account_id"}:
                    store.put(key, fid, str(body.get(fid)))
        existing = next((item for item in self._connections(org) if _txt(item.get("provider")) == key), None)
        row = existing or default_connection(key)
        row.update(
            {
                "organization_id": org,
                "public": {**(row.get("public") or {}), **public},
                "account_id": public.get("ad_account_id") or public.get("customer_id") or public.get("advertiser_id") or public.get("phone_number_id") or public.get("email_from") or row.get("account_id"),
                "workspace_id": public.get("business_id") or public.get("manager_id") or public.get("target_chat") or public.get("business_account_id") or row.get("workspace_id"),
                "scopes": scopes or row.get("scopes") or [],
                "status": "AUTHORIZING" if key in {"meta", "google", "tiktok"} else "CONFIGURING",
                "enabled": True,
                "mode": "LIVE",
                "connected": False,
                "updated_at": _now(),
            }
        )
        if key == "whatsapp" and public.get("phone_number_id"):
            await self._persist_whatsapp_phone_map(org, str(public.get("phone_number_id")))
        from services.recruiting_ops.provider_connections import TELEGRAM_FROZEN

        if key == "telegram" and TELEGRAM_FROZEN:
            row["status"] = "DISABLED"
            row["enabled"] = False
            row["frozen"] = True
            row["connected"] = False
        if not existing:
            row["id"] = str(uuid.uuid4())
            row["created_at"] = _now()
            saved = await self._persist("provider_connection", row)
            self._bag(org)["provider_connection"].insert(0, saved)
        else:
            persisted = await self._persist_patch(org, str(row["id"]), row)
            saved = persisted or row
            self._replace(org, "provider_connection", saved)
        await self._activity(
            organization_id=org,
            entity_type="provider_connection",
            entity_id=str(saved.get("id")),
            action="provider_configured",
            summary=f"Провайдер {key}: настройка",
            role=role,
            payload={"provider": key, "status": saved.get("status")},
        )
        self._sync_runtime_connections(org)
        from services.recruiting_ops.provider_connections import public_card

        return self._ok(item=public_card(saved))

    async def provider_action(self, organization_id: str, provider: str, action: str, body: dict[str, Any] | None = None, role: str | None = None) -> dict[str, Any]:
        key = _txt(provider).lower()
        act = _txt(action).lower()
        if act == "diagnostics":
            denied = require(role, "list")
        elif act in {"test", "test_connection", "health", "list_accounts"}:
            denied = require(role, "update")
        else:
            denied = require_provider_admin(role, key, act if act != "disable" else "disconnect")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        body = body or {}
        from services.recruiting_ops.provider_adapters import get_adapter, mock_providers_allowed
        from services.recruiting_ops.provider_connections import PROVIDERS, default_connection, public_card

        if key not in PROVIDERS:
            return {"ok": False, "error": "not_found", "message_ru": "Неизвестный провайдер"}
        from services.recruiting_ops.provider_connections import TELEGRAM_FROZEN, TELEGRAM_FROZEN_MESSAGE_RU, public_card

        if key == "email" and act in {"test_email", "send_test", "test-email"}:
            return await self.test_smtp_email(org, body, role=role)
        if key == "telegram" and TELEGRAM_FROZEN:
            existing = next((item for item in self._connections(org) if _txt(item.get("provider")) == key), None)
            row = existing or default_connection(key)
            row.update(
                {
                    "organization_id": org,
                    "status": "DISABLED",
                    "frozen": True,
                    "enabled": False,
                    "connected": False,
                    "last_health_check_at": _now(),
                    "updated_at": _now(),
                }
            )
            if not existing:
                row["id"] = str(uuid.uuid4())
                row["created_at"] = _now()
                saved = await self._persist("provider_connection", row)
                self._bag(org)["provider_connection"].insert(0, saved)
            else:
                persisted = await self._persist_patch(org, str(row["id"]), row)
                saved = persisted or row
                self._replace(org, "provider_connection", saved)
            self._sync_runtime_connections(org)
            return self._ok(
                item=public_card(saved),
                adapter={
                    "ok": True,
                    "status": "DISABLED",
                    "frozen": True,
                    "connected": False,
                    "mode": "LIVE",
                    "message_ru": TELEGRAM_FROZEN_MESSAGE_RU,
                },
            )
        mode = _txt(body.get("mode") or "LIVE").upper()
        if mode == "MOCK" and not mock_providers_allowed():
            return {"ok": False, "error": "forbidden", "message_ru": "Mock-режим запрещён в production."}
        adapter = get_adapter(key, mode=mode)
        existing = next((item for item in self._connections(org) if _txt(item.get("provider")) == key), None)
        row = existing or default_connection(key)
        if act in {"list_accounts", "accounts"}:
            return await self.list_provider_accounts(org, key, role=role)
        if act in {"select_account", "select"}:
            return await self.select_provider_account(org, key, body, role=role)
        if act in {"enable_sync", "disable_sync"}:
            return await self.set_provider_sync(org, key, enabled=act == "enable_sync", role=role)
        if act in {"sync", "sync-metrics"}:
            return await self.sync_provider_metrics(org, key, role=role)
        result: dict[str, Any]
        if act in {"test", "test_connection", "health", "refresh", "refresh_credentials"}:
            result = adapter.invoke("health_check", organization_id=org)
        elif act in {"connect", "reconnect"}:
            result = adapter.invoke("connect", organization_id=org)
        elif act in {"disable", "disconnect"}:
            result = adapter.invoke("disconnect")
        elif act == "diagnostics":
            return await self.provider_diagnostics(org, key, role=role)
        else:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестное действие"}
        from services.recruiting_ops.provider_state import normalize_provider_status, status_from_error

        previous_status = _txt(row.get("status"))
        ads = key in {"meta", "google", "tiktok"}
        status = str(result.get("status") or row.get("status") or "NOT_CONFIGURED")
        if ads:
            status = normalize_provider_status(status)
        if act in {"disable", "disconnect"}:
            status = "DISCONNECTED" if ads else "NOT_CONFIGURED"
            row["enabled"] = False
            row["sync_enabled"] = False
            row["live_verified"] = False
            row["connected"] = False
            from services.recruiting_ops.secret_store import delete_tenant_credentials

            if ads:
                delete_tenant_credentials(key, organization_id=org)
        elif result.get("mock") or mode == "MOCK":
            if result.get("connected"):
                status = "CONNECTED"
                row["enabled"] = True
        elif result.get("connected") and (result.get("live_verified") or result.get("mocked_http")):
            status = "CONNECTED"
            row["enabled"] = True
        elif ads and result.get("connected") and not result.get("live_verified"):
            status = "AUTHORIZING"
            row["enabled"] = True
        elif result.get("connected"):
            status = "CONNECTED"
            row["enabled"] = True
        elif ads and not result.get("ok"):
            status = status_from_error(result.get("error") or result.get("error_code"))
        row.update(
            {
                "organization_id": org,
                "status": status,
                "mode": result.get("mode") or mode,
                "mock": bool(result.get("mock") or mode == "MOCK"),
                "connected": bool(result.get("connected")),
                "last_health_check_at": _now(),
                "last_error": None if result.get("ok") else (result.get("error") or result.get("message_ru")),
                "latency_ms": result.get("latency_ms"),
                "live_verified": bool(result.get("live_verified")),
                "mocked_http": bool(result.get("mocked_http")),
                "identity": result.get("identity") or row.get("identity") or {},
                "consecutive_failures": 0 if result.get("connected") else int(row.get("consecutive_failures") or 0) + (0 if act in {"disable", "disconnect"} else 1),
                "updated_at": _now(),
            }
        )
        if result.get("ok") and result.get("connected"):
            row["last_successful_request_at"] = _now()
        from services.recruiting_ops.provider_health import record_check

        record_check(key, result)
        if not existing:
            row["id"] = str(uuid.uuid4())
            row["created_at"] = _now()
            saved = await self._persist("provider_connection", row)
            self._bag(org)["provider_connection"].insert(0, saved)
        else:
            persisted = await self._persist_patch(org, str(row["id"]), row)
            saved = persisted or row
            self._replace(org, "provider_connection", saved)
        self._sync_runtime_connections(org)
        reactivation = None
        if str(saved.get("status")).upper() == "CONNECTED":
            reactivation = await self.reactivate_waiting_provider(org, key, role=role)
        await self._activity(
            organization_id=org,
            entity_type="provider_connection",
            entity_id=str(saved.get("id")),
            action=f"provider_{act}",
            summary=f"Провайдер {key}: {act}",
            role=role,
            payload={"provider": key, "status": saved.get("status"), "mode": saved.get("mode"), "secret": None},
        )
        new_status = _txt(saved.get("status"))
        if previous_status != new_status:
            await self._activity(
                organization_id=org,
                entity_type="provider_connection",
                entity_id=str(saved.get("id")),
                action="provider_health_transition",
                summary=f"Провайдер {key}: {previous_status or 'NONE'} → {new_status}",
                role=role,
                payload={"provider": key, "from": previous_status or None, "to": new_status, "secret": None},
            )
        return self._ok(item=public_card(saved), adapter=result, reactivation=reactivation)

    async def reactivate_waiting_provider(self, organization_id: str, provider: str, role: str | None = None, *, batch_limit: int = 50) -> dict[str, Any]:
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        dest = _txt(provider).lower()
        from services.recruiting_ops.tracking_lifecycle import WAITING_PROVIDER, RETRYING, iso_now
        from services.recruiting_ops.tracking_adapters import destination_of
        from services.recruiting_ops.tracking_worker import get_tracking_worker

        activated: list[str] = []
        skipped: list[str] = []
        errors: list[str] = []
        for item in list(self._bag(org).get("tracking") or []):
            if len(activated) >= batch_limit:
                break
            if destination_of(item) != dest:
                continue
            status = str(item.get("delivery_status") or "")
            if status != WAITING_PROVIDER:
                skipped.append(str(item.get("id")))
                continue
            eid = str(item.get("event_id") or item.get("id") or "")
            if eid and eid in activated:
                continue
            patch = {
                "delivery_status": RETRYING,
                "delivery_class": "retry_scheduled",
                "next_attempt_at": iso_now(),
                "reactivation_batch": True,
            }
            try:
                persisted = await self._persist_patch(org, str(item.get("id")), patch)
                if persisted:
                    item.update(persisted)
                else:
                    item.update(patch)
                get_tracking_worker().enqueue(item)
                activated.append(str(item.get("id")))
            except Exception as exc:
                errors.append(str(item.get("id")))
                logger.warning("waiting_provider reactivation failed id=%s: %s", item.get("id"), exc)
        await self._activity(
            organization_id=org,
            entity_type="tracking",
            entity_id=dest,
            action="waiting_provider_reactivated",
            summary=f"Активировано WAITING_PROVIDER {dest}: {len(activated)}",
            role=role,
            payload={"provider": dest, "activated": len(activated), "skipped": len(skipped), "errors": len(errors), "ids": activated},
        )
        return {
            "ok": True,
            "provider": dest,
            "activated": len(activated),
            "skipped": len(skipped),
            "errors": len(errors),
            "ids": activated,
            "deleted": 0,
        }

    async def ingest_provider_lead(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        org = _org(organization_id, body.get("tenant_id"))
        await self.ensure_hydrated(org)
        from services.recruiting_ops.lead_ingest import find_provider_duplicate, merge_duplicate, normalize_provider_lead

        incoming = normalize_provider_lead(body)
        if not incoming.get("name"):
            return {"ok": False, "error": "validation", "message_ru": "Укажите имя лида"}
        existing = find_provider_duplicate(self._bag(org)["lead"], incoming)
        if existing:
            patch = merge_duplicate(existing, incoming)
            patch["updated_at"] = _now()
            existing.update(patch)
            persisted = await self._persist_patch(org, str(existing["id"]), patch)
            if persisted:
                existing = persisted
                self._replace(org, "lead", existing)
            await self._activity(
                organization_id=org,
                entity_type="lead",
                entity_id=str(existing["id"]),
                action="provider_lead_duplicate",
                summary=f"Повторный лид {incoming.get('provider')}: {existing.get('name')}",
                role=role,
                payload={"provider": incoming.get("provider"), "external_id": incoming.get("external_id"), "history_preserved": True},
            )
            return self._ok(item=existing, duplicate=True)
        created = await self.create_lead(org, {**body, **incoming}, role)
        return created

    async def create_automation_rule(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.recruiting_ops.automation import normalize_rule

        parsed = normalize_rule(body)
        if not parsed.get("ok"):
            return parsed
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = {
            "id": str(body.get("id") or uuid.uuid4()),
            "organization_id": org,
            "created_at": _now(),
            "updated_at": _now(),
            **parsed["item"],
        }
        saved = await self._persist("automation_rule", item)
        self._bag(org)["automation_rule"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="automation_rule",
            entity_id=str(saved["id"]),
            action="automation_rule_created",
            summary=f"Правило автоматизации: {saved.get('name')}",
            role=role,
            payload={"rule_type": saved.get("rule_type"), "approval_required": saved.get("approval_required")},
        )
        return self._ok(item=saved)

    async def run_automation_rule(self, organization_id: str, rule_id: str, body: dict[str, Any] | None = None, role: str | None = None) -> dict[str, Any]:
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        rule = self._find(org, "automation_rule", rule_id)
        if not rule:
            return {"ok": False, "error": "not_found", "message_ru": "Правило не найдено"}
        from services.recruiting_ops.automation import evaluate_rule

        metrics = (body or {}).get("metrics") if isinstance((body or {}).get("metrics"), dict) else (body or {})
        health = (body or {}).get("provider_health") if isinstance(body, dict) else None
        evaluation = evaluate_rule(rule, metrics=metrics, provider_health=health)
        run = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "rule_id": rule_id,
            "rule_type": rule.get("rule_type"),
            "reason": evaluation["reason"],
            "input_metrics": evaluation["input_metrics"],
            "result": evaluation["result"],
            "approval_required": evaluation["approval_required"],
            "auto_applied": False,
            "created_at": _now(),
        }
        saved = await self._persist("automation_run", run)
        self._bag(org)["automation_run"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="automation_run",
            entity_id=str(saved["id"]),
            action="automation_evaluated",
            summary=f"Автоматизация: {evaluation['result']}",
            role=role,
            payload={"rule_id": rule_id, "result": evaluation["result"], "reason": evaluation["reason"]},
        )
        return self._ok(item=saved, evaluation=evaluation)

    async def create_ai_recommendation(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        from services.recruiting_ops.ai_optimization import build_recommendation
        from services.recruiting_ops.provider_metrics import aggregate_live_metrics

        org = _org(organization_id)
        await self.ensure_hydrated(org)
        live_rows = [item for item in self._bag(org).get("ads_metrics") or [] if item.get("source") == "LIVE"]
        agg = aggregate_live_metrics(live_rows)
        metrics = body.get("metrics") if isinstance(body.get("metrics"), dict) else {}
        metrics = {
            "leads": len(self._bag(org).get("lead") or []),
            "qualified": len([item for item in self._bag(org).get("lead") or [] if _txt(item.get("status")).lower() in {"qualified", "converted"}]),
            "interviews": len([item for item in self._bag(org).get("candidate") or [] if _txt(item.get("pipeline_stage")).upper() == "INTERVIEW"]),
            "hires": len([item for item in self._bag(org).get("candidate") or [] if _txt(item.get("pipeline_stage")).upper() == "HIRED"]),
            "spend": agg.get("spend"),
            "impressions": agg.get("impressions"),
            "clicks": agg.get("clicks"),
            **metrics,
        }
        parsed = build_recommendation(body, metrics=metrics)
        if not parsed.get("ok"):
            return parsed
        item = {
            "id": str(body.get("id") or uuid.uuid4()),
            "organization_id": org,
            "created_at": _now(),
            "updated_at": _now(),
            "data_freshness": max((str(row.get("updated_at") or row.get("bucket") or "") for row in live_rows), default=None),
            "observation": _txt(body.get("observation") or body.get("reason")) or "Анализ внутренних метрик воронки и доступных live-данных.",
            **parsed["item"],
        }
        saved = await self._persist("ai_recommendation", item)
        self._bag(org)["ai_recommendation"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="ai_recommendation",
            entity_id=str(saved["id"]),
            action="ai_recommendation_created",
            summary=f"AI рекомендация: {saved.get('recommendation')}",
            role=role,
            payload={"recommendation": saved.get("recommendation"), "advisory_only": True, "live_write_access": False},
        )
        return self._ok(item=saved)

    async def decide_ai_recommendation(self, organization_id: str, rec_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "ai_recommendation", rec_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Рекомендация не найдена"}
        from services.recruiting_ops.ai_optimization import apply_human_decision

        parsed = apply_human_decision(item, str(body.get("decision") or body.get("status") or ""))
        if not parsed.get("ok"):
            return parsed
        patch = parsed["item"]
        patch["updated_at"] = _now()
        item.update(patch)
        persisted = await self._persist_patch(org, rec_id, patch)
        saved = persisted or item
        self._replace(org, "ai_recommendation", saved)
        await self._activity(
            organization_id=org,
            entity_type="ai_recommendation",
            entity_id=rec_id,
            action="ai_recommendation_decided",
            summary=f"AI рекомендация: {saved.get('status')}",
            role=role,
            payload={"status": saved.get("status"), "live_applied": False},
        )
        return self._ok(item=saved)

    async def oauth_start(self, organization_id: str, provider: str, role: str | None = None) -> dict[str, Any]:
        denied = require_provider_admin(role, provider, "oauth")
        if denied:
            return denied
        from services.recruiting_ops.provider_oauth import authorize_url

        result = authorize_url(provider, _org(organization_id))
        if result.get("ok"):
            await self._activity(
                organization_id=_org(organization_id),
                entity_type="provider_connection",
                entity_id=provider,
                action="oauth_started",
                summary=f"OAuth {provider}: старт",
                role=role,
                payload={"provider": provider, "redirect_uri": result.get("redirect_uri")},
            )
        return result

    async def oauth_callback(self, provider: str, *, state: str, code: str | None, error: str | None = None) -> dict[str, Any]:
        from services.recruiting_ops.provider_connections import default_connection, public_card
        from services.recruiting_ops.provider_oauth import consume_oauth_nonce, decode_state, exchange_code
        from services.recruiting_ops.secret_store import get_secret_store, public_secret_audit

        parsed = decode_state(state)
        if not parsed.get("ok"):
            return parsed
        if _txt(parsed.get("provider")) != _txt(provider).lower():
            return {"ok": False, "error": "AUTH_ERROR", "message_ru": "OAuth state не совпадает с провайдером."}
        if not consume_oauth_nonce(str(parsed.get("nonce") or "")):
            return {"ok": False, "error": "AUTH_ERROR", "message_ru": "OAuth callback уже использован."}
        if error or not _txt(code):
            return {"ok": False, "error": "AUTH_ERROR", "status": "API_ERROR", "message_ru": "Провайдер не выдал код авторизации."}
        org = _org(parsed.get("organization_id"))
        await self.ensure_hydrated(org)
        exchanged = exchange_code(provider, str(code))
        if not exchanged.get("ok"):
            return exchanged
        key = _txt(provider).lower()
        store = get_secret_store()
        expires_at = None
        if exchanged.get("expires_in"):
            try:
                expires_at = datetime.fromtimestamp(time.time() + float(exchanged["expires_in"]), tz=timezone.utc).isoformat()
            except (TypeError, ValueError, OSError):
                expires_at = None
        scopes = list(exchanged.get("scopes") or [])
        if exchanged.get("access_token"):
            store.put(key, "access_token", str(exchanged["access_token"]), expires_at=expires_at, scopes=scopes, organization_id=org)
        if exchanged.get("refresh_token"):
            store.put(key, "refresh_token", str(exchanged["refresh_token"]), expires_at=expires_at, scopes=scopes, organization_id=org)
        await self._activity(
            organization_id=org,
            entity_type="provider_connection",
            entity_id=provider,
            action="oauth_token_stored",
            summary=f"OAuth {provider}: токен сохранён",
            role="system",
            payload=public_secret_audit("put", key, "access_token"),
        )
        existing = next((item for item in self._connections(org) if _txt(item.get("provider")) == key), None)
        row = existing or default_connection(key)
        row.update(
            {
                "organization_id": org,
                "tenant_id": org,
                "status": "AUTHORIZING",
                "connected": False,
                "live_verified": False,
                "enabled": True,
                "sync_enabled": False,
                "scopes": scopes,
                "token_expires_at": expires_at,
                "credential_version": int(row.get("credential_version") or 0) + 1,
                "last_error": None,
                "updated_at": _now(),
            }
        )
        if not existing:
            row["id"] = str(uuid.uuid4())
            row["created_at"] = _now()
            saved = await self._persist("provider_connection", row)
            self._bag(org)["provider_connection"].insert(0, saved)
        else:
            persisted = await self._persist_patch(org, str(row["id"]), row)
            saved = persisted or row
            self._replace(org, "provider_connection", saved)
        accounts = await self.list_provider_accounts(org, key, role="platform_owner")
        card = public_card(saved)
        leaked = str(exchanged.get("access_token") or "")
        safe = self._ok(
            item=card,
            accounts=accounts.get("items") or [],
            status="AUTHORIZING",
            connected=False,
            live_verified=False,
            mocked=bool(exchanged.get("live") is False),
            message_ru="Авторизация получена. Выберите рекламный аккаунт и выполните живую проверку.",
        )
        if leaked and leaked in str(safe):
            safe = {k: v for k, v in safe.items() if k != "adapter"}
        return safe

    async def test_provider_connection(self, organization_id: str, provider: str, role: str | None = None) -> dict[str, Any]:
        result = await self.provider_action(organization_id, provider, "test", {"mode": "LIVE"}, role=role)
        item = result.get("item") if isinstance(result.get("item"), dict) else {}
        adapter = result.get("adapter") if isinstance(result.get("adapter"), dict) else {}
        identity = item.get("identity") or adapter.get("identity") or {}
        safe = {
            "provider": _txt(provider).lower(),
            "status": item.get("status") or adapter.get("status"),
            "account_identity": {k: identity.get(k) for k in ("id", "name", "username", "phone", "account_id") if identity.get(k)},
            "latency": item.get("latency_ms") or adapter.get("latency_ms"),
            "permissions": item.get("scopes") or item.get("permissions") or [],
            "checked_at": item.get("last_successful_health_check") or _now(),
            "error_code": adapter.get("error_code") or adapter.get("error"),
            "safe_error_message": adapter.get("message_ru"),
            "mocked_http": bool(adapter.get("mocked_http") or item.get("mocked_http")),
            "live_verified": bool(adapter.get("live_verified") or item.get("live_verified")),
        }
        if result.get("ok") is False and not adapter:
            return result
        if _txt(provider).lower() == "whatsapp":
            from services.recruiting_ops.secret_store import get_secret_store

            pnid = _txt(get_secret_store().get("whatsapp", "phone_number_id") or os.getenv("WHATSAPP_PHONE_NUMBER_ID"))
            if pnid:
                await self._persist_whatsapp_phone_map(_org(organization_id), pnid)
        return self._ok(**safe)

    async def list_provider_accounts(self, organization_id: str, provider: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        from services.recruiting_ops.provider_adapters import get_adapter

        listed = get_adapter(provider, mode="LIVE").invoke("list_accounts", organization_id=org)
        items = [item for item in (listed.get("items") or []) if isinstance(item, dict)]
        if not listed.get("ok"):
            return {
                "ok": False,
                "error": listed.get("error") or "NOT_CONFIGURED",
                "items": [],
                "fake_data": False,
                "mocked": bool(listed.get("mocked_http")),
                "message_ru": listed.get("message_ru") or "Аккаунты недоступны.",
            }
        return self._ok(
            items=items,
            provider=_txt(provider).lower(),
            mocked=bool(listed.get("mocked_http")),
            live_verified=bool(listed.get("live_verified")),
            developer_token_available=listed.get("developer_token_available"),
            message_ru=listed.get("message_ru"),
        )

    async def select_provider_account(self, organization_id: str, provider: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require_provider_admin(role, provider, "select_account")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        key = _txt(provider).lower()
        account_id = _txt(body.get("account_id") or body.get("customer_id") or body.get("advertiser_id") or body.get("ad_account_id"))
        if not account_id:
            return {"ok": False, "error": "validation", "message_ru": "Укажите рекламный аккаунт."}
        from services.recruiting_ops.provider_adapters import get_adapter
        from services.recruiting_ops.provider_connections import default_connection, public_card
        from services.recruiting_ops.secret_store import get_secret_store

        store = get_secret_store()
        if key == "meta":
            store.put(key, "ad_account_id", account_id, organization_id=org)
        elif key == "google":
            store.put(key, "customer_id", account_id.replace("-", ""), organization_id=org)
            login = _txt(body.get("login_customer_id") or body.get("manager_id"))
            if login:
                store.put(key, "manager_id", login.replace("-", ""), organization_id=org)
        elif key == "tiktok":
            store.put(key, "advertiser_id", account_id, organization_id=org)
        existing = next((item for item in self._connections(org) if _txt(item.get("provider")) == key), None)
        row = existing or default_connection(key)
        verify = get_adapter(key, mode="LIVE").invoke("verify_connection", organization_id=org)
        live_ok = bool(verify.get("ok") and (verify.get("live_verified") or verify.get("mocked_http")))
        identity = verify.get("identity") if isinstance(verify.get("identity"), dict) else {}
        row.update(
            {
                "organization_id": org,
                "tenant_id": org,
                "account_id": account_id,
                "connected_account_id": account_id,
                "connected_account_name": identity.get("name") or identity.get("account_name") or body.get("account_name"),
                "currency": identity.get("currency") or body.get("currency"),
                "timezone": identity.get("timezone") or identity.get("timezone_name") or body.get("timezone"),
                "login_customer_id": _txt(body.get("login_customer_id") or body.get("manager_id")) or None,
                "status": "CONNECTED" if live_ok else "AUTHORIZING",
                "connected": live_ok,
                "live_verified": bool(verify.get("live_verified")),
                "mocked_http": bool(verify.get("mocked_http")),
                "identity": identity or row.get("identity") or {},
                "last_health_check_at": _now(),
                "last_error": None if live_ok else (verify.get("error") or verify.get("message_ru")),
                "updated_at": _now(),
            }
        )
        if live_ok:
            row["connected_at"] = row.get("connected_at") or _now()
            row["last_successful_request_at"] = _now()
        if not existing:
            row["id"] = str(uuid.uuid4())
            row["created_at"] = _now()
            saved = await self._persist("provider_connection", row)
            self._bag(org)["provider_connection"].insert(0, saved)
        else:
            persisted = await self._persist_patch(org, str(row["id"]), row)
            saved = persisted or row
            self._replace(org, "provider_connection", saved)
        self._sync_runtime_connections(org)
        await self._activity(
            organization_id=org,
            entity_type="provider_connection",
            entity_id=str(saved.get("id")),
            action="provider_account_selected",
            summary=f"Провайдер {key}: выбран аккаунт",
            role=role,
            payload={"provider": key, "account_id": account_id, "status": saved.get("status"), "secret": None},
        )
        return self._ok(item=public_card(saved), adapter=verify, mocked=bool(verify.get("mocked_http")))

    async def set_provider_sync(self, organization_id: str, provider: str, *, enabled: bool, role: str | None = None) -> dict[str, Any]:
        denied = require_provider_admin(role, provider, "enable_sync")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        from services.recruiting_ops.provider_connections import public_card

        row = next((item for item in self._connections(org) if _txt(item.get("provider")) == _txt(provider).lower()), None)
        if not row:
            return {"ok": False, "error": "NOT_CONFIGURED", "message_ru": "Провайдер не настроен."}
        if enabled and not (str(row.get("status") or "").upper() == "CONNECTED" and (row.get("live_verified") or row.get("mocked_http"))):
            return {"ok": False, "error": "NOT_CONFIGURED", "status": "AUTHORIZING", "message_ru": "Синхронизация включается только после живой проверки."}
        row["sync_enabled"] = bool(enabled)
        row["updated_at"] = _now()
        persisted = await self._persist_patch(org, str(row["id"]), row)
        saved = persisted or row
        self._replace(org, "provider_connection", saved)
        return self._ok(item=public_card(saved))

    async def provider_diagnostics(self, organization_id: str, provider: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        from services.recruiting_ops.provider_layer import app_prerequisites, safe_diagnostics
        from services.recruiting_ops.secret_store import credential_presence

        key = _txt(provider).lower()
        row = next((item for item in self._connections(org) if _txt(item.get("provider")) == key), None) or {"provider": key, "status": "NOT_CONFIGURED"}
        diag = safe_diagnostics(row, app=app_prerequisites(key), creds=credential_presence(key, organization_id=org))
        return self._ok(diagnostics=True, **diag)

    async def confirm_provider_mapping(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require_provider_admin(role, _txt(body.get("provider")), "configure")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        external_id = _txt(body.get("external_campaign_id"))
        internal_id = _txt(body.get("internal_campaign_id"))
        if not external_id or not internal_id:
            return {"ok": False, "error": "validation", "message_ru": "Нужны external_campaign_id и internal_campaign_id."}
        existing = [
            item
            for item in self._bag(org).get("provider_mapping") or []
            if _txt(item.get("external_campaign_id")) == external_id and _txt(item.get("provider")) == _txt(body.get("provider")).lower()
        ]
        if any(_txt(item.get("internal_campaign_id")) not in {"", internal_id} and item.get("state") == "MAPPED" for item in existing):
            return {"ok": False, "error": "CONFLICT", "state": "CONFLICT", "message_ru": "Кампания уже сопоставлена с другой внутренней. Автослияние запрещено."}
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "provider": _txt(body.get("provider")).lower(),
            "external_campaign_id": external_id,
            "internal_campaign_id": internal_id,
            "state": "MAPPED",
            "quality": "MANUAL",
            "confirmed_by": normalize_role(role),
            "created_at": _now(),
        }
        saved = await self._persist("provider_mapping", item)
        self._bag(org).setdefault("provider_mapping", []).insert(0, saved)
        return self._ok(item=saved)

    async def sync_provider_metrics(self, organization_id: str, provider: str, role: str | None = None) -> dict[str, Any]:
        denied = require_provider_admin(role, provider, "sync")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        from services.recruiting_ops.provider_adapters import get_adapter
        from services.recruiting_ops.provider_layer import refuse_sync
        from services.recruiting_ops.provider_metrics import normalize_metric_row, upsert_metrics

        key = _txt(provider).lower()
        row = next((item for item in self._connections(org) if _txt(item.get("provider")) == key), None) or {}
        blocked = refuse_sync(
            key,
            configured=bool(row.get("status") not in {None, "", "NOT_CONFIGURED"}),
            connected=str(row.get("status") or "").upper() == "CONNECTED" and bool(row.get("live_verified") or row.get("mocked_http")),
            account_selected=bool(row.get("account_id") or (row.get("identity") or {}).get("id")),
        )
        if blocked:
            run = {
                "id": str(uuid.uuid4()),
                "organization_id": org,
                "provider": key,
                "status": blocked["status"],
                "ok": False,
                "fake_data": False,
                "created_at": _now(),
            }
            await self._persist("provider_sync_run", run)
            self._bag(org).setdefault("provider_sync_run", []).insert(0, run)
            return blocked
        fetched = get_adapter(provider, mode="LIVE").invoke("fetch_metrics", organization_id=org)
        if not fetched.get("ok"):
            return fetched
        incoming = [
            normalize_metric_row(provider, row if isinstance(row, dict) else {}, account=str((fetched.get("identity") or {}).get("id") or ""))
            for row in fetched.get("items") or []
        ]
        existing = list(self._bag(org).get("ads_metrics") or [])
        self._bag(org)["ads_metrics"] = upsert_metrics(existing, incoming)
        for row in incoming:
            saved = await self._persist("ads_metrics", {**row, "id": str(uuid.uuid4()), "organization_id": org})
            self._bag(org)["ads_metrics"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="ads_metrics",
            entity_id=provider,
            action="metrics_synced",
            summary=f"Метрики {provider}: {len(incoming)}",
            role=role,
            payload={"provider": provider, "count": len(incoming), "mocked_http": fetched.get("mocked_http")},
        )
        if row:
            row["last_sync_at"] = _now()
            row["sync_cursor"] = fetched.get("cursor")
            persisted = await self._persist_patch(org, str(row["id"]), row)
            if persisted:
                self._replace(org, "provider_connection", persisted)
        run = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "provider": key,
            "status": "OK",
            "count": len(incoming),
            "mocked_http": bool(fetched.get("mocked_http")),
            "live_verified": bool(fetched.get("live_verified")),
            "created_at": _now(),
        }
        await self._persist("provider_sync_run", run)
        self._bag(org).setdefault("provider_sync_run", []).insert(0, run)
        return self._ok(items=incoming, cursor=fetched.get("cursor"), mocked_http=fetched.get("mocked_http"), live_verified=fetched.get("live_verified"), mocked=bool(fetched.get("mocked_http")))

    async def sync_provider_campaigns(self, organization_id: str, provider: str, role: str | None = None) -> dict[str, Any]:
        denied = require_provider_admin(role, provider, "sync")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        from services.recruiting_ops.provider_adapters import get_adapter
        from services.recruiting_ops.campaign_model import normalize_campaign
        from services.recruiting_ops.provider_layer import refuse_sync, suggest_campaign_mapping

        key = _txt(provider).lower()
        row = next((item for item in self._connections(org) if _txt(item.get("provider")) == key), None) or {}
        blocked = refuse_sync(
            key,
            configured=bool(row.get("status") not in {None, "", "NOT_CONFIGURED"}),
            connected=str(row.get("status") or "").upper() == "CONNECTED" and bool(row.get("live_verified") or row.get("mocked_http")),
            account_selected=bool(row.get("account_id")),
        )
        if blocked:
            return blocked
        listed = get_adapter(provider, mode="LIVE").invoke("list_campaigns", organization_id=org)
        if not listed.get("ok"):
            return listed
        synced = []
        for raw in listed.get("items") or []:
            if not isinstance(raw, dict):
                continue
            external_id = str(raw.get("id") or raw.get("campaign_id") or "")
            existing = next(
                (
                    item
                    for item in self._bag(org).get("campaign") or []
                    if str(item.get("external_id")) == external_id and _txt(item.get("provider")) == _txt(provider)
                ),
                None,
            )
            domain = normalize_campaign(
                {
                    "provider": provider,
                    "external_id": external_id,
                    "name": raw.get("name"),
                    "status": raw.get("status"),
                    "budget": raw.get("budget") or raw.get("daily_budget"),
                    "start_at": raw.get("start_time") or raw.get("start_at"),
                    "end_at": raw.get("stop_time") or raw.get("end_at"),
                },
                existing=existing,
            )
            domain["lifecycle_status"] = domain.get("status")
            domain["provider_status"] = raw.get("status")
            domain["sync_state"] = "SYNCED"
            domain["last_synced_at"] = _now()
            if existing:
                history = list(existing.get("audit_history") or [])
                domain.pop("status", None)
                existing.update({k: v for k, v in domain.items() if k != "audit_history"})
                existing["audit_history"] = history
                persisted = await self._persist_patch(org, str(existing["id"]), existing)
                saved = persisted or existing
                self._replace(org, "campaign", saved)
            else:
                item = {"id": str(uuid.uuid4()), "organization_id": org, "status": "active", "created_at": _now(), **domain}
                saved = await self._persist("campaign", item)
                self._bag(org)["campaign"].insert(0, saved)
            synced.append(saved)
            internals = [item for item in self._bag(org).get("campaign") or [] if item.get("origin") == "INTERNAL"]
            suggestion = suggest_campaign_mapping(raw if isinstance(raw, dict) else {}, internals)
            if suggestion.get("state") in {"SUGGESTED", "CONFLICT", "UNMAPPED"}:
                mapping = {
                    "id": str(uuid.uuid4()),
                    "organization_id": org,
                    "provider": key,
                    "external_campaign_id": external_id,
                    "internal_campaign_id": suggestion.get("internal_campaign_id"),
                    "state": suggestion.get("state"),
                    "quality": suggestion.get("quality"),
                    "ambiguous": bool(suggestion.get("ambiguous")),
                    "created_at": _now(),
                }
                await self._persist("provider_mapping", mapping)
                self._bag(org).setdefault("provider_mapping", []).insert(0, mapping)
        return self._ok(items=synced, mocked_http=listed.get("mocked_http"), mocked=bool(listed.get("mocked_http")))

    async def propose_campaign_write(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        from services.recruiting_ops.campaign_writes import propose_write

        parsed = propose_write(body)
        if not parsed.get("ok"):
            return parsed
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = {"id": str(uuid.uuid4()), "organization_id": org, **parsed["item"]}
        saved = await self._persist("campaign_write", item)
        self._bag(org)["campaign_write"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="campaign_write",
            entity_id=str(saved["id"]),
            action="campaign_write_proposed",
            summary=f"Live-изменение {saved.get('action')} ожидает согласования",
            role=role,
            payload={"action": saved.get("action"), "provider": saved.get("provider"), "approval_required": True},
        )
        return self._ok(item=saved)

    async def decide_campaign_write(self, organization_id: str, write_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "campaign_write", write_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Нет заявки на изменение кампании"}
        from services.recruiting_ops.campaign_writes import apply_approved_write

        parsed = apply_approved_write(item, decision=str(body.get("decision") or ""))
        if parsed.get("error") == "validation":
            return parsed
        patch = parsed["item"]
        patch["updated_at"] = _now()
        item.update(patch)
        persisted = await self._persist_patch(org, write_id, patch)
        saved = persisted or item
        self._replace(org, "campaign_write", saved)
        await self._activity(
            organization_id=org,
            entity_type="campaign_write",
            entity_id=write_id,
            action="campaign_write_decided",
            summary=f"Live-изменение: {saved.get('status')}",
            role=role,
            payload={"status": saved.get("status"), "live_applied": saved.get("live_applied")},
        )
        return self._ok(item=saved, adapter=parsed.get("adapter"))

    async def list_email_templates(self, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.recruiting_ops.email_smtp import TEMPLATES

        return self._ok(items=list(TEMPLATES.values()))

    async def preview_candidate_email(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.recruiting_ops.email_smtp import render_template

        context = body.get("context") if isinstance(body.get("context"), dict) else {}
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        candidate_id = _txt(body.get("candidate_id"))
        if candidate_id:
            cand = self._find(org, "candidate", candidate_id) or {}
            context = {
                "name": _txt(cand.get("name") or context.get("name")),
                "first_name": _txt((cand.get("name") or "").split(" ")[0] or context.get("first_name")),
                "vacancy": _txt(context.get("vacancy") or cand.get("vacancy") or ""),
                "company": _txt(context.get("company") or ""),
                "link": _txt(context.get("link") or ""),
                **{k: _txt(v) for k, v in context.items()},
            }
        rendered = render_template(_txt(body.get("template_id") or "intro"), context)
        return self._ok(**rendered)

    async def test_smtp_email(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        from services.recruiting_ops.email_smtp import send_smtp_message
        from services.recruiting_ops.provider_live import _SMTP_FACTORY, smtp_settings
        from services.recruiting_ops.secret_store import public_secret_audit

        to = _txt(body.get("to") or body.get("email"))
        result = send_smtp_message(
            to=to,
            subject=_txt(body.get("subject") or "Проверка SMTP Recruiting"),
            body=_txt(body.get("body") or "Это проверка SMTP. Автоматическая рассылка не выполнялась."),
            cfg=smtp_settings(),
            factory=_SMTP_FACTORY,
        )
        await self._activity(
            organization_id=org,
            entity_type="provider_connection",
            entity_id="email",
            action="email_test_send",
            summary="Тестовое письмо SMTP",
            role=role,
            payload={**public_secret_audit("test_email", "email", "smtp_password"), "status": result.get("status"), "sent": result.get("sent"), "delivered": False},
        )
        return {
            "ok": bool(result.get("ok")),
            "status": result.get("status"),
            "sent": bool(result.get("sent")),
            "delivered": False,
            "error": result.get("error"),
            "message_ru": result.get("message_ru"),
            "retryable": result.get("retryable"),
        }

    async def list_candidate_emails(self, organization_id: str, candidate_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        items = [
            item
            for item in self._bag(org).get("communication") or []
            if _txt(item.get("candidate_id")) == _txt(candidate_id) and _txt(item.get("channel")).upper() == "EMAIL"
        ]
        return self._ok(items=items)

    async def add_email_suppression(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        from services.recruiting_ops.email_smtp import valid_recipient

        email = _txt(body.get("email") or body.get("to")).lower()
        if not valid_recipient(email):
            return {"ok": False, "error": "validation", "message_ru": "Некорректный адрес для suppression."}
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "email": email,
            "reason": _txt(body.get("reason") or "manual"),
            "created_at": _now(),
        }
        saved = await self._persist("email_suppression", item)
        self._bag(org)["email_suppression"].insert(0, saved)
        return self._ok(item=saved)

    def _email_suppressed(self, org: str, address: str) -> bool:
        needle = _txt(address).lower()
        return any(_txt(item.get("email")).lower() == needle for item in self._bag(org).get("email_suppression") or [])

    async def send_candidate_email(self, organization_id: str, candidate_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        from services.observability import inc_metric
        from services.recruiting_ops.email_smtp import idempotency_key, render_template, send_smtp_message, valid_recipient
        from services.recruiting_ops.provider_errors import RATE_LIMITED
        from services.recruiting_ops.provider_live import _SMTP_FACTORY, smtp_settings
        from services.recruiting_ops.public_limits import check_rate_limit
        from services.recruiting_ops.secret_store import public_secret_audit

        cand = self._find(org, "candidate", candidate_id)
        if not cand:
            return {"ok": False, "error": "not_found", "message_ru": "Кандидат не найден"}
        to = _txt(body.get("to") or body.get("email") or cand.get("email"))
        if not valid_recipient(to):
            return {"ok": False, "error": "validation", "message_ru": "Некорректный получатель."}
        if self._email_suppressed(org, to):
            return {"ok": False, "error": "suppressed", "message_ru": "Адрес в списке suppression. Письмо не отправлено."}
        if _txt(body.get("campaign_id")) and not body.get("approved"):
            return {"ok": False, "error": "APPROVAL_REQUIRED", "message_ru": "Рассылка кампании требует согласования."}
        try:
            limit = max(1, int(os.getenv("EMAIL_SEND_RATE_LIMIT") or "20"))
        except ValueError:
            limit = 20
        rl = check_rate_limit(key=f"email-send:{org}", limit=limit)
        if not rl.get("allowed"):
            inc_metric("email_rate_limited_total")
            return {"ok": False, "error": RATE_LIMITED, "message_ru": "Превышен лимит отправки email.", "retry_after_seconds": rl.get("retry_after_seconds")}
        context = body.get("context") if isinstance(body.get("context"), dict) else {}
        rendered = render_template(
            _txt(body.get("template_id") or "intro"),
            {
                "name": _txt(cand.get("name") or context.get("name")),
                "first_name": _txt((cand.get("name") or "").split(" ")[0] or context.get("first_name")),
                "vacancy": _txt(context.get("vacancy") or cand.get("vacancy") or ""),
                "company": _txt(context.get("company") or ""),
                "link": _txt(context.get("link") or ""),
            },
        )
        subject = _txt(body.get("subject") or rendered.get("subject"))
        text = _txt(body.get("body") or rendered.get("body"))
        key = idempotency_key(organization_id=org, to=to, subject=subject, body=text, candidate_id=candidate_id)
        for row in self._bag(org)["idempotency"]:
            if _txt(row.get("key")) == key:
                existing = self._find(org, "communication", _txt(row.get("communication_id")))
                if existing and existing.get("status") == "SENT":
                    return self._ok(item=existing, duplicate=True, message_ru="Повторная отправка предотвращена.")
        result = send_smtp_message(to=to, subject=subject, body=text, cfg=smtp_settings(), factory=_SMTP_FACTORY)
        status = "SENT" if result.get("ok") else "FAILED"
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "channel": "EMAIL",
            "body": text,
            "subject": subject,
            "to": to,
            "candidate_id": candidate_id,
            "campaign_id": _txt(body.get("campaign_id")) or None,
            "template_id": rendered.get("template_id"),
            "sent": bool(result.get("ok")),
            "delivered": False,
            "delivery": result.get("delivery") or ("accepted" if result.get("ok") else "failed"),
            "status": status,
            "journal_only": not bool(result.get("ok")),
            "data_mode": "REAL",
            "created_at": _now(),
            "updated_at": _now(),
            "last_error": None if result.get("ok") else (result.get("error") or result.get("message_ru")),
        }
        saved = await self._persist("communication", item)
        self._bag(org)["communication"].insert(0, saved)
        if result.get("ok"):
            await self._store_idempotency_email(org, key, saved)
        await self._activity(
            organization_id=org,
            entity_type="candidate",
            entity_id=candidate_id,
            action="email_sent" if result.get("ok") else "email_failed",
            summary=f"Email {status}: {to}",
            role=role,
            payload={**public_secret_audit("send", "email", "smtp_password"), "status": status, "delivered": False, "to": to},
        )
        out = self._ok(item=saved, adapter={"ok": result.get("ok"), "error": result.get("error"), "message_ru": result.get("message_ru"), "retryable": result.get("retryable"), "delivered": False})
        if not result.get("ok"):
            out["ok"] = False
            out["error"] = result.get("error")
            out["message_ru"] = result.get("message_ru")
        return out

    async def _store_idempotency_email(self, org: str, key: str, communication: dict[str, Any]) -> None:
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "key": key,
            "communication_id": communication.get("id"),
            "kind": "email",
            "created_at": _now(),
        }
        saved = await self._persist("idempotency", item)
        self._bag(org)["idempotency"].insert(0, saved)

    async def create_outbound_message(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        from services.recruiting_ops.messaging_lifecycle import normalize_outbound
        from services.recruiting_ops.provider_connections import is_runtime_connected

        channel = _txt(body.get("channel") or body.get("provider")).lower()
        parsed = normalize_outbound(body, connected=is_runtime_connected(channel))
        if not parsed.get("ok"):
            return parsed
        item = {"id": str(uuid.uuid4()), "organization_id": org, **parsed["item"], "candidate_id": _txt(body.get("candidate_id")) or None}
        saved = await self._persist("outbound_message", item)
        self._bag(org)["outbound_message"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="outbound_message",
            entity_id=str(saved["id"]),
            action="message_created",
            summary=f"Сообщение {saved.get('channel')}: {saved.get('status')}",
            role=role,
            payload={"channel": saved.get("channel"), "status": saved.get("status")},
        )
        return self._ok(item=saved)

    async def decide_outbound_message(self, organization_id: str, message_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "outbound_message", message_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Сообщение не найдено"}
        decision = _txt(body.get("decision")).upper()
        if decision in {"REJECT", "REJECTED"}:
            item.update({"status": "FAILED", "updated_at": _now()})
            await self._persist_patch(org, message_id, item)
            self._replace(org, "outbound_message", item)
            return self._ok(item=item)
        if decision not in {"APPROVE", "APPROVED"}:
            return {"ok": False, "error": "validation", "message_ru": "Нужно Approve или Reject."}
        from services.observability import inc_metric
        from services.recruiting_ops.provider_adapters import get_adapter
        from services.recruiting_ops.messaging_lifecycle import WAITING_PROVIDER, SENDING, SENT, FAILED
        from services.recruiting_ops.provider_errors import RATE_LIMITED
        from services.recruiting_ops.public_limits import check_rate_limit

        if item.get("status") == WAITING_PROVIDER:
            return self._ok(item=item, message_ru="Провайдер не подключен.")
        channel = _txt(item.get("channel")).lower()
        if channel == "whatsapp":
            try:
                limit = max(1, int(os.getenv("WHATSAPP_SEND_RATE_LIMIT") or "20"))
            except ValueError:
                limit = 20
            rl = check_rate_limit(key=f"whatsapp-send:{org}", limit=limit)
            if not rl.get("allowed"):
                inc_metric("whatsapp_rate_limited_total")
                return {"ok": False, "error": RATE_LIMITED, "message_ru": "Превышен лимит WhatsApp.", "retry_after_seconds": rl.get("retry_after_seconds")}
        item["status"] = SENDING
        sent = get_adapter(str(item.get("channel")), mode="LIVE").invoke(
            "send_message",
            approved=True,
            to=item.get("to"),
            text=item.get("body"),
            body=item.get("body"),
            subject=item.get("subject") or "Сообщение",
            template=item.get("template") if isinstance(item.get("template"), dict) else None,
            template_name=item.get("template_name"),
            language=item.get("language"),
            components=item.get("components") if isinstance(item.get("components"), list) else None,
            parameters=item.get("parameters") if isinstance(item.get("parameters"), list) else None,
        )
        item.update(
            {
                "status": SENT if sent.get("ok") else FAILED,
                "sent": bool(sent.get("ok")),
                "delivered": False,
                "delivery": sent.get("delivery") or ("accepted" if sent.get("ok") else None),
                "journal_only": not bool(sent.get("ok")),
                "provider_message_id": sent.get("provider_message_id"),
                "updated_at": _now(),
            }
        )
        persisted = await self._persist_patch(org, message_id, item)
        saved = persisted or item
        self._replace(org, "outbound_message", saved)
        await self._activity(
            organization_id=org,
            entity_type="outbound_message",
            entity_id=message_id,
            action="message_sent" if saved.get("sent") else "message_failed",
            summary=f"Сообщение {saved.get('channel')}: {saved.get('status')}",
            role=role,
            payload={"status": saved.get("status"), "provider_message_id": saved.get("provider_message_id")},
        )
        if channel == "whatsapp":
            await self._record_whatsapp_message(
                org,
                {
                    "direction": "outgoing",
                    "to": saved.get("to"),
                    "body": saved.get("body"),
                    "status": saved.get("status"),
                    "send_status": saved.get("status"),
                    "sent": bool(saved.get("sent")),
                    "delivered": False,
                    "read": False,
                    "failed": saved.get("status") == FAILED,
                    "provider_message_id": saved.get("provider_message_id"),
                    "candidate_id": saved.get("candidate_id"),
                    "outbound_id": saved.get("id"),
                    "message_kind": saved.get("message_kind") or ("template" if saved.get("template_name") else "text"),
                    "template_name": saved.get("template_name"),
                },
            )
            if saved.get("sent") and saved.get("candidate_id"):
                await self._touch_candidate_whatsapp(org, str(saved["candidate_id"]), outbound_at=_now())
        return self._ok(item=saved, adapter={"ok": sent.get("ok"), "error": sent.get("error"), "message_ru": sent.get("message_ru")})

    async def _record_whatsapp_message(self, org: str, payload: dict[str, Any]) -> dict[str, Any]:
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "channel": "WHATSAPP",
            "provider": "whatsapp",
            "created_at": _now(),
            **payload,
        }
        saved = await self._persist("whatsapp_message", item)
        self._bag(org).setdefault("whatsapp_message", []).insert(0, saved)
        return saved

    async def _touch_candidate_whatsapp(
        self,
        org: str,
        candidate_id: str,
        *,
        inbound_at: str | None = None,
        outbound_at: str | None = None,
    ) -> None:
        item = self._find(org, "candidate", candidate_id)
        if not item:
            return
        patch: dict[str, Any] = {"updated_at": _now()}
        if inbound_at:
            patch["whatsapp_last_inbound_at"] = inbound_at
            patch["last_inbound_whatsapp_at"] = inbound_at
            patch["whatsapp_session_open"] = True
        if outbound_at:
            patch["whatsapp_last_outbound_at"] = outbound_at
            patch["last_outbound_whatsapp_at"] = outbound_at
        item.update(patch)
        persisted = await self._persist_patch(org, candidate_id, patch)
        if persisted:
            item = persisted
        self._replace(org, "candidate", item)

    def _whatsapp_idempotency_hit(self, org: str, key: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        if not key:
            return None, None
        for row in self._bag(org)["idempotency"]:
            if _txt(row.get("key")) != key:
                continue
            msg_id = _txt(row.get("outbound_id") or row.get("whatsapp_message_id"))
            item = self._find(org, "outbound_message", msg_id) if msg_id else None
            return row, item
        return None, None

    async def _store_whatsapp_idempotency(self, org: str, key: str, outbound: dict[str, Any]) -> None:
        if not key:
            return
        existing, _item = self._whatsapp_idempotency_hit(org, key)
        patch = {
            "key": key,
            "kind": "whatsapp_send",
            "outbound_id": outbound.get("id"),
            "status": outbound.get("status"),
            "provider_message_id": outbound.get("provider_message_id"),
            "updated_at": _now(),
        }
        if existing:
            existing.update(patch)
            persisted = await self._persist_patch(org, str(existing["id"]), patch)
            self._replace(org, "idempotency", persisted or existing)
            return
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "created_at": _now(),
            **patch,
        }
        saved = await self._persist("idempotency", item)
        self._bag(org)["idempotency"].insert(0, saved)

    def _whatsapp_event_recorded(self, org: str, provider_message_id: str) -> bool:
        pid = _txt(provider_message_id)
        if not pid:
            return False
        for kind in ("whatsapp_message", "outbound_message"):
            for item in self._bag(org).get(kind) or []:
                if _txt(item.get("provider_message_id")) == pid:
                    return True
        return False

    async def list_whatsapp_conversations(self, organization_id: str, role: str | None = None, *, candidate_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        from services.recruiting_ops.whatsapp_ops import public_conversation_item

        items = list(self._bag(org).get("whatsapp_message") or [])
        if candidate_id:
            items = [item for item in items if _txt(item.get("candidate_id")) == _txt(candidate_id)]
        return self._ok(items=[public_conversation_item(item) for item in items], provider="whatsapp")

    async def list_whatsapp_templates(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        from services.recruiting_ops.provider_live import live_list_whatsapp_templates

        return live_list_whatsapp_templates()

    async def draft_whatsapp_ai(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        from services.recruiting_ops.whatsapp_ops import ai_draft

        cand = self._find(org, "candidate", _txt(body.get("candidate_id"))) or {}
        draft = ai_draft(name=_txt(cand.get("name") or body.get("name")), vacancy=_txt(body.get("vacancy") or cand.get("vacancy")))
        await self._activity(
            organization_id=org,
            entity_type="whatsapp_message",
            entity_id=_txt(body.get("candidate_id")) or "draft",
            action="whatsapp_ai_draft",
            summary="Создан черновик WhatsApp (AI, без отправки)",
            role=role,
            payload={"sent": False, "advisory_only": True, "live_write_access": False},
        )
        return draft

    async def send_candidate_whatsapp(self, organization_id: str, candidate_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        cand = self._find(org, "candidate", candidate_id)
        if not cand:
            return {"ok": False, "error": "not_found", "message_ru": "Кандидат не найден"}
        from services.recruiting_ops.whatsapp_ops import (
            ERROR_TEMPLATE_REQUIRED,
            extract_template,
            normalize_phone,
            outbound_idempotency_key,
            session_window,
        )

        to = normalize_phone(_txt(body.get("to") or body.get("phone") or cand.get("phone")))
        text = _txt(body.get("body") or body.get("text"))
        template = extract_template(body)
        if not to or (not text and not template):
            return {"ok": False, "error": "validation", "message_ru": "Укажите телефон и текст или шаблон."}
        thread = [item for item in self._bag(org).get("whatsapp_message") or [] if _txt(item.get("candidate_id")) == candidate_id]
        window = session_window(cand, thread)
        if not template and not window.get("text_allowed"):
            return {
                "ok": False,
                "error": ERROR_TEMPLATE_REQUIRED,
                "reason": window.get("reason"),
                "template_required": True,
                "window_open": False,
                "last_inbound_at": window.get("last_inbound_at"),
                "last_outbound_at": window.get("last_outbound_at"),
                "message_ru": window.get("message_ru"),
            }
        client_key = _txt(body.get("idempotency_key") or body.get("Idempotency-Key"))
        key = outbound_idempotency_key(
            organization_id=org,
            candidate_id=candidate_id,
            to=to,
            client_key=client_key,
            body=text,
            template_name=_txt((template or {}).get("name")),
        )
        if key:
            _row, existing = self._whatsapp_idempotency_hit(org, key)
            if existing and _txt(existing.get("status")).upper() in {"SENT", "SENDING", "DELIVERED", "APPROVAL_REQUIRED"}:
                if _txt(existing.get("status")).upper() == "APPROVAL_REQUIRED" and (
                    body.get("confirm") or _txt(body.get("decision")).upper() in {"APPROVE", "APPROVED"}
                ):
                    return await self.decide_outbound_message(org, str(existing["id"]), {"decision": "APPROVE"}, role=role)
                return self._ok(
                    item=existing,
                    duplicate=True,
                    sent=bool(existing.get("sent")),
                    message_ru="Повторная отправка WhatsApp предотвращена.",
                )
            if existing and _txt(existing.get("status")).upper() == "FAILED" and (
                body.get("confirm") or _txt(body.get("decision")).upper() in {"APPROVE", "APPROVED"}
            ):
                retried = await self.decide_outbound_message(org, str(existing["id"]), {"decision": "APPROVE"}, role=role)
                if retried.get("ok") and retried.get("item"):
                    await self._store_whatsapp_idempotency(org, key, retried["item"])
                return retried
        outbound_body = {
            "channel": "whatsapp",
            "to": to,
            "body": text or (f"[template:{(template or {}).get('name')}]" if template else ""),
            "candidate_id": candidate_id,
            "template": template,
            "template_name": (template or {}).get("name"),
            "language": (template or {}).get("language"),
            "components": (template or {}).get("components"),
            "message_kind": "template" if template else "text",
            "window_open": window.get("window_open"),
            "template_required": window.get("template_required"),
        }
        created = await self.create_outbound_message(org, outbound_body, role=role)
        if not created.get("ok"):
            return created
        item = created["item"]
        if key:
            await self._store_whatsapp_idempotency(org, key, item)
        if not body.get("confirm") and _txt(body.get("decision")).upper() not in {"APPROVE", "APPROVED"}:
            return self._ok(
                item=item,
                approval_required=True,
                sent=False,
                window_open=window.get("window_open"),
                template_required=bool(template) or bool(window.get("template_required")),
                message_ru="Отправка WhatsApp требует подтверждения человеком.",
            )
        decided = await self.decide_outbound_message(org, str(item["id"]), {"decision": "APPROVE"}, role=role)
        if key and decided.get("item"):
            await self._store_whatsapp_idempotency(org, key, decided["item"])
        return decided

    async def whatsapp_webhook(
        self,
        *,
        method: str,
        query: dict[str, Any],
        body: dict[str, Any] | None = None,
        raw: bytes | None = None,
        signature: str | None = None,
    ) -> dict[str, Any]:
        from services.observability import inc_metric
        from services.recruiting_ops.secret_store import get_secret_store, public_secret_audit
        from services.recruiting_ops.whatsapp_ops import (
            ERROR_MALFORMED_WEBHOOK,
            ERROR_UNKNOWN_PHONE,
            log_webhook_event,
            mark_webhook_seen,
            match_candidate,
            parse_event_time,
            parse_webhook,
            seen_webhook,
            verify_webhook_signature,
            webhook_event_key,
        )

        store = get_secret_store()
        verify = store.get("whatsapp", "verify_token") or _txt(os.getenv("WHATSAPP_VERIFY_TOKEN"))
        if method.upper() == "GET":
            if _txt(query.get("hub.mode")) == "subscribe" and _txt(query.get("hub.verify_token")) == verify and verify:
                return {"ok": True, "challenge": query.get("hub.challenge"), "verified": True}
            await self._activity(
                organization_id=_org(os.getenv("VANGUARD_ORGANIZATION_ID") or "ados"),
                entity_type="provider_connection",
                entity_id="whatsapp",
                action="whatsapp_webhook_verify_failed",
                summary="Webhook verify не прошёл",
                payload=public_secret_audit("webhook_verify", "whatsapp", "verify_token"),
            )
            log_webhook_event("verify_failed")
            return {"ok": False, "error": "AUTH_ERROR", "message_ru": "Webhook verify не прошёл."}
        signed = verify_webhook_signature(raw, signature)
        if not signed.get("ok"):
            inc_metric("whatsapp_webhook_received_total")
            await self._activity(
                organization_id=_org(os.getenv("VANGUARD_ORGANIZATION_ID") or "ados"),
                entity_type="provider_connection",
                entity_id="whatsapp",
                action="whatsapp_webhook_verify_failed",
                summary="Подпись webhook отклонена",
                payload={"error": signed.get("error")},
            )
            log_webhook_event("signature_rejected", error=signed.get("error"))
            return signed
        inc_metric("whatsapp_webhook_received_total")
        if body is not None and not isinstance(body, dict):
            log_webhook_event("malformed", reason="body_not_object")
            return {"ok": False, "error": ERROR_MALFORMED_WEBHOOK, "message_ru": "Некорректное тело webhook."}
        parsed = parse_webhook(body)
        if parsed.get("malformed") and not parsed.get("messages") and not parsed.get("statuses"):
            log_webhook_event("malformed", reason="unreadable_payload")
            return {"ok": False, "error": ERROR_MALFORMED_WEBHOOK, "message_ru": "Некорректное тело webhook."}
        phone_number_id = _txt(parsed.get("phone_number_id"))
        has_events = bool(parsed.get("messages") or parsed.get("statuses"))
        org = await self.resolve_whatsapp_org(phone_number_id) if phone_number_id else None
        if has_events and phone_number_id and not org:
            log_webhook_event("unknown_phone_number_id", phone_number_id=phone_number_id)
            return {
                "ok": False,
                "error": ERROR_UNKNOWN_PHONE,
                "received": False,
                "ignored": True,
                "phone_number_id": phone_number_id,
                "message_ru": "Неизвестный phone_number_id. Сообщения не привязаны к организации.",
            }
        org = _org(org or os.getenv("VANGUARD_ORGANIZATION_ID") or "ados")
        await self.ensure_hydrated(org)
        events: list[dict[str, Any]] = []
        duplicates = 0
        for msg in parsed.get("messages") or []:
            pid = _txt(msg.get("provider_message_id"))
            key = webhook_event_key("in", pid)
            if seen_webhook(key) or self._whatsapp_event_recorded(org, pid):
                duplicates += 1
                inc_metric("whatsapp_webhook_duplicate_total")
                log_webhook_event("duplicate", kind="incoming", provider_message_id=pid)
                continue
            cand = match_candidate(list(self._bag(org).get("candidate") or []), str(msg.get("from") or ""))
            inbound_at = None
            parsed_ts = parse_event_time(msg.get("timestamp"))
            inbound_at = parsed_ts.isoformat() if parsed_ts else _now()
            saved = await self._record_whatsapp_message(
                org,
                {
                    "direction": "incoming",
                    "from_phone": msg.get("from"),
                    "body": msg.get("body"),
                    "status": "RECEIVED",
                    "send_status": "RECEIVED",
                    "sent": False,
                    "delivered": True,
                    "read": False,
                    "failed": False,
                    "provider_message_id": pid,
                    "candidate_id": cand.get("id") if cand else None,
                    "unresolved": cand is None,
                    "timestamp": msg.get("timestamp"),
                    "whatsapp_last_inbound_at": inbound_at,
                },
            )
            mark_webhook_seen(key)
            if cand:
                await self._touch_candidate_whatsapp(org, str(cand["id"]), inbound_at=inbound_at)
            events.append({"kind": "incoming", "id": saved.get("id"), "unresolved": cand is None})
        for status in parsed.get("statuses") or []:
            pid = _txt(status.get("provider_message_id"))
            st = _txt(status.get("status")).lower()
            key = webhook_event_key(st or "status", pid)
            if seen_webhook(key):
                duplicates += 1
                inc_metric("whatsapp_webhook_duplicate_total")
                log_webhook_event("duplicate", kind="status", provider_message_id=pid, status=st)
                continue
            if st == "delivered":
                inc_metric("whatsapp_message_delivered_total")
            if st == "read":
                inc_metric("whatsapp_message_read_total")
            matched = False
            for kind in ("outbound_message", "whatsapp_message"):
                for item in list(self._bag(org).get(kind) or []):
                    if _txt(item.get("provider_message_id")) != pid:
                        continue
                    matched = True
                    patch = {"updated_at": _now()}
                    if st == "sent":
                        patch.update({"send_status": "SENT", "sent": True, "delivered": False})
                    elif st == "delivered":
                        patch.update({"status": "DELIVERED", "delivered": True, "send_status": "DELIVERED"})
                    elif st == "read":
                        patch.update({"read": True, "status": item.get("status") or "DELIVERED"})
                    elif st == "failed":
                        patch.update({"status": "FAILED", "failed": True, "provider_error": status.get("error")})
                    item.update(patch)
                    await self._persist_patch(org, str(item.get("id")), patch)
                    self._replace(org, kind, item)
                    events.append({"kind": "status", "status": st, "id": item.get("id")})
            mark_webhook_seen(key)
            if not matched:
                log_webhook_event("status_unmatched", provider_message_id=pid, status=st)
        log_webhook_event(
            "processed",
            phone_number_id=phone_number_id or "none",
            events=len(events),
            duplicates=duplicates,
        )
        return self._ok(items=events, received=bool(events) or duplicates > 0, duplicate_count=duplicates)

    async def _probe_website(self, url: str) -> tuple[str, str]:
        try:
            import aiohttp

            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status < 500:
                        return STATUS_CONNECTED, f"Сайт ответил HTTP {resp.status}."
                    return STATUS_DEGRADED, f"Сайт ответил HTTP {resp.status}."
        except Exception as exc:
            return STATUS_DISCONNECTED, f"Сайт недоступен: {exc}"

    async def _storage_probe_reason(self) -> tuple[str, str]:
        try:
            from database.session import get_session
            from sqlalchemy import text

            async with get_session() as session:
                await session.execute(text("SELECT 1"))
                exists = await session.execute(text("SELECT to_regclass('public.recruiting_ops_records')"))
                table = exists.scalar()
            if not table:
                if memory_fallback_allowed():
                    return STATUS_DEGRADED, "PostgreSQL доступен, но таблица recruiting_ops_records отсутствует; заявки остаются в DEV memory."
                return STATUS_DISCONNECTED, "Таблица recruiting_ops_records отсутствует."
            return STATUS_CONNECTED, "PostgreSQL и recruiting_ops_records доступны."
        except Exception as exc:
            if memory_fallback_allowed():
                return STATUS_DEGRADED, f"PostgreSQL недоступен, DEV memory fallback: {exc}"
            return STATUS_DISCONNECTED, f"PostgreSQL недоступен: {exc}"

    async def _storage_probe(self) -> str:
        code, _reason = await self._storage_probe_reason()
        return code

    async def lookup_reference(
        self,
        organization_id: str,
        query: str,
        role: str | None = None,
    ) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        needle = _txt(query).lower()
        if not needle:
            return self._ok(found=False, items=[], query=query)
        hits = []
        for item in self._bag(org)["lead"]:
            fields = [
                _txt(item.get("external_id")),
                _txt(item.get("reference")),
                _txt(item.get("id")),
                _txt(item.get("email")),
                _txt(item.get("name")),
            ]
            if any(needle == field.lower() or needle in field.lower() for field in fields if field):
                hits.append(item)
        return self._ok(found=bool(hits), items=hits, query=query)

    async def list_activity(
        self,
        organization_id: str,
        role: str | None = None,
        *,
        project: str | None = None,
    ) -> dict[str, Any]:
        return await self.list_kind(organization_id, "activity", role, project=project)


_SVC: RecruitingOpsService | None = None


def get_recruiting_ops_service() -> RecruitingOpsService:
    global _SVC
    if _SVC is None:
        _SVC = RecruitingOpsService()
    return _SVC


def reset_recruiting_ops_for_tests() -> None:
    global _SVC
    _SVC = None
    from services.recruiting_ops.ingest_auth import reset_ingest_auth_for_tests
    from services.recruiting_ops.public_limits import reset_public_limits_for_tests

    reset_ingest_auth_for_tests()
    reset_public_limits_for_tests()
    from services.recruiting_ops.tracking_worker import reset_tracking_worker_for_tests

    reset_tracking_worker_for_tests()
    from services.recruiting_ops.secret_store import reset_secret_store_for_tests
    from services.recruiting_ops.provider_adapters import reset_adapters_for_tests
    from services.recruiting_ops.provider_connections import reset_runtime_connections

    reset_secret_store_for_tests()
    reset_adapters_for_tests()
    reset_runtime_connections()
    from services.recruiting_ops.provider_oauth import reset_oauth_nonces_for_tests

    reset_oauth_nonces_for_tests()
    from services.recruiting_ops.provider_live import set_smtp_factory

    set_smtp_factory(None)
    from services.recruiting_ops.provider_http import reset_http_transport
    from services.recruiting_ops.whatsapp_ops import reset_whatsapp_runtime_for_tests

    reset_http_transport()
    reset_whatsapp_runtime_for_tests()
