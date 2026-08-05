"""Domain adapters — wrap existing SoR; no business-logic rewrite (34.2C)."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from platform_state.conversation import conversation_engine
from platform_state.events import (
    CalendarUpdatedEvent,
    ConversationUpdatedEvent,
    CrmUpdatedEvent,
    FileUploadedEvent,
    MemoryUpdatedEvent,
    NotificationCreatedEvent,
    PlatformStateChangedEvent,
    TaskCompletedEvent,
    TaskCreatedEvent,
    WorkspaceChangedEvent,
)
from platform_state.memory_store import memory_adapter
from platform_state.models import EntityMeta, compute_revision, utcnow
from platform_state.sync_engine import sync_engine
from platform_state.version_engine import version_engine

logger = logging.getLogger(__name__)


class _EntityVersions:
    """34.2C-compatible facade over VersionEngine (TD-54)."""

    def key(self, entity_type: str, entity_id: str) -> str:
        return version_engine.key(entity_type, entity_id)

    def get(self, entity_type: str, entity_id: str) -> EntityMeta:
        return version_engine.meta(entity_type, entity_id)

    def bump(
        self,
        entity_type: str,
        entity_id: str,
        *,
        updated_by: str | None = None,
        source_client: str | None = None,
    ) -> EntityMeta:
        return version_engine.bump_compat(
            entity_type,
            entity_id,
            updated_by=updated_by,
            source_client=source_client,
        )

    @property
    def _meta(self) -> dict[str, EntityMeta]:
        # Compatibility for snapshot revision hashing
        return {
            k: EntityMeta(
                entity_type=v.entity_type,
                entity_id=v.id,
                version=v.version,
                updated_at=v.updated_at,
                updated_by=v.updated_by,
                source_client=v.source_client,
            )
            for k, v in version_engine._heads.items()
        }

    def reset(self) -> None:
        version_engine.reset()


entity_versions = _EntityVersions()


# ---------------------------------------------------------------------------
# In-process notification / file / CRM / activity mirrors (unified center)
# ---------------------------------------------------------------------------


class NotificationStore:
    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    def add(self, item: dict[str, Any]) -> dict[str, Any]:
        self._items.append(item)
        return item

    def list(self, *, user_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        items = self._items
        if user_id:
            items = [i for i in items if i.get("user_id") == user_id or i.get("telegram_id")]
        return list(reversed(items[-limit:]))

    def snapshot(self, **kw: Any) -> dict[str, Any]:
        items = self.list(user_id=kw.get("user_id"), limit=100)
        return {"count": len(items), "notifications": items, "revision": compute_revision(len(self._items))}

    def reset(self) -> None:
        self._items.clear()


class FileStore:
    def __init__(self) -> None:
        self._files: dict[str, dict[str, Any]] = {}

    def upload(self, meta: dict[str, Any]) -> dict[str, Any]:
        fid = meta.get("file_id") or str(uuid.uuid4())
        row = {**meta, "file_id": fid, "uploaded_at": utcnow().isoformat()}
        self._files[fid] = row
        return row

    def list(self, *, conversation_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        items = list(self._files.values())
        if conversation_id:
            items = [f for f in items if f.get("conversation_id") == conversation_id]
        return items[-limit:]

    def snapshot(self, **kw: Any) -> dict[str, Any]:
        items = self.list(conversation_id=kw.get("conversation_id"), limit=100)
        return {"count": len(items), "files": items, "revision": compute_revision(sorted(self._files))}

    def reset(self) -> None:
        self._files.clear()


class CrmMirror:
    """Lightweight CRM projection for sync tests; delegates reads when DB available."""

    def __init__(self) -> None:
        self._leads: dict[str, dict[str, Any]] = {}
        self._deals: dict[str, dict[str, Any]] = {}
        self._contacts: dict[str, dict[str, Any]] = {}

    def upsert_lead(self, lead: dict[str, Any]) -> dict[str, Any]:
        lid = str(lead.get("id") or lead.get("lead_id") or uuid.uuid4())
        row = {**lead, "id": lid}
        self._leads[lid] = row
        return row

    def upsert_deal(self, deal: dict[str, Any]) -> dict[str, Any]:
        did = str(deal.get("id") or deal.get("deal_id") or uuid.uuid4())
        row = {**deal, "id": did}
        self._deals[did] = row
        return row

    def upsert_contact(self, contact: dict[str, Any]) -> dict[str, Any]:
        cid = str(contact.get("id") or contact.get("contact_id") or uuid.uuid4())
        row = {**contact, "id": cid}
        self._contacts[cid] = row
        return row

    def snapshot(self, **_kw: Any) -> dict[str, Any]:
        return {
            "leads": list(self._leads.values()),
            "deals": list(self._deals.values()),
            "contacts": list(self._contacts.values()),
            "revision": compute_revision(len(self._leads), len(self._deals), len(self._contacts)),
        }

    def reset(self) -> None:
        self._leads.clear()
        self._deals.clear()
        self._contacts.clear()


notification_store = NotificationStore()
file_store = FileStore()
crm_mirror = CrmMirror()

_activity: list[dict[str, Any]] = []
_favorites: dict[str, list[str]] = {}
_sessions: dict[str, dict[str, Any]] = {}


async def _publish(event: PlatformStateChangedEvent) -> dict[str, Any]:
    return await sync_engine.publish_change(event)


class TaskAdapter:
    """Wraps services.tasks.TaskService — publishes PlatformState events after writes."""

    async def create(
        self,
        *,
        title: str,
        creator_telegram_id: int,
        source_client: str = "api",
        description: str = "",
        module: str = "system",
        priority: str = "NORMAL",
        actor_id: str | None = None,
        skip_db: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        task_id: int | str | None = None
        if not skip_db:
            try:
                from services.tasks import TaskService

                task_id = TaskService.create(
                    task_type=kwargs.get("task_type", TaskService.HUMAN),
                    creator_id=creator_telegram_id,
                    title=title,
                    description=description,
                    module=module,
                    priority=priority,
                    assigned_user_id=kwargs.get("assigned_user_id"),
                    due_date=kwargs.get("due_date"),
                    project_id=kwargs.get("project_id"),
                )
            except Exception as exc:  # noqa: BLE001
                logger.debug("TaskAdapter DB create fallback: %s", exc)
        if not task_id:
            task_id = f"local-{uuid.uuid4().hex[:8]}"
        eid = str(task_id)
        meta = entity_versions.bump("task", eid, updated_by=actor_id, source_client=source_client)
        payload = {
            "task_id": eid,
            "title": title,
            "description": description,
            "module": module,
            "priority": priority,
            "creator_telegram_id": creator_telegram_id,
            "entity": meta.to_dict(),
        }
        await _publish(
            TaskCreatedEvent(
                entity_id=eid,
                revision=meta.updated_at,
                source_client=source_client,
                actor_id=actor_id,
                version=meta.version,
                payload=payload,
            )
        )
        _activity.append(
            {
                "type": "task_created",
                "entity_id": eid,
                "source_client": source_client,
                "at": utcnow().isoformat(),
            }
        )
        return payload

    async def complete(
        self,
        *,
        task_id: str | int,
        user_telegram_id: int,
        source_client: str = "api",
        actor_id: str | None = None,
        skip_db: bool = False,
    ) -> dict[str, Any]:
        ok = True
        if not skip_db:
            try:
                from services.tasks import TaskService

                ok = bool(TaskService.update_task_status(int(task_id), user_telegram_id, "DONE"))
            except Exception as exc:  # noqa: BLE001
                logger.debug("TaskAdapter complete fallback: %s", exc)
                ok = True
        eid = str(task_id)
        meta = entity_versions.bump("task", eid, updated_by=actor_id, source_client=source_client)
        payload = {"task_id": eid, "status": "DONE", "ok": ok, "entity": meta.to_dict()}
        await _publish(
            TaskCompletedEvent(
                entity_id=eid,
                revision=meta.updated_at,
                source_client=source_client,
                actor_id=actor_id,
                version=meta.version,
                payload=payload,
            )
        )
        return payload

    def snapshot(self, *, telegram_id: int | None = None, limit: int = 20) -> dict[str, Any]:
        rows: list[Any] = []
        if telegram_id is not None:
            try:
                from services.tasks import TaskService

                rows = TaskService.get_tasks_by_user(telegram_id, limit=limit) or []
            except Exception:  # noqa: BLE001
                rows = []
        return {
            "count": len(rows),
            "tasks": [{"raw": str(r)} for r in rows[:limit]],
            "revision": compute_revision(len(rows), entity_versions._meta),
        }


class CalendarAdapter:
    async def create_event(
        self,
        *,
        title: str,
        start_time: str,
        creator_telegram_id: int,
        source_client: str = "api",
        actor_id: str | None = None,
        skip_db: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        event_id: int | str | None = None
        if not skip_db:
            try:
                from services.calendar_service import CalendarService

                event_id = CalendarService.create_event(
                    creator_id=creator_telegram_id,
                    title=title,
                    start_time=start_time,
                    description=kwargs.get("description", ""),
                    module=kwargs.get("module", "system"),
                    event_type=kwargs.get("event_type", "general"),
                    remind_before=kwargs.get("remind_before", 0),
                )
            except Exception as exc:  # noqa: BLE001
                logger.debug("CalendarAdapter DB create fallback: %s", exc)
        if not event_id:
            event_id = f"local-{uuid.uuid4().hex[:8]}"
        eid = str(event_id)
        meta = entity_versions.bump("calendar_event", eid, updated_by=actor_id, source_client=source_client)
        payload = {
            "event_id": eid,
            "title": title,
            "start_time": start_time,
            "entity": meta.to_dict(),
        }
        await _publish(
            CalendarUpdatedEvent(
                entity_id=eid,
                revision=meta.updated_at,
                action="created",
                source_client=source_client,
                actor_id=actor_id,
                version=meta.version,
                payload=payload,
            )
        )
        return payload

    def snapshot(self, *, telegram_id: int | None = None, limit: int = 20) -> dict[str, Any]:
        rows: list[Any] = []
        if telegram_id is not None:
            try:
                from services.calendar_service import CalendarService

                rows = CalendarService.get_events_by_user(telegram_id, limit=limit) or []
            except Exception:  # noqa: BLE001
                rows = []
        return {"count": len(rows), "events": [{"raw": str(r)} for r in rows[:limit]], "revision": compute_revision(len(rows))}


class NotificationAdapter:
    async def create(
        self,
        *,
        title: str,
        body: str,
        user_id: str | None = None,
        telegram_id: int | None = None,
        source_client: str = "api",
        channel: str = "in_app",
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        nid = str(uuid.uuid4())
        meta = entity_versions.bump("notification", nid, updated_by=actor_id, source_client=source_client)
        item = {
            "notification_id": nid,
            "title": title,
            "body": body,
            "user_id": user_id,
            "telegram_id": telegram_id,
            "channel": channel,
            "source_client": source_client,
            "created_at": utcnow().isoformat(),
            "entity": meta.to_dict(),
        }
        notification_store.add(item)
        await _publish(
            NotificationCreatedEvent(
                entity_id=nid,
                revision=meta.updated_at,
                source_client=source_client,
                actor_id=actor_id,
                version=meta.version,
                payload=item,
            )
        )
        return item


class ConversationAdapter:
    async def ensure(
        self,
        *,
        source_client: str,
        external_id: str,
        user_id: str | None = None,
        telegram_id: int | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        conv = conversation_engine.get_or_create(
            user_id=user_id,
            telegram_id=telegram_id,
            workspace_id=workspace_id,
            source_client=source_client,
            external_id=external_id,
        )
        return conv.to_dict()

    async def append(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
        source_client: str,
        actor_id: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        msg = conversation_engine.append_message(
            conversation_id,
            role=role,
            content=content,
            source_client=source_client,
            attachments=attachments,
            actor_id=actor_id,
        )
        if attachments:
            for att in attachments:
                file_store.upload({**att, "conversation_id": conversation_id, "source_client": source_client})
        conv = conversation_engine.get(conversation_id)
        assert conv and conv.entity
        await _publish(
            ConversationUpdatedEvent(
                entity_id=conversation_id,
                revision=conv.entity.updated_at,
                source_client=source_client,
                actor_id=actor_id,
                version=conv.entity.version,
                payload={"message": msg.to_dict(), "conversation_id": conversation_id},
            )
        )
        return {"conversation": conv.to_dict(), "message": msg.to_dict()}


class MemoryFacadeAdapter:
    async def store(
        self,
        *,
        scope: str,
        scope_id: str,
        content: str,
        source_client: str = "ai",
        category: str = "general",
        actor_id: str | None = None,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        rec = memory_adapter.store(
            scope=scope,
            scope_id=scope_id,
            content=content,
            category=category,
            source_client=source_client,
            actor_id=actor_id,
        )
        if conversation_id:
            conversation_engine.add_memory_ref(conversation_id, rec.memory_id)
        assert rec.entity
        await _publish(
            MemoryUpdatedEvent(
                entity_id=rec.memory_id,
                revision=rec.entity.updated_at,
                source_client=source_client,
                actor_id=actor_id,
                version=rec.entity.version,
                payload=rec.to_dict(),
            )
        )
        return rec.to_dict()


class FileAdapter:
    async def upload(
        self,
        *,
        name: str,
        source_client: str,
        conversation_id: str | None = None,
        mime: str | None = None,
        actor_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = file_store.upload(
            {
                "name": name,
                "mime": mime,
                "conversation_id": conversation_id,
                "source_client": source_client,
                **(extra or {}),
            }
        )
        meta = entity_versions.bump("file", row["file_id"], updated_by=actor_id, source_client=source_client)
        row["entity"] = meta.to_dict()
        await _publish(
            FileUploadedEvent(
                entity_id=row["file_id"],
                revision=meta.updated_at,
                source_client=source_client,
                actor_id=actor_id,
                version=meta.version,
                payload=row,
            )
        )
        return row


class CrmAdapter:
    async def update_lead(
        self,
        lead: dict[str, Any],
        *,
        source_client: str = "api",
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        row = crm_mirror.upsert_lead(lead)
        meta = entity_versions.bump("lead", row["id"], updated_by=actor_id, source_client=source_client)
        row["entity"] = meta.to_dict()
        await _publish(
            CrmUpdatedEvent(
                entity_id=row["id"],
                entity_type="lead",
                revision=meta.updated_at,
                source_client=source_client,
                actor_id=actor_id,
                version=meta.version,
                payload=row,
            )
        )
        return row


class WorkspaceAdapter:
    async def change(
        self,
        workspace_id: str,
        *,
        source_client: str,
        actor_id: str | None = None,
        changes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        meta = entity_versions.bump("workspace", workspace_id, updated_by=actor_id, source_client=source_client)
        payload = {"workspace_id": workspace_id, "changes": changes or {}, "entity": meta.to_dict()}
        await _publish(
            WorkspaceChangedEvent(
                entity_id=workspace_id,
                revision=meta.updated_at,
                source_client=source_client,
                actor_id=actor_id,
                version=meta.version,
                payload=payload,
            )
        )
        return payload


task_adapter = TaskAdapter()
calendar_adapter = CalendarAdapter()
notification_adapter = NotificationAdapter()
conversation_adapter = ConversationAdapter()
memory_facade = MemoryFacadeAdapter()
file_adapter = FileAdapter()
crm_adapter = CrmAdapter()
workspace_adapter = WorkspaceAdapter()
