"""Legal Ops service — durable Lawyer CRM (Sprint 51.0)."""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from repositories.legal_ops_repository import LegalOpsRepository, row_to_dict
from services.legal_ops import google_calendar as gcal
from services.legal_ops.ai_ops import LegalOpsAiMixin
from services.legal_ops.desk_ops import LegalOpsDeskMixin, active_only
from services.legal_ops.monitoring import LegalOpsMonitoringMixin
from services.legal_ops.rbac import can, normalize_role, require, roles_catalog

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _org(organization_id: str | None, tenant_id: str | None = None) -> str:
    return (organization_id or tenant_id or "default").strip() or "default"


class LegalOpsService(LegalOpsDeskMixin, LegalOpsAiMixin, LegalOpsMonitoringMixin):
    """Org-scoped Lawyer CRM with Postgres persistence + memory fallback."""

    def __init__(self) -> None:
        self._mem: dict[str, dict[str, list[dict[str, Any]]]] = {}
        self._hydrated: set[str] = set()

    def _bag(self, org: str) -> dict[str, list[dict[str, Any]]]:
        if org not in self._mem:
            self._mem[org] = {
                "clients": [],
                "cases": [],
                "contracts": [],
                "documents": [],
                "tasks": [],
                "hearings": [],
                "calendar": [],
                "activity": [],
                "files": [],
                "ai_analyses": [],
                "watchlist": [],
                "monitor_changes": [],
                "enforcement": [],
                "calendar_mappings": [],
            }
        bag = self._mem[org]
        for key in ("ai_analyses", "watchlist", "monitor_changes", "enforcement", "calendar_mappings", "notifications"):
            bag.setdefault(key, [])
        if "monitor_settings" not in bag:
            bag["monitor_settings"] = None  # type: ignore[assignment]
        return bag  # type: ignore[return-value]

    async def ensure_hydrated(self, organization_id: str) -> None:
        org = _org(organization_id)
        if org in self._hydrated:
            return
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = LegalOpsRepository(session)
                bag = self._bag(org)
                bag["clients"] = [row_to_dict(r) for r in await repo.list_clients(org)]
                bag["cases"] = [row_to_dict(r) for r in await repo.list_cases(org)]
                bag["contracts"] = [row_to_dict(r) for r in await repo.list_contracts(org)]
                bag["documents"] = [row_to_dict(r) for r in await repo.list_documents(org)]
                bag["tasks"] = [row_to_dict(r) for r in await repo.list_tasks(org)]
                bag["hearings"] = [row_to_dict(r) for r in await repo.list_hearings(org)]
                bag["calendar"] = [row_to_dict(r) for r in await repo.list_calendar(org)]
                bag["activity"] = [row_to_dict(r) for r in await repo.list_activity(org)]
                bag["files"] = [row_to_dict(r) for r in await repo.list_files(org)]
                try:
                    bag["ai_analyses"] = [row_to_dict(r) for r in await repo.list_ai_analyses(org)]
                except Exception as ai_exc:
                    logger.warning("legal_ops ai_analyses hydrate skipped: %s", ai_exc)
                    bag["ai_analyses"] = bag.get("ai_analyses") or []
                try:
                    bag["watchlist"] = [row_to_dict(r) for r in await repo.list_watchlist(org)]
                    bag["monitor_changes"] = [row_to_dict(r) for r in await repo.list_monitor_changes(org)]
                    bag["enforcement"] = [row_to_dict(r) for r in await repo.list_enforcement(org)]
                    bag["calendar_mappings"] = [row_to_dict(r) for r in await repo.list_calendar_mappings(org)]
                    ms = await repo.get_monitor_settings(org)
                    bag["monitor_settings"] = row_to_dict(ms) if ms else None
                except Exception as mon_exc:
                    logger.warning("legal_ops monitor hydrate skipped: %s", mon_exc)
        except Exception as exc:
            logger.warning("legal_ops hydrate skipped: %s", exc)
        self._hydrated.add(org)

    async def _persist(self, kind: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = LegalOpsRepository(session)
                if kind == "client":
                    row = await repo.insert_client(data)
                elif kind == "case":
                    row = await repo.insert_case(data)
                elif kind == "contract":
                    row = await repo.insert_contract(data)
                elif kind == "document":
                    row = await repo.insert_document(data)
                elif kind == "task":
                    row = await repo.insert_task(data)
                elif kind == "hearing":
                    row = await repo.insert_hearing(data)
                elif kind == "calendar":
                    row = await repo.insert_calendar_event(data)
                elif kind == "activity":
                    row = await repo.insert_activity(data)
                elif kind == "file":
                    row = await repo.insert_file(data)
                elif kind == "ai_analysis":
                    row = await repo.insert_ai_analysis(data)
                elif kind == "watchlist":
                    row = await repo.insert_watchlist(data)
                elif kind == "monitor_change":
                    row = await repo.insert_monitor_change(data)
                elif kind == "enforcement":
                    row = await repo.insert_enforcement(data)
                elif kind == "calendar_mapping":
                    row = await repo.insert_calendar_mapping(data)
                elif kind == "monitor_settings":
                    row = await repo.upsert_monitor_settings(data)
                else:
                    return data
                return row_to_dict(row)
        except Exception as exc:
            logger.warning("legal_ops persist %s failed (memory kept): %s", kind, exc)
            return data

    async def _activity(
        self,
        *,
        organization_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        summary: str,
        role: str | None = None,
        actor_id: str | None = None,
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
            "actor_id": actor_id,
            "summary": summary,
            "payload": payload or {},
            "created_at": _now(),
        }
        saved = await self._persist("activity", item)
        self._bag(org)["activity"].insert(0, saved)
        return saved

    def roles(self) -> list[dict[str, Any]]:
        return roles_catalog()

    def gcal_status(self) -> dict[str, Any]:
        from services.legal_ops.calendar_integration import get_calendar_integration
        from services.legal_ops.monitoring import scrub_secrets

        return scrub_secrets(get_calendar_integration().google.status())

    async def dashboard(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        bag = self._bag(org)
        today = datetime.now(timezone.utc).date().isoformat()
        hearings_today = [
            h
            for h in active_only(bag["hearings"])
            if str(h.get("scheduled_at") or "").startswith(today) and str(h.get("status")) != "cancelled"
        ]
        open_deadlines = [
            t
            for t in active_only(bag["tasks"])
            if str(t.get("kind")) == "deadline"
            and str(t.get("status")).lower() in {"open", "pending", "new", "in_progress", "waiting"}
        ]
        pending_approvals = [c for c in active_only(bag["contracts"]) if str(c.get("approval_status")) == "pending"]
        return {
            "ok": True,
            "organization_id": org,
            "role": normalize_role(role),
            "cards": {
                "clients": len(active_only(bag["clients"])),
                "open_cases": len([c for c in active_only(bag["cases"]) if str(c.get("status")) == "open"]),
                "hearings_today": len(hearings_today),
                "open_deadlines": len(open_deadlines),
                "pending_approvals": len(pending_approvals),
            },
            "hearings_today": hearings_today[:10],
            "open_deadlines": open_deadlines[:10],
            "pending_approvals": pending_approvals[:10],
            "google_calendar": self.gcal_status(),
        }

    async def list_clients(self, organization_id: str, role: str | None = None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        items = active_only(self._bag(org)["clients"])
        if query:
            items = self.filter_items(items, query)
        return {"ok": True, "items": items}

    async def create_client(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        name = str(body.get("name") or "").strip()
        if not name:
            return {"ok": False, "error": "validation", "message_ru": "Укажите имя клиента"}
        tags = body.get("tags") or []
        if isinstance(tags, str):
            tags = [x.strip() for x in tags.split(",") if x.strip()]
        contacts = body.get("contacts") or []
        if isinstance(contacts, str):
            contacts = [x.strip() for x in contacts.split(",") if x.strip()]
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "name": name,
            "email": body.get("email"),
            "phone": body.get("phone"),
            "status": body.get("status") or "active",
            "notes": body.get("notes"),
            "client_type": body.get("client_type") or "person",
            "avatar_file_id": body.get("avatar_file_id"),
            "address": body.get("address"),
            "city": body.get("city"),
            "country": body.get("country"),
            "company": body.get("company"),
            "position": body.get("position"),
            "responsible": body.get("responsible"),
            "source": body.get("source"),
            "identity_data": body.get("identity_data"),
            "tags": tags,
            "contacts": contacts,
            "payload": body.get("payload") or {},
            "created_at": _now(),
        }
        saved = await self._persist("client", item)
        self._bag(org)["clients"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="client",
            entity_id=saved["id"],
            action="client_created",
            summary=f"Клиент создан: {name}",
            role=role,
        )
        return {"ok": True, "item": saved}

    async def list_cases(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        return {"ok": True, "items": active_only(self._bag(org)["cases"])}

    async def create_case(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        title = str(body.get("title") or "").strip()
        if not title:
            return {"ok": False, "error": "validation", "message_ru": "Укажите название дела"}
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "client_id": body.get("client_id"),
            "title": title,
            "case_number": body.get("case_number") or f"CASE-{uuid.uuid4().hex[:8].upper()}",
            "status": body.get("status") or "open",
            "practice_area": body.get("practice_area"),
            "responsible": body.get("responsible"),
            "case_type": body.get("case_type"),
            "court": body.get("court"),
            "judge": body.get("judge"),
            "notes": body.get("notes"),
            "priority": body.get("priority") or "normal",
            "participants": body.get("participants") or [],
            "deadline_at": body.get("deadline_at"),
            "court_case_number": body.get("court_case_number"),
            "description": body.get("description"),
            "opened_at": body.get("opened_at") or _now(),
            "timeline": [{"at": _now(), "event": "case_created", "summary": "Дело создано"}],
            "payload": body.get("payload") or {},
            "created_at": _now(),
        }
        saved = await self._persist("case", item)
        self._bag(org)["cases"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="case",
            entity_id=saved["id"],
            action="case_created",
            summary=f"Дело создано: {title}",
            role=role,
        )
        await self.ensure_linked_calendar(org, "case", saved, role)
        return {"ok": True, "item": saved}

    async def get_case(self, organization_id: str, case_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        case = next((c for c in self._bag(org)["cases"] if c.get("id") == case_id), None)
        if not case:
            return {"ok": False, "error": "not_found", "message_ru": "Дело не найдено"}
        activity = [a for a in self._bag(org)["activity"] if a.get("entity_id") == case_id]
        return {"ok": True, "item": case, "timeline": case.get("timeline") or [], "activity": activity}

    async def list_contracts(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        return {"ok": True, "items": active_only(self._bag(org)["contracts"])}

    async def create_contract(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        title = str(body.get("title") or "").strip()
        if not title:
            return {"ok": False, "error": "validation", "message_ru": "Укажите название договора"}
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "client_id": body.get("client_id"),
            "case_id": body.get("case_id"),
            "title": title,
            "status": body.get("status") or "draft",
            "approval_status": body.get("approval_status") or "pending",
            "body": body.get("body") or "",
            "contract_number": body.get("contract_number"),
            "counterparty": body.get("counterparty"),
            "responsible": body.get("responsible"),
            "start_at": body.get("start_at"),
            "end_at": body.get("end_at"),
            "deadline_at": body.get("deadline_at"),
            "notes": body.get("notes"),
            "signing_status": body.get("signing_status") or "draft",
            "contract_type": body.get("contract_type") or "services",
            "amount": body.get("amount"),
            "currency": body.get("currency") or "RUB",
            "contract_date": body.get("contract_date"),
            "payload": body.get("payload") or {},
            "created_at": _now(),
        }
        saved = await self._persist("contract", item)
        self._bag(org)["contracts"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="contract",
            entity_id=saved["id"],
            action="contract_created",
            summary=f"Договор создан: {title}",
            role=role,
        )
        await self.ensure_linked_calendar(org, "contract", saved, role)
        return {"ok": True, "item": saved}

    async def update_contract(self, organization_id: str, contract_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        action = "approve" if "approval_status" in body and body.get("approval_status") != "pending" else "update"
        denied = require(role, action if action == "approve" else "update")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        items = self._bag(org)["contracts"]
        idx = next((i for i, c in enumerate(items) if c.get("id") == contract_id), None)
        if idx is None:
            return {"ok": False, "error": "not_found", "message_ru": "Договор не найден"}
        cur = dict(items[idx])
        for key in ("title", "status", "approval_status", "body", "payload", "client_id", "case_id"):
            if key in body:
                cur[key] = body[key]
        cur["updated_at"] = _now()
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = LegalOpsRepository(session)
                row = await repo.get_contract(org, contract_id)
                if row:
                    await repo.update_contract(row, body)
                    cur = row_to_dict(row)
        except Exception as exc:
            logger.warning("contract update persist skipped: %s", exc)
        items[idx] = cur
        act = "approval_changed" if "approval_status" in body else "contract_edited"
        await self._activity(
            organization_id=org,
            entity_type="contract",
            entity_id=contract_id,
            action=act,
            summary=f"Договор обновлён ({act})",
            role=role,
            payload={"patch": body},
        )
        return {"ok": True, "item": cur}

    async def list_documents(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        return {"ok": True, "items": active_only(self._bag(org)["documents"])}

    async def create_document(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        title = str(body.get("title") or "").strip()
        if not title:
            return {"ok": False, "error": "validation", "message_ru": "Укажите название документа"}
        content = str(body.get("content") or body.get("body") or "")
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest() if content else None
        storage_ref = body.get("storage_ref") or f"legal-ops://{org}/{uuid.uuid4().hex}"
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "client_id": body.get("client_id"),
            "case_id": body.get("case_id"),
            "contract_id": body.get("contract_id"),
            "title": title,
            "doc_type": body.get("doc_type") or "general",
            "storage_ref": storage_ref,
            "content_hash": content_hash,
            "status": body.get("status") or "uploaded",
            "description": body.get("description"),
            "document_date": body.get("document_date"),
            "uploaded_by": body.get("uploaded_by") or role,
            "tags": body.get("tags") if not isinstance(body.get("tags"), str) else [x.strip() for x in str(body.get("tags")).split(",") if x.strip()],
            "payload": {"content_preview": content[:500], **(body.get("payload") or {})},
            "created_at": _now(),
        }
        if content and isinstance(item["payload"], dict) and "content" not in item["payload"]:
            item["payload"]["content"] = content
        saved = await self._persist("document", item)
        self._bag(org)["documents"].insert(0, saved)
        act = "document_ai_draft" if item.get("status") == "ai_draft" else "document_uploaded"
        await self._activity(
            organization_id=org,
            entity_type="document",
            entity_id=saved["id"],
            action=act,
            summary=f"{'AI Draft создан' if act == 'document_ai_draft' else 'Документ загружен'}: {title}",
            role=role,
        )
        return {"ok": True, "item": saved}

    async def list_tasks(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        return {"ok": True, "items": active_only(self._bag(org)["tasks"])}

    async def create_task(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        title = str(body.get("title") or "").strip()
        if not title:
            return {"ok": False, "error": "validation", "message_ru": "Укажите задачу / срок"}
        kind = str(body.get("kind") or "task")
        status = str(body.get("status") or "new")
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "case_id": body.get("case_id"),
            "client_id": body.get("client_id"),
            "contract_id": body.get("contract_id"),
            "title": title,
            "kind": kind,
            "status": status,
            "due_at": body.get("due_at"),
            "assignee": body.get("assignee"),
            "description": body.get("description"),
            "priority": body.get("priority") or "normal",
            "reminder_minutes": _as_int(body.get("reminder_minutes")),
            "payload": body.get("payload") or {},
            "created_at": _now(),
        }
        saved = await self._persist("task", item)
        self._bag(org)["tasks"].insert(0, saved)
        action = "deadline_changed" if kind == "deadline" else "task_created"
        await self._activity(
            organization_id=org,
            entity_type="task",
            entity_id=saved["id"],
            action=action,
            summary=f"{'Срок' if kind == 'deadline' else 'Задача'}: {title}",
            role=role,
        )
        await self.ensure_linked_calendar(org, "task", saved, role)
        return {"ok": True, "item": saved}

    async def complete_task(self, organization_id: str, task_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        items = self._bag(org)["tasks"]
        idx = next((i for i, t in enumerate(items) if t.get("id") == task_id), None)
        if idx is None:
            return {"ok": False, "error": "not_found", "message_ru": "Задача не найдена"}
        cur = dict(items[idx])
        cur["status"] = "done"
        cur["completed_at"] = _now()
        cur["updated_at"] = _now()
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = LegalOpsRepository(session)
                row = await repo.get_task(org, task_id)
                if row:
                    await repo.update_task(row, {"status": "done", "completed_at": cur["completed_at"]})
                    cur = row_to_dict(row)
        except Exception as exc:
            logger.warning("task complete persist skipped: %s", exc)
        items[idx] = cur
        await self._activity(
            organization_id=org,
            entity_type="task",
            entity_id=task_id,
            action="task_completed",
            summary=f"Задача выполнена: {cur.get('title')}",
            role=role,
        )
        return {"ok": True, "item": cur}

    async def list_hearings(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        return {"ok": True, "items": active_only(self._bag(org)["hearings"])}

    async def create_hearing(self, organization_id: str, body: dict[str, Any], role: str | None = None) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        title = str(body.get("title") or "").strip()
        if not title:
            return {"ok": False, "error": "validation", "message_ru": "Укажите название заседания"}
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "case_id": body.get("case_id"),
            "title": title,
            "court_name": body.get("court_name"),
            "scheduled_at": body.get("scheduled_at"),
            "ends_at": body.get("ends_at"),
            "status": body.get("status") or "scheduled",
            "location": body.get("location"),
            "court_case_number": body.get("court_case_number"),
            "judge": body.get("judge"),
            "room": body.get("room"),
            "hearing_format": body.get("hearing_format") or "in_person",
            "video_url": body.get("video_url"),
            "description": body.get("description"),
            "result": body.get("result"),
            "notes": body.get("notes"),
            "payload": body.get("payload") or {},
            "created_at": _now(),
        }
        saved = await self._persist("hearing", item)
        self._bag(org)["hearings"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="hearing",
            entity_id=saved["id"],
            action="hearing_created",
            summary=f"Заседание создано: {title}",
            role=role,
        )
        await self.ensure_linked_calendar(org, "hearing", saved, role)
        return {"ok": True, "item": saved}

    async def list_calendar(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        return {"ok": True, "items": active_only(self._bag(org)["calendar"]), "google_calendar": self.gcal_status()}

    async def create_calendar_event(
        self, organization_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        title = str(body.get("title") or "").strip()
        if not title:
            return {"ok": False, "error": "validation", "message_ru": "Укажите название события"}
        dedupe = body.get("dedupe_key") or gcal.make_dedupe_key(
            organization_id=org,
            title=title,
            starts_at=str(body.get("starts_at") or ""),
            case_id=body.get("case_id"),
        )
        # Duplicate prevention (memory + DB)
        existing = next((e for e in self._bag(org)["calendar"] if e.get("dedupe_key") == dedupe), None)
        if existing:
            return {
                "ok": False,
                "error": "duplicate",
                "message_ru": "Событие календаря уже существует (защита от дублей)",
                "item": existing,
            }
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = LegalOpsRepository(session)
                db_hit = await repo.find_calendar_by_dedupe(org, dedupe)
                if db_hit:
                    d = row_to_dict(db_hit)
                    return {
                        "ok": False,
                        "error": "duplicate",
                        "message_ru": "Событие календаря уже существует (защита от дублей)",
                        "item": d,
                    }
        except Exception:
            pass

        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "case_id": body.get("case_id"),
            "hearing_id": body.get("hearing_id"),
            "title": title,
            "starts_at": body.get("starts_at"),
            "ends_at": body.get("ends_at"),
            "dedupe_key": dedupe,
            "gcal_event_id": None,
            "sync_status": "local",
            "payload": body.get("payload") or {},
            "event_type": body.get("event_type") or "other",
            "all_day": bool(body.get("all_day")),
            "client_id": body.get("client_id"),
            "contract_id": body.get("contract_id"),
            "task_id": body.get("task_id"),
            "responsible_user_id": body.get("responsible_user_id"),
            "location": body.get("location"),
            "description": body.get("description"),
            "reminder_minutes": _as_int(body.get("reminder_minutes")),
            "source_kind": body.get("source_kind"),
            "source_id": body.get("source_id"),
            "created_at": _now(),
        }
        sync = False
        if body.get("sync_google"):
            denied_sync = require(role, "sync")
            if denied_sync:
                return denied_sync
            sync_res = gcal.sync_event_to_google(item)
            item["sync_status"] = sync_res.get("sync_status") or "local"
            item["gcal_event_id"] = sync_res.get("gcal_event_id")
            sync = True
            if sync_res.get("gcal_event_id"):
                # Also prevent duplicate gcal ids
                dup_g = next(
                    (e for e in self._bag(org)["calendar"] if e.get("gcal_event_id") == sync_res["gcal_event_id"]),
                    None,
                )
                if dup_g:
                    return {
                        "ok": False,
                        "error": "duplicate",
                        "message_ru": "Google Calendar event id уже связан (защита от дублей)",
                        "item": dup_g,
                    }

        try:
            saved = await self._persist("calendar", item)
        except Exception as exc:
            msg = str(exc).lower()
            if "uq_legal_ops_cal" in msg or "unique" in msg or "duplicate" in msg:
                return {
                    "ok": False,
                    "error": "duplicate",
                    "message_ru": "Событие календаря уже существует (защита от дублей)",
                }
            raise
        self._bag(org)["calendar"].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type="calendar",
            entity_id=saved["id"],
            action="calendar_sync" if sync else "calendar_event_created",
            summary=f"Событие календаря: {title}",
            role=role,
        )
        return {"ok": True, "item": saved, "google_calendar": self.gcal_status()}

    async def sync_calendar(self, organization_id: str, event_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "sync")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        items = self._bag(org)["calendar"]
        idx = next((i for i, e in enumerate(items) if e.get("id") == event_id), None)
        if idx is None:
            return {"ok": False, "error": "not_found", "message_ru": "Событие не найдено"}
        cur = dict(items[idx])
        sync_res = gcal.sync_event_to_google(cur)
        if sync_res.get("gcal_event_id"):
            dup = next(
                (
                    e
                    for e in items
                    if e.get("gcal_event_id") == sync_res["gcal_event_id"] and e.get("id") != event_id
                ),
                None,
            )
            if dup:
                return {
                    "ok": False,
                    "error": "duplicate",
                    "message_ru": "Google Calendar event id уже связан (защита от дублей)",
                    "item": dup,
                }
        cur["sync_status"] = sync_res.get("sync_status")
        cur["gcal_event_id"] = sync_res.get("gcal_event_id")
        items[idx] = cur
        await self._activity(
            organization_id=org,
            entity_type="calendar",
            entity_id=event_id,
            action="calendar_sync",
            summary=str(sync_res.get("message_ru") or "calendar sync"),
            role=role,
            payload=sync_res,
        )
        return {"ok": bool(sync_res.get("ok")), "item": cur, "sync": sync_res, "google_calendar": self.gcal_status()}

    async def list_activity(
        self,
        organization_id: str,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        role: str | None = None,
    ) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        items = self._bag(org)["activity"]
        if entity_type:
            items = [a for a in items if a.get("entity_type") == entity_type]
        if entity_id:
            items = [a for a in items if a.get("entity_id") == entity_id]
        return {"ok": True, "items": items}

_SVC: LegalOpsService | None = None


def get_legal_ops_service() -> LegalOpsService:
    global _SVC
    if _SVC is None:
        _SVC = LegalOpsService()
    return _SVC


def reset_legal_ops_for_tests() -> None:
    global _SVC
    _SVC = None
