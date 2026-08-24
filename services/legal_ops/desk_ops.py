"""Sprint 51.1 — update/archive/restore, files, calendar links, inbox, reminders."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from repositories.legal_ops_repository import LegalOpsRepository, row_to_dict
from services.legal_ops import files as file_store
from services.legal_ops.calendar_integration import get_calendar_integration
from services.legal_ops.rbac import require

logger = logging.getLogger(__name__)

KIND_BAG = {
    "client": "clients",
    "case": "cases",
    "contract": "contracts",
    "document": "documents",
    "task": "tasks",
    "hearing": "hearings",
    "calendar": "calendar",
    "file": "files",
    "ai_analysis": "ai_analyses",
    "watchlist": "watchlist",
    "monitor_change": "monitor_changes",
    "enforcement": "enforcement",
}

CASE_FIELDS = (
    "title",
    "case_number",
    "court_case_number",
    "case_type",
    "status",
    "client_id",
    "responsible",
    "participants",
    "court",
    "judge",
    "opened_at",
    "closed_at",
    "deadline_at",
    "notes",
    "description",
    "priority",
    "practice_area",
    "payload",
)

CONTRACT_FIELDS = (
    "title",
    "contract_number",
    "contract_type",
    "client_id",
    "case_id",
    "counterparty",
    "responsible",
    "status",
    "approval_status",
    "signing_status",
    "start_at",
    "end_at",
    "deadline_at",
    "contract_date",
    "amount",
    "currency",
    "notes",
    "body",
    "payload",
)

CALENDAR_FIELDS = (
    "title",
    "event_type",
    "starts_at",
    "ends_at",
    "all_day",
    "client_id",
    "case_id",
    "contract_id",
    "task_id",
    "hearing_id",
    "responsible_user_id",
    "location",
    "description",
    "reminder_minutes",
    "payload",
)

CLIENT_FIELDS = (
    "name",
    "email",
    "phone",
    "status",
    "notes",
    "payload",
    "client_type",
    "avatar_file_id",
    "address",
    "city",
    "country",
    "company",
    "position",
    "responsible",
    "source",
    "identity_data",
    "tags",
    "contacts",
)
DOCUMENT_FIELDS = (
    "title",
    "doc_type",
    "client_id",
    "case_id",
    "contract_id",
    "status",
    "description",
    "document_date",
    "uploaded_by",
    "tags",
    "payload",
)
TASK_FIELDS = (
    "title",
    "kind",
    "status",
    "due_at",
    "assignee",
    "case_id",
    "client_id",
    "contract_id",
    "description",
    "priority",
    "reminder_minutes",
    "completed_at",
    "payload",
)
HEARING_FIELDS = (
    "title",
    "court_name",
    "scheduled_at",
    "ends_at",
    "status",
    "location",
    "case_id",
    "court_case_number",
    "judge",
    "room",
    "hearing_format",
    "video_url",
    "description",
    "result",
    "notes",
    "payload",
)
FILE_FIELDS = (
    "filename",
    "mime_type",
    "size",
    "storage_path",
    "description",
    "file_version",
    "entity_type",
    "entity_id",
    "inbox_status",
    "uploaded_by",
    "payload",
)
AI_ANALYSIS_FIELDS = (
    "workspace_kind",
    "action",
    "mode",
    "target_type",
    "target_id",
    "client_id",
    "case_id",
    "question",
    "result",
    "sources",
    "context_snapshot",
    "provider_meta",
    "created_tasks",
    "created_events",
    "created_documents",
    "actor_role",
    "actor_id",
    "status",
    "payload",
)
WATCHLIST_FIELDS = (
    "case_id",
    "client_id",
    "entity_kind",
    "external_case_number",
    "provider",
    "status",
    "last_checked_at",
    "last_success_at",
    "next_check_at",
    "last_error",
    "fingerprint",
    "normalized_state",
    "automation",
    "payload",
    "title",
    "source_url",
    "check_frequency",
    "comment",
    "counterparty",
    "decision_ref",
    "enforcement_id",
    "active",
)
MONITOR_CHANGE_FIELDS = (
    "watchlist_id",
    "case_id",
    "client_id",
    "change_type",
    "title",
    "detail",
    "dedupe_key",
    "provider",
    "source_label",
    "read_at",
    "payload",
    "workflow_status",
    "summary",
    "old_fingerprint",
    "new_fingerprint",
    "source_reference",
    "enforcement_id",
    "suggestions",
)
ENFORCEMENT_FIELDS = (
    "production_number",
    "client_id",
    "case_id",
    "debtor",
    "creditor",
    "executor",
    "status",
    "opened_at",
    "last_checked_at",
    "notes",
    "provider",
    "payload",
)

FIELDS = {
    "client": CLIENT_FIELDS,
    "case": CASE_FIELDS,
    "contract": CONTRACT_FIELDS,
    "document": DOCUMENT_FIELDS,
    "task": TASK_FIELDS,
    "hearing": HEARING_FIELDS,
    "calendar": CALENDAR_FIELDS,
    "file": FILE_FIELDS,
    "ai_analysis": AI_ANALYSIS_FIELDS,
    "watchlist": WATCHLIST_FIELDS,
    "monitor_change": MONITOR_CHANGE_FIELDS,
    "enforcement": ENFORCEMENT_FIELDS,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_archived(item: dict[str, Any]) -> bool:
    return bool(item.get("archived_at"))


def active_only(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [i for i in items if not is_archived(i)]


class LegalOpsDeskMixin:
    async def _patch_mem(self, org: str, kind: str, item_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        bag = self._bag(org)[KIND_BAG[kind]]  # type: ignore[attr-defined]
        idx = next((i for i, x in enumerate(bag) if str(x.get("id")) == str(item_id)), None)
        if idx is None:
            return None
        cur = dict(bag[idx])
        cur.update(patch)
        cur["updated_at"] = _now()
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = LegalOpsRepository(session)
                getter = {
                    "client": repo.get_client,
                    "case": repo.get_case,
                    "contract": repo.get_contract,
                    "document": repo.get_document,
                    "task": repo.get_task,
                    "hearing": repo.get_hearing,
                    "calendar": repo.get_calendar,
                    "file": repo.get_file,
                    "ai_analysis": repo.get_ai_analysis,
                    "watchlist": repo.get_watchlist,
                    "monitor_change": repo.get_monitor_change,
                    "enforcement": repo.get_enforcement,
                }[kind]
                row = await getter(org, item_id)
                if row:
                    keys = FIELDS.get(kind, ()) + (
                        "archived_at",
                        "archived_by",
                        "archive_reason",
                        "inbox_status",
                        "entity_type",
                        "entity_id",
                        "file_version",
                        "description",
                        "external_event_id",
                        "external_provider",
                        "gcal_event_id",
                        "sync_status",
                    )
                    await repo.update_row(row, patch, keys)
                    db = row_to_dict(row)
                    db.update(patch)
                    db["updated_at"] = cur["updated_at"]
                    cur = db
                else:
                    logger.warning("legal_ops patch: %s %s missing in postgres", kind, item_id)
        except Exception as exc:
            logger.warning("legal_ops patch failed kind=%s id=%s: %s", kind, item_id, exc)
        bag[idx] = cur
        return cur

    async def get_entity(self, organization_id: str, kind: str, item_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        item = next((x for x in self._bag(org)[KIND_BAG[kind]] if str(x.get("id")) == str(item_id)), None)  # type: ignore[attr-defined]
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Объект не найден"}
        files = [f for f in self._bag(org).get("files", []) if str(f.get("entity_id")) == str(item_id) and not is_archived(f)]  # type: ignore[attr-defined]
        activity = [a for a in self._bag(org)["activity"] if str(a.get("entity_id")) == str(item_id)]  # type: ignore[attr-defined]
        return {"ok": True, "item": item, "files": files, "activity": activity}

    RELATED_KINDS = ("client", "case", "contract", "document", "task", "hearing")

    async def related_bundle(
        self, organization_id: str, kind: str, item_id: str, role: str | None = None
    ) -> dict[str, Any]:
        """Linked CRM subgraph (detail drawers / cross-linking, Lawyer 3.6)."""
        denied = require(role, "get")
        if denied:
            return denied
        if kind not in self.RELATED_KINDS:
            return {"ok": False, "error": "validation", "message_ru": "Связки доступны для client/case/contract/document/task/hearing"}
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        bag = self._bag(org)  # type: ignore[attr-defined]
        base = next((x for x in bag.get(KIND_BAG[kind], []) if str(x.get("id")) == str(item_id)), None)
        if not base:
            return {"ok": False, "error": "not_found", "message_ru": "Объект не найден"}

        # anchors: which client/case ids this entity connects through
        client_ids: set[str] = set()
        case_ids: set[str] = set()
        if kind == "client":
            client_ids.add(str(item_id))
        elif kind == "case":
            case_ids.add(str(item_id))
            if base.get("client_id"):
                client_ids.add(str(base["client_id"]))
        else:
            if base.get("case_id"):
                case_ids.add(str(base["case_id"]))
            if base.get("client_id"):
                client_ids.add(str(base["client_id"]))

        def anchored(rows: list[dict[str, Any]], *, use_client: bool = True) -> list[dict[str, Any]]:
            return active_only(
                [
                    r
                    for r in rows
                    if str(r.get("case_id") or "") in case_ids
                    or (use_client and str(r.get("client_id") or "") in client_ids)
                ]
            )

        if kind == "client":
            cases = anchored(bag["cases"])
            case_ids |= {str(c["id"]) for c in cases}
        else:
            cases = active_only([c for c in bag["cases"] if str(c.get("id")) in case_ids])

        # resolve owner clients through the case when the entity itself has no client_id
        owner_client_ids = client_ids | {str(c.get("client_id")) for c in cases if c.get("client_id")}
        clients = active_only([c for c in bag["clients"] if str(c.get("id")) in owner_client_ids])
        contracts = anchored(bag["contracts"])
        documents = anchored(bag["documents"])
        tasks = anchored(bag["tasks"])
        hearings = anchored(bag["hearings"], use_client=False)
        calendar = anchored(bag["calendar"])
        monitoring = anchored(bag.get("watchlist", []))
        changes = anchored(bag.get("monitor_changes", []))
        ai = anchored(bag.get("ai_analyses", []))

        # exclude the base object from its own related lists
        def without_self(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
            return [r for r in rows if str(r.get("id")) != str(item_id)]

        files = active_only(
            [
                f
                for f in bag.get("files", [])
                if (str(f.get("entity_type") or "") == kind and str(f.get("entity_id")) == str(item_id))
                or str(f.get("entity_id")) == str(item_id)
            ]
        )
        activity = [a for a in bag["activity"] if str(a.get("entity_id")) == str(item_id)]

        def uniq(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
            seen: set[str] = set()
            out = []
            for r in rows:
                rid = str(r.get("id"))
                if rid in seen:
                    continue
                seen.add(rid)
                out.append(r)
            return out

        return {
            "ok": True,
            "item": base,
            "related": {
                "clients": uniq(without_self(clients) if kind == "client" else clients),
                "cases": uniq(without_self(cases) if kind == "case" else cases),
                "contracts": uniq(without_self(contracts) if kind == "contract" else contracts),
                "documents": uniq(without_self(documents) if kind == "document" else documents),
                "tasks": uniq(without_self(tasks) if kind == "task" else tasks),
                "hearings": uniq(without_self(hearings) if kind == "hearing" else hearings),
                "calendar": uniq(calendar),
                "monitoring": uniq(monitoring),
                "changes": uniq(changes),
                "files": files,
                "activity": activity,
                "ai": uniq(ai) or [a for a in activity if a.get("action") == "ai_analysis_executed"],
            },
        }

    def filter_items(self, items: list[dict[str, Any]], query: dict[str, str]) -> list[dict[str, Any]]:
        q = (query.get("q") or "").strip().lower()
        out = items
        if q:
            out = [
                i
                for i in out
                if q in str(i.get("name") or "").lower()
                or q in str(i.get("title") or "").lower()
                or q in str(i.get("email") or "").lower()
                or q in str(i.get("phone") or "").lower()
                or q in str(i.get("tags") or "").lower()
            ]
        for key in ("status", "client_type", "type", "responsible", "priority", "kind", "event_type"):
            val = (query.get(key) or "").strip()
            if not val:
                continue
            field = "client_type" if key == "type" else key
            out = [i for i in out if str(i.get(field) or "") == val]
        tag = (query.get("tag") or "").strip().lower()
        if tag:
            out = [
                i
                for i in out
                if tag in [str(t).lower() for t in (i.get("tags") or [] if isinstance(i.get("tags"), list) else str(i.get("tags") or "").split(","))]
            ]
        return out

    async def update_entity(
        self, organization_id: str, kind: str, item_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        allowed = set(FIELDS.get(kind, ()))
        patch = {k: body[k] for k in allowed if k in body}
        for json_key in ("tags", "contacts", "participants"):
            if json_key in patch and isinstance(patch[json_key], str):
                patch[json_key] = [x.strip() for x in patch[json_key].split(",") if x.strip()]
        if "reminder_minutes" in patch:
            try:
                patch["reminder_minutes"] = int(patch["reminder_minutes"]) if patch["reminder_minutes"] not in (None, "") else None
            except (TypeError, ValueError):
                patch["reminder_minutes"] = None
        if kind == "case" and "deadline_at" in patch:
            payload = dict(patch.get("payload") or {})
            if not payload:
                existing = next(
                    (x for x in self._bag(org)[KIND_BAG[kind]] if str(x.get("id")) == str(item_id)),  # type: ignore[attr-defined]
                    {},
                )
                payload = dict(existing.get("payload") or {})
            payload["deadline_at"] = patch["deadline_at"]
            patch["payload"] = payload
        if not patch:
            return {"ok": False, "error": "validation", "message_ru": "Нет полей для обновления"}
        saved = await self._patch_mem(org, kind, item_id, patch)
        if not saved:
            return {"ok": False, "error": "not_found", "message_ru": "Объект не найден"}
        action = "status_changed" if "status" in patch or "approval_status" in patch else "edited"
        if kind == "calendar":
            action = "calendar_event_changed"
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type=kind,
            entity_id=item_id,
            action=action,
            summary=f"{kind} изменён",
            role=role,
            payload={"patch": list(patch.keys())},
        )
        if kind == "calendar":
            await self._maybe_sync_google(org, saved, "update", role)
        if kind in {"task", "contract", "hearing", "case"}:
            await self.ensure_linked_calendar(org, kind, saved, role)
        return {"ok": True, "item": saved}

    async def archive_entity(
        self,
        organization_id: str,
        kind: str,
        item_id: str,
        role: str | None = None,
        reason: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        patch = {"archived_at": _now(), "archived_by": actor_id or role, "archive_reason": reason}
        saved = await self._patch_mem(org, kind, item_id, patch)
        if not saved:
            return {"ok": False, "error": "not_found", "message_ru": "Объект не найден"}
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type=kind,
            entity_id=item_id,
            action="archived",
            summary=f"{kind} перемещён в архив",
            role=role,
        )
        if kind == "calendar":
            await self._maybe_sync_google(org, saved, "delete", role)
        return {"ok": True, "item": saved}

    async def restore_entity(self, organization_id: str, kind: str, item_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        saved = await self._patch_mem(org, kind, item_id, {"archived_at": None, "archived_by": None, "archive_reason": None})
        if not saved:
            return {"ok": False, "error": "not_found", "message_ru": "Объект не найден"}
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type=kind,
            entity_id=item_id,
            action="restored",
            summary=f"{kind} восстановлен из архива",
            role=role,
        )
        return {"ok": True, "item": saved}

    async def list_archive(self, organization_id: str, role: str | None = None, kind: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        kinds = (
            [kind]
            if kind
            else ["case", "contract", "document", "calendar", "client", "task", "hearing", "file", "enforcement", "watchlist", "ai_analysis"]
        )
        items: list[dict[str, Any]] = []
        for k in kinds:
            bag = self._bag(org).get(KIND_BAG[k], [])  # type: ignore[attr-defined]
            for row in bag:
                if is_archived(row):
                    items.append({**row, "entity_kind": k})
        return {"ok": True, "items": items}

    async def upload_file(
        self,
        organization_id: str,
        *,
        filename: str,
        mime_type: str | None,
        data: bytes,
        entity_type: str | None,
        entity_id: str | None,
        description: str | None,
        role: str | None,
        uploaded_by: str | None,
    ) -> dict[str, Any]:
        denied = require(role, "create")
        if denied:
            return denied
        err = file_store.validate_upload(filename, mime_type)
        if err:
            return err
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        file_id = str(uuid.uuid4())
        path = file_store.write_bytes(org, file_id, data)
        inbox = "unlinked" if not entity_id else "linked"
        item = {
            "id": file_id,
            "organization_id": org,
            "tenant_id": org,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "filename": filename,
            "mime_type": mime_type,
            "size": len(data),
            "storage_path": path,
            "description": description,
            "file_version": 1,
            "uploaded_by": uploaded_by or role,
            "inbox_status": inbox,
            "created_at": _now(),
        }
        saved = await self._persist("file", item)  # type: ignore[attr-defined]
        self._bag(org).setdefault("files", []).insert(0, saved)  # type: ignore[attr-defined]
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type=entity_type or "inbox",
            entity_id=entity_id or file_id,
            action="file_uploaded",
            summary=f"Файл загружен: {filename}",
            role=role,
        )
        return {"ok": True, "item": saved}

    async def replace_file(
        self, organization_id: str, file_id: str, filename: str, mime_type: str | None, data: bytes, role: str | None
    ) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        err = file_store.validate_upload(filename, mime_type)
        if err:
            return err
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        cur = next((x for x in self._bag(org).get("files", []) if str(x.get("id")) == file_id), None)  # type: ignore[attr-defined]
        if not cur:
            return {"ok": False, "error": "not_found", "message_ru": "Файл не найден"}
        path = file_store.write_bytes(org, file_id, data)
        patch = {
            "filename": filename,
            "mime_type": mime_type,
            "size": len(data),
            "storage_path": path,
            "file_version": int(cur.get("file_version") or 1) + 1,
        }
        saved = await self._patch_mem(org, "file", file_id, patch)
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type=str(cur.get("entity_type") or "file"),
            entity_id=str(cur.get("entity_id") or file_id),
            action="file_replaced",
            summary=f"Версия файла заменена: {filename}",
            role=role,
        )
        return {"ok": True, "item": saved}

    async def link_file(
        self, organization_id: str, file_id: str, entity_type: str, entity_id: str, role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        allowed = {
            "client",
            "case",
            "contract",
            "document",
            "task",
            "hearing",
            "enforcement",
            "ai_analysis",
            "calendar",
            "inbox",
        }
        et = str(entity_type or "").strip()
        eid = str(entity_id or "").strip()
        if et not in allowed or not eid:
            return {
                "ok": False,
                "error": "validation",
                "message_ru": "Укажите допустимый тип объекта и идентификатор для привязки файла",
            }
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        saved = await self._patch_mem(
            org, "file", file_id, {"entity_type": et, "entity_id": eid, "inbox_status": "linked"}
        )
        if not saved:
            return {"ok": False, "error": "not_found", "message_ru": "Файл не найден"}
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="file",
            entity_id=file_id,
            action="FILE_RELINKED",
            summary=f"Файл привязан к {et}",
            role=role,
            payload={"entity_type": et, "entity_id": eid},
        )
        return {"ok": True, "item": saved}

    async def rename_file(
        self, organization_id: str, file_id: str, filename: str, role: str | None = None
    ) -> dict[str, Any]:
        denied = require(role, "update")
        if denied:
            return denied
        name = str(filename or "").strip()
        if not name or len(name) > 512:
            return {"ok": False, "error": "validation", "message_ru": "Укажите корректное имя файла"}
        err = file_store.validate_upload(name, None)
        if err:
            return err
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        saved = await self._patch_mem(org, "file", file_id, {"filename": name})
        if not saved:
            return {"ok": False, "error": "not_found", "message_ru": "Файл не найден"}
        await self._activity(  # type: ignore[attr-defined]
            organization_id=org,
            entity_type="file",
            entity_id=file_id,
            action="FILE_RENAMED",
            summary=f"Файл переименован: {name}",
            role=role,
        )
        return {"ok": True, "item": saved}

    async def list_files(self, organization_id: str, role: str | None = None, **filters: Any) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        items = active_only(self._bag(org).get("files", []))  # type: ignore[attr-defined]
        et, eid, inbox = filters.get("entity_type"), filters.get("entity_id"), filters.get("inbox_status")
        if et:
            items = [x for x in items if x.get("entity_type") == et]
        if eid:
            items = [x for x in items if str(x.get("entity_id")) == str(eid)]
        if inbox:
            items = [x for x in items if x.get("inbox_status") == inbox]
        return {"ok": True, "items": items}

    async def list_inbox(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        return await self.list_files(organization_id, role, inbox_status="unlinked")

    async def file_bytes(self, organization_id: str, file_id: str, role: str | None = None) -> tuple[dict[str, Any] | None, bytes | None]:
        denied = require(role, "get")
        if denied:
            return denied, None
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        item = next((x for x in self._bag(org).get("files", []) if str(x.get("id")) == file_id), None)  # type: ignore[attr-defined]
        if not item:
            return {"ok": False, "error": "not_found"}, None
        data = file_store.read_bytes(str(item.get("storage_path") or ""))
        return item, data

    async def ensure_linked_calendar(
        self, organization_id: str, kind: str, source: dict[str, Any], role: str | None
    ) -> dict[str, Any] | None:
        """Create a canonical calendar event for hearings/deadlines/contract ends without duplicates."""
        org = organization_id
        source_id = str(source.get("id") or "")
        if kind == "hearing":
            event_type, starts, title = "hearing", source.get("scheduled_at"), source.get("title")
            source_kind = "hearing"
        elif kind == "task" and str(source.get("kind")) == "deadline":
            event_type, starts, title = "deadline", source.get("due_at"), source.get("title")
            source_kind = "deadline"
        elif kind == "contract" and (source.get("deadline_at") or source.get("end_at")):
            event_type, starts, title = "contract_end", source.get("deadline_at") or source.get("end_at"), source.get("title")
            source_kind = "contract_end"
        elif kind == "case" and (
            source.get("deadline_at") or (source.get("payload") or {}).get("deadline_at")
        ):
            event_type = "deadline"
            starts = source.get("deadline_at") or (source.get("payload") or {}).get("deadline_at")
            title = source.get("title")
            source_kind = "case_deadline"
        else:
            return None
        if not starts:
            return None
        existing = next(
            (
                e
                for e in self._bag(org)["calendar"]  # type: ignore[attr-defined]
                if e.get("source_kind") == source_kind and str(e.get("source_id")) == source_id and not is_archived(e)
            ),
            None,
        )
        if existing:
            return existing
        body = {
            "title": title,
            "event_type": event_type,
            "starts_at": starts,
            "ends_at": starts,
            "case_id": source.get("case_id"),
            "client_id": source.get("client_id"),
            "contract_id": source.get("id") if kind == "contract" else source.get("contract_id"),
            "task_id": source.get("id") if kind == "task" else None,
            "hearing_id": source.get("id") if kind == "hearing" else None,
            "source_kind": source_kind,
            "source_id": source_id,
            "dedupe_key": f"{org}|{source_kind}|{source_id}",
        }
        return await self.create_calendar_event(org, body, role)  # type: ignore[attr-defined]

    async def _maybe_sync_google(self, org: str, event: dict[str, Any], op: str, role: str | None) -> dict[str, Any]:
        integ = get_calendar_integration()
        adapter = integ.google
        if op == "create":
            res = adapter.create_event(event)
        elif op == "update":
            res = adapter.update_event(event)
        else:
            res = adapter.delete_event(event)
        if res.get("ok") and event.get("id"):
            patch = {
                "sync_status": res.get("sync_status"),
                "gcal_event_id": res.get("gcal_event_id") or res.get("external_event_id"),
                "external_event_id": res.get("external_event_id") or res.get("gcal_event_id"),
                "external_provider": "google",
            }
            await self._patch_mem(org, "calendar", str(event["id"]), patch)
            await self._activity(  # type: ignore[attr-defined]
                organization_id=org,
                entity_type="calendar",
                entity_id=str(event["id"]),
                action="calendar_synced",
                summary=str(res.get("message_ru") or "calendar sync"),
                role=role,
                payload=res,
            )
        return res

    def integrations_catalog(self) -> dict[str, Any]:
        return {"ok": True, "items": get_calendar_integration().catalog()}

    async def list_reminders(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = organization_id
        await self.ensure_hydrated(org)  # type: ignore[attr-defined]
        now = datetime.now(timezone.utc)
        due = []
        for ev in active_only(self._bag(org)["calendar"]):  # type: ignore[attr-defined]
            mins = ev.get("reminder_minutes")
            starts = ev.get("starts_at")
            if not mins or not starts:
                continue
            try:
                st = datetime.fromisoformat(str(starts).replace("Z", "+00:00"))
            except ValueError:
                continue
            delta = (st - now).total_seconds() / 60
            if 0 <= delta <= int(mins) + 1:
                due.append(ev)
        return {"ok": True, "items": due, "channel": "in_app"}
