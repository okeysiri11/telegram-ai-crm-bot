"""Recruiting Ops service — durable ATS desk (Sprint Recruiting 1.0).

Org-scoped memory bags hydrated from and persisted to Postgres
(`recruiting_ops_records`). Memory fallback is DEV/test only.
Production Vanguard ingest never reports success for a memory-only lead.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from repositories.recruiting_ops_repository import RecruitingOpsRepository, record_to_dict
from services.recruiting_ops.projects import (
    belongs_to_project,
    get_project,
    infer_project_key,
    project_catalog,
    resolve_project_key,
    status_payload,
    vanguard_website_url,
    STATUS_CONNECTED,
    STATUS_DEGRADED,
    STATUS_DISCONNECTED,
    STATUS_NOT_CONFIGURED,
    STATUS_UNKNOWN,
    VANGUARD_PROJECT_KEY,
)
from services.recruiting_ops.rbac import can, normalize_role, require, roles_catalog
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
            "notes",
        ],
        "example": {
            "first_name": "Иван",
            "last_name": "Петров",
            "phone": "+380501112233",
            "email": "ivan@example.com",
            "source": "vanguard",
            "vacancy_id": "vac-1",
            "external_id": "vg-1001",
            "utm_source": "vanguard",
            "utm_medium": "website",
            "utm_campaign": "career",
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
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = RecruitingOpsRepository(session)
                bag = self._bag(org)
                for kind in KINDS:
                    rows = await repo.list_kind(org, kind)
                    bag[kind] = [record_to_dict(r) for r in rows]
        except Exception as exc:
            logger.warning("recruiting_ops hydrate skipped: %s", exc)
        self._hydrated.add(org)

    async def _persist(self, kind: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = RecruitingOpsRepository(session)
                row = await repo.insert(kind, data)
                saved = record_to_dict(row)
                saved["storage"] = "postgres"
                saved["durable"] = True
                saved["persistence_mode"] = "POSTGRES"
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
            "data_modes": ["REAL", "DEMO", "NON_DURABLE_DEVELOPMENT_MODE"],
            "ads": ads_foundation(),
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
            "sprint": "recruiting_1.5",
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
            "ads": {"connected": False, "message_ru": "Провайдер не подключен"},
        }

    def _ok(self, **extra: Any) -> dict[str, Any]:
        return {"ok": True, "data_mode": "REAL", **extra}

    async def dashboard(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        bag = self._bag(org)
        overdue, upcoming = self._task_buckets(bag["task"])
        unassigned = [l for l in bag["lead"] if not _txt(l.get("assignee")) and l.get("status") != "converted"]
        attention = []
        if overdue:
            attention.append({"kind": "overdue_tasks", "count": len(overdue), "message_ru": f"Просрочено задач: {len(overdue)}"})
        if unassigned:
            attention.append({"kind": "unassigned_leads", "count": len(unassigned), "message_ru": f"Лиды без рекрутера: {len(unassigned)}"})
        return self._ok(
            cards={
                "leads": len(bag["lead"]),
                "candidates": len(bag["candidate"]),
                "vacancies": len(bag["vacancy"]),
                "overdue_tasks": len(overdue),
                "next_tasks": len(upcoming),
            },
            overdue_tasks=overdue[:10],
            next_tasks=upcoming[:10],
            attention=attention,
            visits=VISITS_UNAVAILABLE,
            vanguard=self.vanguard_contract(),
            projects=self._project_summaries(org, bag),
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
        await self.ensure_hydrated(org)
        bag = self._bag(org)
        key = _txt(project).lower()
        leads = list(bag["lead"])
        candidates = list(bag["candidate"])
        if key:
            leads = [item for item in leads if belongs_to_project(item, key)]
            candidates = [item for item in candidates if belongs_to_project(item, key)]
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
        for cand in candidates:
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
        await self.ensure_hydrated(org)
        items = list(self._bag(org).get(kind) or [])
        key = _txt(project).lower()
        if key:
            items = self._filter_project_items(org, kind, items, key)
        extra: dict[str, Any] = {}
        if kind == "task":
            overdue, upcoming = self._task_buckets(items)
            extra = {"overdue_tasks": overdue, "next_tasks": upcoming}
        if kind == "candidate":
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
        groups = {stage: [] for stage in PIPELINE_STAGES}
        for cand in candidates:
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
            "phone": _txt(body.get("phone")),
            "email": _txt(body.get("email")),
            "source": _txt(body.get("source")) or "manual",
            "project_key": infer_project_key(
                source=_txt(body.get("source")) or "manual",
                project_key=_txt(body.get("project_key")) or None,
            ),
            "campaign_id": _txt(body.get("campaign_id")) or None,
            "vacancy_id": vacancy,
            "vacancy": _txt(body.get("vacancy")) or vacancy,
            "external_id": _txt(body.get("external_id") or body.get("reference") or body.get("reference_id")) or None,
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
        from services.recruiting_ops.attribution import touch_payload

        item.update(touch_payload(body))
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

    def _find_duplicate(
        self,
        org: str,
        *,
        external_id: str | None,
        vacancy_id: str | None,
        email: str | None = None,
        program: str | None = None,
    ) -> dict[str, Any] | None:
        ext = _txt(external_id)
        vac = _txt(vacancy_id)
        if ext:
            for item in self._bag(org)["lead"]:
                if _txt(item.get("external_id")) != ext:
                    continue
                if _txt(item.get("vacancy_id") or item.get("vacancy") or item.get("program_of_interest")) == vac:
                    return item
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
        org = _org(
            body.get("organization_id") or os.getenv("VANGUARD_ORGANIZATION_ID") or "ados",
            body.get("tenant_id"),
        )
        await self.ensure_hydrated(org)
        vacancy = _txt(body.get("vacancy_id") or body.get("vacancy")) or None
        external_id = _txt(body.get("external_id") or body.get("reference") or body.get("reference_id")) or None
        self._ingest_log["last_check_at"] = _now()
        existing = self._find_duplicate(
            org,
            external_id=external_id,
            vacancy_id=vacancy,
            email=email,
            program=_txt(body.get("program_of_interest") or body.get("program")),
        )
        if existing:
            from services.recruiting_ops.attribution import preserve_first_touch

            patch = preserve_first_touch(existing, body)
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
            return self._ok(item=existing, duplicate=True, already_exists=True)
        payload = dict(body)
        payload["name"] = name
        payload["first_name"] = first
        payload["last_name"] = last
        payload["source"] = _txt(body.get("source")) or "vanguard"
        payload["project_key"] = VANGUARD_PROJECT_KEY
        payload["vacancy_id"] = vacancy
        payload["external_id"] = external_id
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
        event["delivery_status"] = "RETRYING"
        if event.get("event_id"):
            for existing in self._bag(org)["tracking"]:
                if _txt(existing.get("event_id")) == event["event_id"]:
                    existing.setdefault("delivery_status", "DELIVERED")
                    return self._ok(item=existing, duplicate=True, delivery_status=existing.get("delivery_status") or "DELIVERED")
        saved: dict[str, Any] | None = None
        try:
            event["delivery_status"] = "RETRYING"
            saved = await self._persist("tracking", event)
        except PersistUnavailable:
            queued = get_tracking_worker().enqueue({**event, "organization_id": org})
            logger.warning("vanguard tracking queued for worker event_id=%s", event.get("event_id"))
            return {
                "ok": False,
                "error": "tracking_retrying",
                "delivery_status": "RETRYING",
                "message_ru": "Событие в повторной доставке",
                "item": queued,
            }
        saved["delivery_status"] = "DELIVERED"
        self._bag(org)["tracking"].insert(0, saved)
        return self._ok(item=saved, delivery_status="DELIVERED")

    async def process_tracking_retries(self) -> dict[str, Any]:
        async def _persist(event: dict[str, Any]) -> dict[str, Any]:
            return await self._persist("tracking", event)

        done = await get_tracking_worker().tick(_persist)
        org = _org(os.getenv("VANGUARD_ORGANIZATION_ID") or "ados")
        await self.ensure_hydrated(org)
        for item in done:
            if item.get("delivery_status") == "DELIVERED":
                self._bag(org)["tracking"].insert(0, item)
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
        item = self._find(org, "lead", lead_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Лид не найден"}
        patch = dict(body)
        if "status" in patch:
            patch["status"] = _lead_status(patch.get("status"), item.get("status") or "new")
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
        assignee = _txt(body.get("assignee"))
        if not assignee:
            return {"ok": False, "error": "validation", "message_ru": "Укажите рекрутера"}
        result = await self.update_lead(organization_id, lead_id, {"assignee": assignee}, role, "update")
        if result.get("ok"):
            await self._activity(
                organization_id=_org(organization_id),
                entity_type="lead",
                entity_id=lead_id,
                action="lead_assigned",
                summary=f"Лид назначен рекрутеру: {assignee}",
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

    async def convert_lead(self, organization_id: str, lead_id: str, body: dict[str, Any] | None = None, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "convert")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        lead = self._find(org, "lead", lead_id)
        if not lead:
            return {"ok": False, "error": "not_found", "message_ru": "Лид не найден"}
        if lead.get("candidate_id"):
            existing = self._find(org, "candidate", str(lead["candidate_id"]))
            return self._ok(item=existing, lead=lead, already_converted=True)
        body = body or {}
        stage = _stage(body.get("pipeline_stage") or ("QUALIFIED" if lead.get("status") == "qualified" else "NEW"))
        candidate_body = {
            "name": lead.get("name"),
            "phone": lead.get("phone"),
            "email": lead.get("email"),
            "source": lead.get("source"),
            "project_key": lead.get("project_key") or infer_project_key(source=_txt(lead.get("source"))),
            "campaign_id": lead.get("campaign_id"),
            "vacancy_id": body.get("vacancy_id") or lead.get("vacancy_id"),
            "assignee": body.get("assignee") or lead.get("assignee"),
            "lead_id": lead_id,
            "pipeline_stage": stage,
            "notes": lead.get("notes"),
        }
        created = await self.create_candidate(org, candidate_body, role)
        if not created.get("ok"):
            return created
        candidate = created["item"]
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
        org = _org(organization_id, body.get("tenant_id"))
        await self.ensure_hydrated(org)
        item = {
            "id": str(body.get("id") or uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "name": name,
            "phone": _txt(body.get("phone")),
            "email": _txt(body.get("email")),
            "source": _txt(body.get("source")) or None,
            "project_key": infer_project_key(
                source=_txt(body.get("source")) or None,
                project_key=_txt(body.get("project_key")) or None,
            ),
            "campaign_id": _txt(body.get("campaign_id")) or None,
            "vacancy_id": _txt(body.get("vacancy_id")) or None,
            "assignee": _txt(body.get("assignee")) or None,
            "lead_id": _txt(body.get("lead_id")) or None,
            "pipeline_stage": _stage(body.get("pipeline_stage")),
            "notes": _txt(body.get("notes")),
            "status": _stage(body.get("pipeline_stage")),
            "data_mode": "REAL",
            "created_at": _now(),
            "updated_at": _now(),
        }
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
        return self._ok(item=saved)

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
        item = self._find(org, "candidate", candidate_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Кандидат не найден"}
        stage = _stage(body.get("pipeline_stage") or body.get("stage") or body.get("status"), item.get("pipeline_stage") or "NEW")
        patch = {"pipeline_stage": stage, "status": stage, "updated_at": _now()}
        if body.get("assignee"):
            patch["assignee"] = _txt(body.get("assignee"))
        if body.get("notes"):
            patch["notes"] = _txt(body.get("notes"))
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
        await self._activity(
            organization_id=org,
            entity_type="candidate",
            entity_id=candidate_id,
            action="pipeline_moved",
            summary=f"Кандидат перемещён в {stage}",
            role=role,
            payload={"pipeline_stage": stage},
        )
        return self._ok(item=item)

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
            "start_date": _txt(body.get("start_date")) or None,
            "end_date": _txt(body.get("end_date")) or None,
            "budget": body.get("budget"),
            "spend": body.get("spend"),
            "impressions": body.get("impressions"),
            "clicks": body.get("clicks"),
            "ads_provider": None,
            "ads_api": "not_connected",
            "vacancy_id": _txt(body.get("vacancy_id")) or None,
            "status": _txt(body.get("status")) or "active",
            "notes": _txt(body.get("notes")),
            "data_mode": "REAL",
            "created_at": _now(),
            "updated_at": _now(),
        }
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
        ):
            if field in body:
                patch[field] = body.get(field)
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

    async def ads_control_center(self, organization_id: str, project_key: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        spec = get_project(project_key) or {"project_key": project_key}
        key = spec.get("project_key") or VANGUARD_PROJECT_KEY
        leads = [item for item in self._bag(org)["lead"] if belongs_to_project(item, key)]
        cands = [item for item in self._bag(org)["candidate"] if belongs_to_project(item, key)]
        events = [item for item in self._bag(org).get("tracking") or [] if belongs_to_project(item, key)]
        campaigns = self._campaign_metrics(org, key, leads, cands, events)
        from services.recruiting_ops.ads_control import control_center
        from services.recruiting_ops.attribution import source_analytics

        payload = control_center(project_key=key, campaigns=campaigns)
        payload["source_analytics"] = source_analytics(leads, cands)
        payload["funnel"] = self._marketing_funnel(org, key, leads, cands, {})
        payload["attribution"] = self._attribution_snapshot(leads, events)
        payload["entities"] = {kind: list(self._bag(org).get(kind) or []) for kind in ("ad_account", "ad_set", "creative", "audience", "ads_metrics")}
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
            "delivery": "manual_log_only",
            "status": "logged",
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
        await self.ensure_hydrated(org)
        bag = self._bag(org)
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
        await self.ensure_hydrated(org)
        key = spec["project_key"]
        leads = [item for item in self._bag(org)["lead"] if belongs_to_project(item, key)]
        cands = [item for item in self._bag(org)["candidate"] if belongs_to_project(item, key)]
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
        from services.recruiting_ops.attribution import source_analytics

        campaigns = self._campaign_metrics(org, key, leads, cands, traffic["events"])
        comms = [item for item in self._bag(org)["communication"] if belongs_to_project(item, key)]
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
            traffic=traffic,
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
            recent_leads=leads[:10],
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
        events = [item for item in self._bag(org).get("tracking") or [] if belongs_to_project(item, project_key)]
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
    ) -> list[dict[str, Any]]:
        from services.recruiting_ops.ads_control import campaign_costs

        out = []
        for camp in self._bag(org)["campaign"]:
            if not belongs_to_project(camp, project_key) and _txt(camp.get("source")).lower() != "vanguard":
                continue
            cid = _txt(camp.get("id"))
            code = _txt(camp.get("campaign_code") or camp.get("utm_campaign") or camp.get("name"))
            camp_leads = [
                item
                for item in leads
                if _txt(item.get("campaign_id")) == cid or _txt(item.get("utm_campaign")) == code
            ]
            camp_cands = [
                item
                for item in cands
                if _txt(item.get("campaign_id")) == cid or _txt(item.get("utm_campaign")) == code
            ]
            visits = [
                item
                for item in events
                if _txt(item.get("campaign_id")) == cid or _txt(item.get("utm_campaign")) == code
            ]
            spend = camp.get("spend")
            costs = campaign_costs(
                spend=spend,
                impressions=camp.get("impressions"),
                clicks=camp.get("clicks"),
                applications=len(camp_leads),
                leads=len(camp_leads),
                candidates=len(camp_cands),
            )
            item = dict(camp)
            item["visits"] = len(visits) if visits else None
            item["applications"] = len(camp_leads)
            item["leads"] = len(camp_leads)
            item["candidates"] = len(camp_cands)
            item["conversion"] = self._pct(len(camp_cands), len(camp_leads))
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
        tracking_code, tracking_reason = self._tracking_health_reason()
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
            "tracking": status_payload(tracking_code, reason_ru=tracking_reason),
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
        org = _org(os.getenv("VANGUARD_ORGANIZATION_ID") or "ados")
        events = self._bag(org).get("tracking") or []
        if not events:
            return STATUS_UNKNOWN, "Событий трекинга ещё нет."
        statuses = {_txt(item.get("delivery_status")) for item in events}
        if "FAILED" in statuses:
            return STATUS_DEGRADED, "Есть недоставленные события трекинга."
        if "RETRYING" in statuses:
            return STATUS_DEGRADED, "Есть события в повторной доставке."
        if events and any(item.get("persistence_mode") == "NON_DURABLE_DEVELOPMENT_MODE" for item in events):
            return STATUS_DEGRADED, "Трекинг в NON_DURABLE_DEVELOPMENT_MODE."
        return STATUS_CONNECTED, "События трекинга доставляются."

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
