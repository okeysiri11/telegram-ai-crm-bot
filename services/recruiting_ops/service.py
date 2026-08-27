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
    status_payload,
    vanguard_website_url,
    STATUS_CONNECTED,
    STATUS_DEGRADED,
    STATUS_OFFLINE,
    STATUS_UNKNOWN,
    VANGUARD_PROJECT_KEY,
)
from services.recruiting_ops.rbac import can, normalize_role, require, roles_catalog
from services.recruiting_ops.runtime import is_production_runtime, memory_fallback_allowed

logger = logging.getLogger(__name__)

KINDS = (
    "lead",
    "candidate",
    "vacancy",
    "campaign",
    "task",
    "communication",
    "activity",
)

LEAD_STATUSES = ("new", "qualified", "converted", "lost")
PIPELINE_STAGES = ("NEW", "QUALIFIED", "INTERVIEW", "APPROVED", "HIRED", "REJECTED")
TASK_STATUSES = ("open", "done", "cancelled")
COMM_CHANNELS = ("TELEGRAM", "WHATSAPP", "EMAIL", "PHONE", "MANUAL")
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
                return saved
        except Exception as exc:
            if not memory_fallback_allowed():
                logger.error("recruiting_ops persist %s failed in production: %s", kind, exc)
                raise PersistUnavailable(str(exc)) from exc
            logger.warning("recruiting_ops persist %s failed (DEV memory kept): %s", kind, exc)
            data["storage"] = "memory"
            data["durable"] = False
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
            logger.warning("recruiting_ops patch persist skipped: %s", exc)
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
        return {
            "ok": True,
            "lead_statuses": list(LEAD_STATUSES),
            "pipeline_stages": list(PIPELINE_STAGES),
            "task_statuses": list(TASK_STATUSES),
            "task_templates": list(TASK_TEMPLATES),
            "communication_channels": list(COMM_CHANNELS),
            "projects": project_catalog(),
            "data_modes": ["REAL", "DEMO"],
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
            "sprint": "recruiting_1.2",
            "vanguard": {
                "connected": False,
                "status": "ingest_ready",
                "inbound": "/api/recruiting-ops/v1/vanguard/leads",
            },
            "visits_available": False,
            "production": is_production_runtime(),
            "memory_fallback_allowed": memory_fallback_allowed(),
            "roles": self.roles(),
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
        if kind in {"lead", "candidate", "campaign", "communication", "task"}:
            return [item for item in items if belongs_to_project(item, project_key)]
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
            "candidate_id": None,
            "data_mode": "REAL",
            "created_at": _now(),
            "updated_at": _now(),
        }
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

    def _find_duplicate(self, org: str, *, external_id: str | None, vacancy_id: str | None) -> dict[str, Any] | None:
        ext = _txt(external_id)
        if not ext:
            return None
        vac = _txt(vacancy_id)
        for item in self._bag(org)["lead"]:
            if _txt(item.get("external_id")) != ext:
                continue
            if _txt(item.get("vacancy_id") or item.get("vacancy")) == vac:
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
        existing = self._find_duplicate(org, external_id=external_id, vacancy_id=vacancy)
        if existing:
            await self._activity(
                organization_id=org,
                entity_type="lead",
                entity_id=str(existing["id"]),
                action="vanguard_lead_duplicate",
                summary=f"Повторная заявка Vanguard: {existing.get('name')}",
                role="platform_owner",
                payload={"external_id": external_id, "vacancy_id": vacancy},
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
                },
            )
            self._note_ingest_success()
        else:
            self._note_ingest_error(str(created.get("error") or "ingest_failed"), str(created.get("message_ru") or ""))
        return created

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
        persisted = await self._persist_patch(org, candidate_id, patch)
        if persisted:
            item = persisted
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
            "assignee": _txt(body.get("assignee")) or None,
            "due_date": _parse_date(body.get("due_date") or body.get("due_at")),
            "status": _task_status(body.get("status"), "open"),
            "notes": _txt(body.get("notes")),
            "data_mode": "REAL",
            "created_at": _now(),
            "updated_at": _now(),
        }
        saved = await self._persist("task", item)
        self._bag(org)["task"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="task",
            entity_id=str(saved["id"]),
            action="task_created",
            summary=f"Задача: {title}",
            role=role,
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
            "sent": False,
            "delivery": "manual_log_only",
            "status": "logged",
            "data_mode": "REAL",
            "created_at": _now(),
            "updated_at": _now(),
        }
        saved = await self._persist("communication", item)
        self._bag(org)["communication"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="communication",
            entity_id=str(saved["id"]),
            action="communication_logged",
            summary=text,
            role=role,
            payload={"channel": channel, "sent": False},
        )
        return self._ok(item=saved)

    def _note_ingest_success(self) -> None:
        self._ingest_log["last_success_at"] = _now()
        self._ingest_log["last_check_at"] = self._ingest_log["last_success_at"]

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
        today_leads = [item for item in leads if _date_only(item.get("created_at")) == today]
        converted = [item for item in leads if _lead_status(item.get("status")) == "converted"]
        conversion = round(len(converted) / len(leads), 4) if leads else None
        last_lead = leads[0] if leads else None
        analytics = await self.analytics(org, role, project=key)
        stages = analytics.get("pipeline_stages") if analytics.get("ok") else {}
        return self._ok(
            project=spec,
            relationship=[
                {"id": "website", "label_ru": "Сайт Vanguard"},
                {"id": "recruiting", "label_ru": "Рекрутинг"},
                {"id": "leads", "label_ru": "Лиды"},
                {"id": "candidates", "label_ru": "Кандидаты"},
            ],
            cards={
                "new_leads": len([item for item in leads if _lead_status(item.get("status")) == "new"]),
                "candidates": len(cands),
                "active_vacancies": self._active_vacancy_count(org, key),
                "applications_today": len(today_leads),
                "lead_to_candidate": conversion,
                "last_application_at": (last_lead or {}).get("created_at"),
            },
            recent_leads=leads[:10],
            pipeline=stages,
            funnel=analytics.get("funnel") if analytics.get("ok") else None,
        )

    async def project_integration(self, organization_id: str, project_key: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        spec = get_project(project_key)
        if not spec:
            return {"ok": False, "error": "not_found", "message_ru": "Проект не найден"}
        self._ingest_log["last_check_at"] = _now()
        from services.recruiting_ops.ingest_auth import resolve_ingest_secret

        url = vanguard_website_url()
        website_code = STATUS_UNKNOWN if not url else STATUS_CONNECTED
        endpoint_code = STATUS_CONNECTED if resolve_ingest_secret() else (
            STATUS_OFFLINE if is_production_runtime() else STATUS_DEGRADED
        )
        recruiting_code = STATUS_CONNECTED
        db_code = await self._storage_probe()
        stages = [
            {"id": "website", "label_ru": "Сайт Vanguard", "code": status_payload(website_code)["code"], "status_label_ru": status_payload(website_code)["label_ru"]},
            {"id": "vanguard_endpoint", "label_ru": "Серверный endpoint Vanguard", "code": status_payload(endpoint_code)["code"], "status_label_ru": status_payload(endpoint_code)["label_ru"]},
            {"id": "recruiting_api", "label_ru": "Recruiting API", "code": status_payload(recruiting_code)["code"], "status_label_ru": status_payload(recruiting_code)["label_ru"]},
            {"id": "database", "label_ru": "База данных", "code": status_payload(db_code)["code"], "status_label_ru": status_payload(db_code)["label_ru"]},
        ]
        codes = [row["code"] for row in stages]
        if STATUS_OFFLINE in codes:
            overall = STATUS_OFFLINE
        elif STATUS_DEGRADED in codes:
            overall = STATUS_DEGRADED
        elif STATUS_UNKNOWN in codes:
            overall = STATUS_DEGRADED if STATUS_CONNECTED in codes else STATUS_UNKNOWN
        else:
            overall = STATUS_CONNECTED
        return self._ok(
            project=spec,
            overall=status_payload(overall),
            website_status=status_payload(website_code),
            integration_status=status_payload(overall),
            stages=stages,
            website={
                "name": spec["name"],
                "public_url": url,
                "environment": "production" if is_production_runtime() else "development",
            },
            last_success_at=self._ingest_log.get("last_success_at"),
            last_error=self._ingest_log.get("last_error"),
            last_error_at=self._ingest_log.get("last_error_at"),
            last_check_at=self._ingest_log.get("last_check_at"),
        )

    async def _storage_probe(self) -> str:
        try:
            from database.session import get_session
            from sqlalchemy import text

            async with get_session() as session:
                await session.execute(text("SELECT 1"))
            return STATUS_CONNECTED
        except Exception:
            return STATUS_DEGRADED if memory_fallback_allowed() else STATUS_OFFLINE

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

    reset_ingest_auth_for_tests()
