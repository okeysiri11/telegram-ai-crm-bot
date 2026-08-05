"""PlatformStateService — single facade for all clients (Sprint 34.2C)."""

from __future__ import annotations

import logging
from typing import Any

from platform_state.adapters.domain import (
    _activity,
    _favorites,
    _sessions,
    calendar_adapter,
    conversation_adapter,
    crm_adapter,
    crm_mirror,
    entity_versions,
    file_adapter,
    file_store,
    memory_facade,
    notification_adapter,
    notification_store,
    task_adapter,
    workspace_adapter,
)
from platform_state.audit import platform_state_audit
from platform_state.conflict import conflict_resolver
from platform_state.conversation import conversation_engine
from platform_state.enterprise import enterprise_runtime
from platform_state.memory_store import memory_adapter
from platform_state.models import (
    ALL_SLICES,
    SLICE_ACTIVITY,
    SLICE_AGENTS,
    SLICE_ANALYTICS,
    SLICE_CALENDAR,
    SLICE_CONVERSATIONS,
    SLICE_CRM,
    SLICE_DOCUMENTS,
    SLICE_FAVORITES,
    SLICE_FILES,
    SLICE_MEMORY,
    SLICE_NOTIFICATIONS,
    SLICE_PROJECTS,
    SLICE_SESSIONS,
    SLICE_TASKS,
    SLICE_USERS,
    SLICE_WORKSPACES,
    PlatformStateSnapshot,
    StateSlice,
    compute_revision,
    utcnow,
)
from platform_state.sync_engine import sync_engine

logger = logging.getLogger(__name__)


class PlatformStateService:
    """
    ONE platform state. Clients (web, telegram, desktop, mobile, api, ai)
    read/write through this service — never by poking sibling modules for side effects.
    """

    def __init__(self) -> None:
        self.tasks = task_adapter
        self.calendar = calendar_adapter
        self.notifications = notification_adapter
        self.conversations = conversation_adapter
        self.memory = memory_facade
        self.files = file_adapter
        self.crm = crm_adapter
        self.workspaces = workspace_adapter
        self.sync = sync_engine
        self.audit = platform_state_audit
        self.conflicts = conflict_resolver
        self.enterprise = enterprise_runtime
        self.versions = enterprise_runtime.versions
        self.events = enterprise_runtime.events
        self.replay = enterprise_runtime.replay
        self.timeline = enterprise_runtime.timeline
        self.telemetry = enterprise_runtime.telemetry
        self.healing = enterprise_runtime.healing

    def status(self) -> dict[str, Any]:
        return {
            "sprint": "34.2D",
            "unified_platform_state": True,
            "enterprise_runtime": True,
            "deterministic": True,
            "revision": sync_engine.revision,
            "slices": list(ALL_SLICES),
            "sync": sync_engine.status(),
            "conversations": len(conversation_engine._by_id),
            "memory_records": len(memory_adapter._records),
            "notifications": len(notification_store._items),
            "files": len(file_store._files),
            "event_bus": "events.event_bus.PlatformEventBus",
            "enterprise": enterprise_runtime.status(),
        }

    def snapshot(
        self,
        *,
        user_id: str | None = None,
        telegram_id: int | None = None,
        workspace_id: str | None = None,
        slices: list[str] | None = None,
    ) -> PlatformStateSnapshot:
        wanted = set(slices or ALL_SLICES)
        built: dict[str, StateSlice] = {}

        def add(slice_id: str, data: dict[str, Any]) -> None:
            if slice_id not in wanted:
                return
            rev = str(data.get("revision") or compute_revision(slice_id, data))
            built[slice_id] = StateSlice(slice_id=slice_id, revision=rev, data=data)

        if SLICE_USERS in wanted:
            add(
                SLICE_USERS,
                {
                    "user_id": user_id,
                    "telegram_id": telegram_id,
                    "note": "identity via platform_identity",
                    "revision": compute_revision(user_id, telegram_id),
                },
            )
        if SLICE_SESSIONS in wanted:
            sess = [s for s in _sessions.values() if not user_id or s.get("user_id") == user_id]
            add(SLICE_SESSIONS, {"sessions": sess, "revision": compute_revision(len(_sessions))})
        if SLICE_CRM in wanted:
            add(SLICE_CRM, crm_mirror.snapshot())
        if SLICE_TASKS in wanted:
            add(SLICE_TASKS, task_adapter.snapshot(telegram_id=telegram_id))
        if SLICE_CALENDAR in wanted:
            add(SLICE_CALENDAR, calendar_adapter.snapshot(telegram_id=telegram_id))
        if SLICE_NOTIFICATIONS in wanted:
            add(SLICE_NOTIFICATIONS, notification_store.snapshot(user_id=user_id))
        if SLICE_FILES in wanted:
            add(SLICE_FILES, file_store.snapshot())
        if SLICE_DOCUMENTS in wanted:
            add(
                SLICE_DOCUMENTS,
                {
                    "documents": file_store.list(limit=50),
                    "revision": file_store.snapshot()["revision"],
                },
            )
        if SLICE_CONVERSATIONS in wanted:
            add(
                SLICE_CONVERSATIONS,
                conversation_engine.snapshot(user_id=user_id, telegram_id=telegram_id),
            )
        if SLICE_MEMORY in wanted:
            add(
                SLICE_MEMORY,
                memory_adapter.snapshot(user_id=user_id, workspace_id=workspace_id),
            )
        if SLICE_AGENTS in wanted:
            try:
                from dataclasses import asdict

                from platform_registry.agents import all_agents

                agents = [asdict(a) for a in all_agents()]
            except Exception:  # noqa: BLE001
                agents = []
            add(SLICE_AGENTS, {"agents": agents, "revision": compute_revision(len(agents))})
        if SLICE_PROJECTS in wanted:
            add(SLICE_PROJECTS, {"projects": [], "revision": "0", "note": "via existing project modules"})
        if SLICE_ANALYTICS in wanted:
            add(
                SLICE_ANALYTICS,
                {
                    "activity_count": len(_activity),
                    "sync_revision": sync_engine.revision,
                    "revision": sync_engine.revision,
                },
            )
        if SLICE_ACTIVITY in wanted:
            add(
                SLICE_ACTIVITY,
                {"recent": list(_activity)[-50:], "revision": compute_revision(len(_activity))},
            )
        if SLICE_FAVORITES in wanted:
            favs = _favorites.get(user_id or "", []) if user_id else []
            add(SLICE_FAVORITES, {"favorites": favs, "revision": compute_revision(favs)})
        if SLICE_WORKSPACES in wanted:
            try:
                from dataclasses import asdict

                from platform_registry.workspaces import all_workspace_modules

                ws = [asdict(w) for w in all_workspace_modules()]
            except Exception:  # noqa: BLE001
                ws = []
            add(
                SLICE_WORKSPACES,
                {
                    "workspaces": ws,
                    "active": workspace_id,
                    "revision": compute_revision(workspace_id, len(ws)),
                },
            )

        revision = compute_revision(sync_engine.revision, sorted(built.keys()), utcnow().isoformat())
        return PlatformStateSnapshot(
            revision=revision,
            generated_at=utcnow().isoformat(),
            slices=built,
            user_id=user_id,
            telegram_id=telegram_id,
            workspace_id=workspace_id,
        )

    def put_session(self, session_id: str, data: dict[str, Any]) -> dict[str, Any]:
        row = {**data, "session_id": session_id, "updated_at": utcnow().isoformat()}
        _sessions[session_id] = row
        return row

    def set_favorites(self, user_id: str, items: list[str]) -> list[str]:
        _favorites[user_id] = list(items)
        return _favorites[user_id]

    def delta(self, last_revision: str | None, *, slices: list[str] | None = None) -> dict[str, Any]:
        events = sync_engine.delta_since(last_revision, slices=slices)
        return {
            "revision": sync_engine.revision,
            "events": events,
            "count": len(events),
        }

    def register_client_cursor(
        self,
        client_id: str,
        *,
        last_revision: str | None = None,
        slices: list[str] | None = None,
    ) -> dict[str, Any]:
        cursor = sync_engine.register_cursor(client_id, last_revision=last_revision, slices=slices)
        return {
            "client_id": cursor.client_id,
            "last_revision": cursor.last_revision,
            "last_seen_at": cursor.last_seen_at,
            "slices": sorted(cursor.slices),
        }

    def reset(self) -> None:
        sync_engine.reset()
        conversation_engine.reset()
        memory_adapter.reset()
        notification_store.reset()
        file_store.reset()
        crm_mirror.reset()
        entity_versions.reset()
        platform_state_audit.reset()
        enterprise_runtime.reset()
        _activity.clear()
        _favorites.clear()
        _sessions.clear()


platform_state = PlatformStateService()
