# Lifecycle management — apps, agents, plugins, workflows, knowledge.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from ecosystem.governance.audit.service import AuditService, audit_service
from ecosystem.governance.events import LifecycleChangedEvent
from ecosystem.governance.models import LifecycleKind, LifecycleRecord, LifecycleState
from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


VALID_TRANSITIONS: dict[LifecycleState, set[LifecycleState]] = {
    LifecycleState.REGISTERED: {LifecycleState.ACTIVE, LifecycleState.RETIRED},
    LifecycleState.ACTIVE: {LifecycleState.SUSPENDED, LifecycleState.DEPRECATED, LifecycleState.RETIRED},
    LifecycleState.SUSPENDED: {LifecycleState.ACTIVE, LifecycleState.RETIRED},
    LifecycleState.DEPRECATED: {LifecycleState.RETIRED, LifecycleState.ACTIVE},
    LifecycleState.RETIRED: set(),
}


class LifecycleService:
    def __init__(self, store: EcosystemStore | None = None, audit: AuditService | None = None) -> None:
        self._store = store or ecosystem_store
        self.audit = audit or audit_service

    async def register(
        self,
        kind: LifecycleKind,
        name: str,
        *,
        entity_id: str = "",
        version: str = "1.0.0",
        metadata: dict[str, Any] | None = None,
    ) -> LifecycleRecord:
        if not name:
            raise ValidationError("name is required")
        record = LifecycleRecord(
            kind=kind,
            name=name,
            entity_id=entity_id or name,
            version=version,
            state=LifecycleState.REGISTERED,
            metadata=metadata or {},
        )
        self._store.lifecycle_records.save(record.record_id, record)
        self.audit.record("lifecycle_register", resource_type=kind.value, resource_id=record.entity_id)
        await publish(
            LifecycleChangedEvent(
                record_id=record.record_id,
                kind=kind.value,
                entity_id=record.entity_id,
                state=record.state.value,
                version=version,
            )
        )
        return record

    async def transition(self, record_id: str, new_state: LifecycleState) -> LifecycleRecord:
        record = self.get(record_id)
        allowed = VALID_TRANSITIONS.get(record.state, set())
        if new_state not in allowed:
            raise ValidationError(f"Cannot transition from {record.state.value} to {new_state.value}")
        record.state = new_state
        record.updated_at = time.time()
        self._store.lifecycle_records.save(record_id, record)
        self.audit.record(
            "lifecycle_transition",
            resource_type=record.kind.value,
            resource_id=record.entity_id,
            details={"state": new_state.value},
        )
        await publish(
            LifecycleChangedEvent(
                record_id=record_id,
                kind=record.kind.value,
                entity_id=record.entity_id,
                state=new_state.value,
                version=record.version,
            )
        )
        return record

    async def set_version(self, record_id: str, version: str) -> LifecycleRecord:
        record = self.get(record_id)
        record.version = version
        record.updated_at = time.time()
        self._store.lifecycle_records.save(record_id, record)
        await publish(
            LifecycleChangedEvent(
                record_id=record_id,
                kind=record.kind.value,
                entity_id=record.entity_id,
                state=record.state.value,
                version=version,
            )
        )
        return record

    def get(self, record_id: str) -> LifecycleRecord:
        record = self._store.lifecycle_records.get(record_id)
        if record is None:
            raise NotFoundError("LifecycleRecord", record_id)
        return record

    def list_records(self, *, kind: LifecycleKind | None = None, state: LifecycleState | None = None) -> list[LifecycleRecord]:
        records = self._store.lifecycle_records.list_all()
        if kind:
            records = [r for r in records if r.kind == kind]
        if state:
            records = [r for r in records if r.state == state]
        return records


lifecycle_service = LifecycleService()
