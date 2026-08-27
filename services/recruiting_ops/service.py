"""Recruiting Ops service — durable ATS desk (Sprint Recruiting 1.0).

Org-scoped memory bags hydrated from and persisted to Postgres
(`recruiting_ops_records`). Memory is kept when DB is unreachable.
No fake visits/metrics. Vanguard is contract-only until a later sprint.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from repositories.recruiting_ops_repository import RecruitingOpsRepository, record_to_dict
from services.recruiting_ops.rbac import can, normalize_role, require, roles_catalog

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

VANGUARD_CONTRACT = {
    "status": "contract_only",
    "connected": False,
    "integration": "vanguard_website",
    "message_ru": "Сайт Vanguard ещё не подключён. Контракт описывает будущий inbound lead.",
    "inbound": {
        "method": "POST",
        "path": "/api/recruiting-ops/v1/leads",
        "required": ["name"],
        "optional": [
            "phone",
            "email",
            "source",
            "campaign_id",
            "vacancy_id",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "notes",
        ],
        "example": {
            "name": "Иван Петров",
            "phone": "+380501112233",
            "email": "ivan@example.com",
            "source": "vanguard",
            "campaign_id": None,
            "vacancy_id": None,
            "utm_source": "vanguard",
            "utm_medium": "website",
            "utm_campaign": "career",
        },
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
                return record_to_dict(row)
        except Exception as exc:
            logger.warning("recruiting_ops persist %s failed (memory kept): %s", kind, exc)
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
        saved = await self._persist("activity", item)
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
            "data_modes": ["REAL", "DEMO"],
        }

    def vanguard_contract(self) -> dict[str, Any]:
        return {"ok": True, **VANGUARD_CONTRACT, "data_mode": "REAL"}

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "sprint": "recruiting_1.0",
            "vanguard": {"connected": False, "status": "contract_only"},
            "visits_available": False,
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

    async def analytics(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        bag = self._bag(org)
        leads = bag["lead"]
        candidates = bag["candidate"]
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
        )

    async def list_kind(self, organization_id: str, kind: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        items = list(self._bag(org).get(kind) or [])
        extra: dict[str, Any] = {}
        if kind == "task":
            overdue, upcoming = self._task_buckets(items)
            extra = {"overdue_tasks": overdue, "next_tasks": upcoming}
        if kind == "candidate":
            extra = {"pipeline": self._pipeline_groups(items)}
        return self._ok(items=items, **extra)

    def _pipeline_groups(self, candidates: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        groups = {stage: [] for stage in PIPELINE_STAGES}
        for cand in candidates:
            groups.setdefault(_stage(cand.get("pipeline_stage")), []).append(cand)
        return groups

    async def create_lead(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        name = _txt(body.get("name") or body.get("full_name"))
        if not name:
            return {"ok": False, "error": "validation", "message_ru": "Укажите имя лида"}
        org = _org(organization_id, body.get("tenant_id"))
        await self.ensure_hydrated(org)
        item = {
            "id": str(body.get("id") or uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "name": name,
            "phone": _txt(body.get("phone")),
            "email": _txt(body.get("email")),
            "source": _txt(body.get("source")) or "manual",
            "campaign_id": _txt(body.get("campaign_id")) or None,
            "vacancy_id": _txt(body.get("vacancy_id")) or None,
            "assignee": _txt(body.get("assignee")) or None,
            "status": _lead_status(body.get("status"), "new"),
            "notes": _txt(body.get("notes")),
            "utm_source": _txt(body.get("utm_source")) or None,
            "utm_medium": _txt(body.get("utm_medium")) or None,
            "utm_campaign": _txt(body.get("utm_campaign")) or None,
            "candidate_id": None,
            "data_mode": "REAL",
            "created_at": _now(),
            "updated_at": _now(),
        }
        saved = await self._persist("lead", item)
        self._bag(org)["lead"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="lead",
            entity_id=str(saved["id"]),
            action="lead_created",
            summary=f"Лид создан: {name}",
            role=role,
            payload={"source": saved.get("source")},
        )
        return self._ok(item=saved)

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

    async def list_activity(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        return await self.list_kind(organization_id, "activity", role)


_SVC: RecruitingOpsService | None = None


def get_recruiting_ops_service() -> RecruitingOpsService:
    global _SVC
    if _SVC is None:
        _SVC = RecruitingOpsService()
    return _SVC


def reset_recruiting_ops_for_tests() -> None:
    global _SVC
    _SVC = None
