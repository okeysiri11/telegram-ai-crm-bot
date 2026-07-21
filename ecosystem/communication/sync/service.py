# Cross-application synchronization.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from ecosystem.communication.events import SynchronizationCompletedEvent
from ecosystem.communication.models import SyncRecord, SyncScope
from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class SyncService:
    """Synchronizes shared state across registered applications."""

    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    async def synchronize(
        self,
        scope: SyncScope,
        data: dict[str, Any],
        *,
        source_application: str,
        target_applications: list[str] | None = None,
    ) -> SyncRecord:
        if not source_application:
            raise ValidationError("source_application is required")
        targets = target_applications or [
            r.application_id
            for r in self._store.registrations.list_all()
            if r.is_connected and r.application_id != source_application
        ]
        record = SyncRecord(
            scope=scope,
            source_application=source_application,
            target_applications=targets,
            data=data,
            status="completed",
            completed_at=time.time(),
        )
        self._store.sync_records.save(record.sync_id, record)
        await publish(
            SynchronizationCompletedEvent(
                sync_id=record.sync_id,
                scope=scope.value,
                source_application=source_application,
                target_count=len(targets),
            )
        )
        return record

    async def sync_context(self, source_application: str, data: dict[str, Any], *, targets: list[str] | None = None) -> SyncRecord:
        return await self.synchronize(SyncScope.CONTEXT, data, source_application=source_application, target_applications=targets)

    async def sync_user(self, source_application: str, user_data: dict[str, Any], *, targets: list[str] | None = None) -> SyncRecord:
        return await self.synchronize(SyncScope.USER, user_data, source_application=source_application, target_applications=targets)

    async def sync_permissions(self, source_application: str, permission_data: dict[str, Any], *, targets: list[str] | None = None) -> SyncRecord:
        return await self.synchronize(SyncScope.PERMISSION, permission_data, source_application=source_application, target_applications=targets)

    async def sync_organization(self, source_application: str, org_data: dict[str, Any], *, targets: list[str] | None = None) -> SyncRecord:
        return await self.synchronize(SyncScope.ORGANIZATION, org_data, source_application=source_application, target_applications=targets)

    async def sync_notifications(self, source_application: str, notification_data: dict[str, Any], *, targets: list[str] | None = None) -> SyncRecord:
        return await self.synchronize(SyncScope.NOTIFICATION, notification_data, source_application=source_application, target_applications=targets)

    def get(self, sync_id: str) -> SyncRecord:
        record = self._store.sync_records.get(sync_id)
        if record is None:
            raise NotFoundError("SyncRecord", sync_id)
        return record

    def history(self, *, source_application: str = "", limit: int = 50) -> list[SyncRecord]:
        records = self._store.sync_records.list_all()
        if source_application:
            records = [r for r in records if r.source_application == source_application]
        return sorted(records, key=lambda r: r.created_at, reverse=True)[:limit]


sync_service = SyncService()
