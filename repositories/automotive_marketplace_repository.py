# Automotive Marketplace Connector Layer v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_marketplace import (
    ConnectorType,
    ImportJobStatus,
    ImportLogAction,
    ImportLogLevel,
    ConnectorCredential,
    VehicleImportJob,
    VehicleImportLog,
)


class ConnectorCredentialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        connector_type: str,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str | None = None,
        is_active: bool = True,
        sync_interval_minutes: int = 60,
        config: dict | None = None,
        notes: str | None = None,
        **extra: Any,
    ) -> ConnectorCredential:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if connector_type not in {t.value for t in ConnectorType}:
            raise ValueError(f"Invalid connector_type: {connector_type}")

        existing = await self.get_by_type(connector_type)
        if existing is None:
            cred = ConnectorCredential(
                connector_type=connector_type,
                api_key=api_key,
                api_secret=api_secret,
                base_url=base_url,
                is_active=is_active,
                sync_interval_minutes=sync_interval_minutes,
                config=config,
                notes=notes,
            )
            self._session.add(cred)
            await self._session.flush()
            return cred

        existing.api_key = api_key
        existing.api_secret = api_secret
        existing.base_url = base_url
        existing.is_active = is_active
        existing.sync_interval_minutes = sync_interval_minutes
        existing.config = config
        existing.notes = notes
        existing.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return existing

    async def get_by_type(self, connector_type: str) -> ConnectorCredential | None:
        result = await self._session.execute(
            select(ConnectorCredential).where(
                ConnectorCredential.connector_type == connector_type
            )
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[ConnectorCredential]:
        result = await self._session.execute(
            select(ConnectorCredential)
            .where(ConnectorCredential.is_active.is_(True))
            .order_by(ConnectorCredential.connector_type.asc())
        )
        return list(result.scalars().all())

    async def list_due_for_sync(self, now: datetime) -> list[ConnectorCredential]:
        creds = await self.list_active()
        due: list[ConnectorCredential] = []
        for cred in creds:
            if cred.last_sync_at is None:
                due.append(cred)
                continue
            elapsed = (now - cred.last_sync_at).total_seconds() / 60
            if elapsed >= cred.sync_interval_minutes:
                due.append(cred)
        return due

    async def mark_synced(
        self,
        connector_type: str,
        synced_at: datetime | None = None,
    ) -> ConnectorCredential | None:
        cred = await self.get_by_type(connector_type)
        if cred is None:
            return None
        cred.last_sync_at = synced_at or datetime.now(timezone.utc)
        cred.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return cred


class VehicleImportJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        connector_type: str,
        scheduled_at: datetime | None = None,
        triggered_by: int | None = None,
        is_scheduled: bool = False,
        status: str = ImportJobStatus.PENDING.value,
        **extra: Any,
    ) -> VehicleImportJob:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if connector_type not in {t.value for t in ConnectorType}:
            raise ValueError(f"Invalid connector_type: {connector_type}")

        job = VehicleImportJob(
            connector_type=connector_type,
            scheduled_at=scheduled_at,
            triggered_by=triggered_by,
            is_scheduled=is_scheduled,
            status=status,
        )
        self._session.add(job)
        await self._session.flush()
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> VehicleImportJob | None:
        result = await self._session.execute(
            select(VehicleImportJob).where(VehicleImportJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def start(self, job_id: uuid.UUID) -> VehicleImportJob | None:
        job = await self.get_by_id(job_id)
        if job is None:
            return None
        job.status = ImportJobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return job

    async def complete(
        self,
        job_id: uuid.UUID,
        *,
        created_count: int = 0,
        updated_count: int = 0,
        skipped_count: int = 0,
        duplicate_count: int = 0,
        images_synced: int = 0,
        price_changes: int = 0,
        status: str = ImportJobStatus.COMPLETED.value,
        error_message: str | None = None,
    ) -> VehicleImportJob | None:
        job = await self.get_by_id(job_id)
        if job is None:
            return None
        job.status = status
        job.completed_at = datetime.now(timezone.utc)
        job.created_count = created_count
        job.updated_count = updated_count
        job.skipped_count = skipped_count
        job.duplicate_count = duplicate_count
        job.images_synced = images_synced
        job.price_changes = price_changes
        job.error_message = error_message
        job.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return job

    async def list_pending_scheduled(
        self,
        now: datetime,
        *,
        limit: int = 50,
    ) -> list[VehicleImportJob]:
        result = await self._session.execute(
            select(VehicleImportJob)
            .where(
                VehicleImportJob.status == ImportJobStatus.PENDING.value,
                VehicleImportJob.is_scheduled.is_(True),
                VehicleImportJob.scheduled_at <= now,
            )
            .order_by(VehicleImportJob.scheduled_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_recent(self, *, limit: int = 50) -> list[VehicleImportJob]:
        result = await self._session.execute(
            select(VehicleImportJob)
            .order_by(VehicleImportJob.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class VehicleImportLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        job_id: uuid.UUID,
        action: str,
        level: str = ImportLogLevel.INFO.value,
        external_id: str | None = None,
        vin: str | None = None,
        vehicle_id: uuid.UUID | None = None,
        message: str | None = None,
        old_price: Decimal | None = None,
        new_price: Decimal | None = None,
        currency: str | None = None,
    ) -> VehicleImportLog:
        if action not in {a.value for a in ImportLogAction}:
            raise ValueError(f"Invalid action: {action}")

        log = VehicleImportLog(
            job_id=job_id,
            action=action,
            level=level,
            external_id=external_id,
            vin=vin,
            vehicle_id=vehicle_id,
            message=message,
            old_price=old_price,
            new_price=new_price,
            currency=currency,
        )
        self._session.add(log)
        await self._session.flush()
        return log

    async def list_by_job(self, job_id: uuid.UUID) -> list[VehicleImportLog]:
        result = await self._session.execute(
            select(VehicleImportLog)
            .where(VehicleImportLog.job_id == job_id)
            .order_by(VehicleImportLog.created_at.asc())
        )
        return list(result.scalars().all())
