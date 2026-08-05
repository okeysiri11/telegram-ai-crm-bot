"""Audit Timeline — full entity history for every change (Sprint 34.2D)."""

from __future__ import annotations

from typing import Any

from platform_state.event_store import PlatformEventStore, event_store
from platform_state.models import utcnow
from platform_state.version_engine import VersionEngine, version_engine


class AuditTimeline:
    def __init__(
        self,
        store: PlatformEventStore | None = None,
        versions: VersionEngine | None = None,
    ) -> None:
        self._store = store or event_store
        self._versions = versions or version_engine
        self._local: list[dict[str, Any]] = []

    def record(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        actor_id: str | None = None,
        source_client: str | None = None,
        workspace_id: str | None = None,
        tenant_id: str | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        agent_id: str | None = None,
        change_id: str | None = None,
    ) -> dict[str, Any]:
        entry = {
            "at": utcnow().isoformat(),
            "who": actor_id,
            "when": utcnow().isoformat(),
            "what": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_value": before,
            "new_value": after,
            "source_client": source_client,
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "change_id": change_id,
        }
        self._local.append(entry)
        # Durable: also append a timeline event if not already in store path
        try:
            from audit.audit_event import AuditRecord
            from audit.audit_service import audit_service
            from datetime import datetime, timezone

            record = AuditRecord(
                event_type=f"PLATFORM_STATE_{action.upper()}",
                entity_type=entity_type,
                entity_id=entity_id,
                actor_id=actor_id,
                old_value=before,
                new_value=after,
                metadata_json={
                    "source_client": source_client,
                    "workspace_id": workspace_id,
                    "tenant_id": tenant_id,
                    "agent_id": agent_id,
                    "change_id": change_id,
                },
                created_at=datetime.now(timezone.utc),
            )
            audit_service._enqueue(audit_service.record(record))
        except Exception:  # noqa: BLE001
            pass
        return entry

    def for_entity(
        self,
        entity_type: str,
        entity_id: str,
        *,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        events = self._store.stream(entity_type, entity_id, limit=limit)
        timeline: list[dict[str, Any]] = []
        for ev in events:
            changed = self._diff_keys(ev.before, ev.after)
            timeline.append(
                {
                    "seq": ev.seq,
                    "event_id": ev.event_id,
                    "who": ev.actor_id,
                    "when": ev.occurred_at,
                    "what": ev.event_type,
                    "what_changed": changed,
                    "old_value": ev.before,
                    "new_value": ev.after,
                    "source_client": ev.source_client,
                    "workspace": ev.workspace_id,
                    "tenant": ev.tenant_id,
                    "agent_id": ev.agent_id,
                    "version": ev.version,
                    "change_id": ev.change_id,
                }
            )
        # Merge local-only entries not yet in store
        for loc in self._local:
            if loc["entity_type"] == entity_type and loc["entity_id"] == entity_id:
                timeline.append(
                    {
                        "who": loc["who"],
                        "when": loc["when"],
                        "what": loc["what"],
                        "what_changed": self._diff_keys(loc.get("old_value"), loc.get("new_value")),
                        "old_value": loc.get("old_value"),
                        "new_value": loc.get("new_value"),
                        "source_client": loc.get("source_client"),
                        "workspace": loc.get("workspace_id"),
                        "tenant": loc.get("tenant_id"),
                        "agent_id": loc.get("agent_id"),
                    }
                )
        return timeline[-limit:]

    def for_workspace(self, workspace_id: str, *, limit: int = 1000) -> list[dict[str, Any]]:
        events = self._store.workspace_stream(workspace_id, limit=limit)
        return [
            {
                "seq": e.seq,
                "who": e.actor_id,
                "when": e.occurred_at,
                "what": e.event_type,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "old_value": e.before,
                "new_value": e.after,
                "source_client": e.source_client,
                "workspace": e.workspace_id,
                "tenant": e.tenant_id,
                "agent_id": e.agent_id,
            }
            for e in events
        ]

    @staticmethod
    def _diff_keys(before: dict[str, Any] | None, after: dict[str, Any] | None) -> list[str]:
        b = before or {}
        a = after or {}
        keys = set(b) | set(a)
        return sorted(k for k in keys if b.get(k) != a.get(k))

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        events = self._store.since_seq(max(0, self._store.max_seq() - limit), limit=limit)
        return [e.to_dict() for e in events]

    def reset(self) -> None:
        self._local.clear()


audit_timeline = AuditTimeline()
