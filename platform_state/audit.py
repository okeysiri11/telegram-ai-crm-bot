"""Platform state audit trail — who / when / from where / before / after.

Sprint 35.0: thin compatibility facade over AuditTimeline + canonical AuditService.
Keeps public symbols; avoids a second competing audit SoR.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from platform_state.audit_timeline import audit_timeline
from platform_state.models import utcnow


class PlatformStateAudit:
    """Hot ring-buffer for recent state mutations; durable history via Event Store timeline."""

    def __init__(self, *, maxlen: int = 1000) -> None:
        self._entries: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def log(
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
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor_id": actor_id,
            "source_client": source_client,
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "before": before,
            "after": after,
            "agent_id": agent_id,
            "change_id": change_id,
        }
        self._entries.append(entry)
        # Bridge to canonical AuditService only (correct AuditRecord contract).
        # Entity timelines are sourced from PlatformEventStore — no second local timeline copy.
        try:
            from datetime import datetime, timezone

            from audit.audit_event import AuditRecord
            from audit.audit_service import audit_service

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

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(self._entries)[-limit:]

    def timeline(self, entity_type: str, entity_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        return audit_timeline.for_entity(entity_type, entity_id, limit=limit)

    def reset(self) -> None:
        self._entries.clear()


platform_state_audit = PlatformStateAudit()
