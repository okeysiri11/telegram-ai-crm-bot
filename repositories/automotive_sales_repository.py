# Automotive Sales Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_sales import (
    Lead,
    LeadSource,
    ReservationStatus,
    SalesPipelineEntry,
    SalesPipelineStage,
    TestDrive,
    TestDriveStatus,
    VehicleReservation,
)


class LeadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        customer_name: str,
        vehicle_id: uuid.UUID | None = None,
        customer_phone: str | None = None,
        customer_email: str | None = None,
        source: str = LeadSource.OTHER.value,
        pipeline_stage: str = SalesPipelineStage.NEW_LEAD.value,
        assigned_to: int | None = None,
        budget: Decimal | None = None,
        currency: str = "USD",
        notes: str | None = None,
        **extra: Any,
    ) -> Lead:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if source not in {s.value for s in LeadSource}:
            raise ValueError(f"Invalid source: {source}")
        if pipeline_stage not in {s.value for s in SalesPipelineStage}:
            raise ValueError(f"Invalid pipeline_stage: {pipeline_stage}")

        lead = Lead(
            customer_name=customer_name,
            vehicle_id=vehicle_id,
            customer_phone=customer_phone,
            customer_email=customer_email,
            source=source,
            pipeline_stage=pipeline_stage,
            assigned_to=assigned_to,
            budget=budget,
            currency=currency,
            notes=notes,
        )
        self._session.add(lead)
        await self._session.flush()
        return lead

    async def get_by_id(self, lead_id: uuid.UUID) -> Lead | None:
        result = await self._session.execute(
            select(Lead).where(Lead.id == lead_id)
        )
        return result.scalar_one_or_none()

    async def list_by_stage(
        self,
        stage: str,
        *,
        limit: int = 100,
    ) -> list[Lead]:
        result = await self._session.execute(
            select(Lead)
            .where(Lead.pipeline_stage == stage)
            .order_by(Lead.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_all(self, *, limit: int = 100) -> list[Lead]:
        result = await self._session.execute(
            select(Lead).order_by(Lead.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def update_fields(
        self,
        lead_id: uuid.UUID,
        **fields: Any,
    ) -> Lead | None:
        lead = await self.get_by_id(lead_id)
        if lead is None:
            return None
        allowed = {
            "vehicle_id", "customer_name", "customer_phone", "customer_email",
            "source", "assigned_to", "budget", "currency", "notes",
        }
        for key, value in fields.items():
            if key not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(lead, key, value)
        lead.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return lead

    async def update_stage(
        self,
        lead_id: uuid.UUID,
        stage: str,
    ) -> Lead | None:
        lead = await self.get_by_id(lead_id)
        if lead is None:
            return None
        if stage not in {s.value for s in SalesPipelineStage}:
            raise ValueError(f"Invalid stage: {stage}")
        lead.pipeline_stage = stage
        lead.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return lead


class VehicleReservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        lead_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        reserved_until: datetime | None = None,
        deposit_amount: Decimal | None = None,
        currency: str = "USD",
        status: str = ReservationStatus.ACTIVE.value,
        notes: str | None = None,
        **extra: Any,
    ) -> VehicleReservation:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in {s.value for s in ReservationStatus}:
            raise ValueError(f"Invalid status: {status}")

        reservation = VehicleReservation(
            lead_id=lead_id,
            vehicle_id=vehicle_id,
            reserved_until=reserved_until,
            deposit_amount=deposit_amount,
            currency=currency,
            status=status,
            notes=notes,
        )
        self._session.add(reservation)
        await self._session.flush()
        return reservation

    async def get_by_id(self, reservation_id: uuid.UUID) -> VehicleReservation | None:
        result = await self._session.execute(
            select(VehicleReservation).where(VehicleReservation.id == reservation_id)
        )
        return result.scalar_one_or_none()

    async def list_by_lead(self, lead_id: uuid.UUID) -> list[VehicleReservation]:
        result = await self._session.execute(
            select(VehicleReservation)
            .where(VehicleReservation.lead_id == lead_id)
            .order_by(VehicleReservation.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_vehicle(self, vehicle_id: uuid.UUID) -> list[VehicleReservation]:
        result = await self._session.execute(
            select(VehicleReservation)
            .where(VehicleReservation.vehicle_id == vehicle_id)
            .order_by(VehicleReservation.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        reservation_id: uuid.UUID,
        status: str,
    ) -> VehicleReservation | None:
        reservation = await self.get_by_id(reservation_id)
        if reservation is None:
            return None
        if status not in {s.value for s in ReservationStatus}:
            raise ValueError(f"Invalid status: {status}")
        reservation.status = status
        reservation.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return reservation


class TestDriveRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        lead_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        scheduled_at: datetime,
        status: str = TestDriveStatus.SCHEDULED.value,
        notes: str | None = None,
        **extra: Any,
    ) -> TestDrive:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in {s.value for s in TestDriveStatus}:
            raise ValueError(f"Invalid status: {status}")

        test_drive = TestDrive(
            lead_id=lead_id,
            vehicle_id=vehicle_id,
            scheduled_at=scheduled_at,
            status=status,
            notes=notes,
        )
        self._session.add(test_drive)
        await self._session.flush()
        return test_drive

    async def get_by_id(self, test_drive_id: uuid.UUID) -> TestDrive | None:
        result = await self._session.execute(
            select(TestDrive).where(TestDrive.id == test_drive_id)
        )
        return result.scalar_one_or_none()

    async def list_by_lead(self, lead_id: uuid.UUID) -> list[TestDrive]:
        result = await self._session.execute(
            select(TestDrive)
            .where(TestDrive.lead_id == lead_id)
            .order_by(TestDrive.scheduled_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        test_drive_id: uuid.UUID,
        status: str,
    ) -> TestDrive | None:
        test_drive = await self.get_by_id(test_drive_id)
        if test_drive is None:
            return None
        if status not in {s.value for s in TestDriveStatus}:
            raise ValueError(f"Invalid status: {status}")
        test_drive.status = status
        test_drive.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return test_drive


class SalesPipelineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        lead_id: uuid.UUID,
        to_stage: str,
        from_stage: str | None = None,
        changed_by: int | None = None,
        notes: str | None = None,
    ) -> SalesPipelineEntry:
        if to_stage not in {s.value for s in SalesPipelineStage}:
            raise ValueError(f"Invalid stage: {to_stage}")

        entry = SalesPipelineEntry(
            lead_id=lead_id,
            from_stage=from_stage,
            to_stage=to_stage,
            changed_by=changed_by,
            notes=notes,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_by_lead(self, lead_id: uuid.UUID) -> list[SalesPipelineEntry]:
        result = await self._session.execute(
            select(SalesPipelineEntry)
            .where(SalesPipelineEntry.lead_id == lead_id)
            .order_by(SalesPipelineEntry.created_at.asc())
        )
        return list(result.scalars().all())
