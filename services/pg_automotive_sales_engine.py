# Automotive Sales Engine v1 — leads, reservations, test drives, pipeline.

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from config import OWNER_ID
from database.models.automotive_sales import (
    ReservationStatus,
    SalesPipelineStage,
    TestDriveStatus,
)
from database.session import get_session
from repositories.automotive_inventory_repository import VehicleRepository
from repositories.automotive_sales_repository import (
    LeadRepository,
    SalesPipelineRepository,
    TestDriveRepository,
    VehicleReservationRepository,
)
from repositories.user_role_repository import UserRoleRepository

SALES_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})


class AutomotiveSalesEngineError(Exception):
    pass


class AutomotiveSalesEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in SALES_ROLES for role in roles)

    @staticmethod
    def _lead_snapshot(lead) -> dict[str, Any]:
        return {
            "id": str(lead.id),
            "vehicle_id": str(lead.vehicle_id) if lead.vehicle_id else None,
            "customer_name": lead.customer_name,
            "customer_phone": lead.customer_phone,
            "customer_email": lead.customer_email,
            "source": lead.source,
            "pipeline_stage": lead.pipeline_stage,
            "assigned_to": lead.assigned_to,
            "budget": str(lead.budget) if lead.budget else None,
            "currency": lead.currency,
            "notes": lead.notes,
            "created_at": lead.created_at.isoformat(),
            "updated_at": lead.updated_at.isoformat(),
        }

    @staticmethod
    def _reservation_snapshot(reservation) -> dict[str, Any]:
        return {
            "id": str(reservation.id),
            "lead_id": str(reservation.lead_id),
            "vehicle_id": str(reservation.vehicle_id),
            "reserved_until": (
                reservation.reserved_until.isoformat()
                if reservation.reserved_until
                else None
            ),
            "deposit_amount": (
                str(reservation.deposit_amount) if reservation.deposit_amount else None
            ),
            "status": reservation.status,
            "currency": reservation.currency,
        }

    @staticmethod
    def _test_drive_snapshot(test_drive) -> dict[str, Any]:
        return {
            "id": str(test_drive.id),
            "lead_id": str(test_drive.lead_id),
            "vehicle_id": str(test_drive.vehicle_id),
            "scheduled_at": test_drive.scheduled_at.isoformat(),
            "status": test_drive.status,
            "notes": test_drive.notes,
        }

    @staticmethod
    async def create_lead(
        actor_id: int,
        *,
        customer_name: str,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveSalesEngineV1.user_can_access(actor_id):
            raise AutomotiveSalesEngineError("Access denied")

        async with get_session() as session:
            lead = await LeadRepository(session).create(
                customer_name=customer_name,
                assigned_to=fields.pop("assigned_to", actor_id),
                **fields,
            )
            await SalesPipelineRepository(session).record(
                lead_id=lead.id,
                to_stage=lead.pipeline_stage,
                changed_by=actor_id,
                notes="Lead created",
            )
            return AutomotiveSalesEngineV1._lead_snapshot(lead)

    @staticmethod
    async def update_lead(
        actor_id: int,
        lead_id: uuid.UUID,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveSalesEngineV1.user_can_access(actor_id):
            raise AutomotiveSalesEngineError("Access denied")

        async with get_session() as session:
            lead = await LeadRepository(session).update_fields(lead_id, **fields)
            if lead is None:
                raise AutomotiveSalesEngineError(f"Lead not found: {lead_id}")
            return AutomotiveSalesEngineV1._lead_snapshot(lead)

    @staticmethod
    async def advance_pipeline(
        actor_id: int,
        lead_id: uuid.UUID,
        stage: str,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveSalesEngineV1.user_can_access(actor_id):
            raise AutomotiveSalesEngineError("Access denied")
        if stage not in {s.value for s in SalesPipelineStage}:
            raise AutomotiveSalesEngineError(f"Invalid stage: {stage}")

        async with get_session() as session:
            repo = LeadRepository(session)
            lead = await repo.get_by_id(lead_id)
            if lead is None:
                raise AutomotiveSalesEngineError(f"Lead not found: {lead_id}")

            old_stage = lead.pipeline_stage
            lead = await repo.update_stage(lead_id, stage)
            await SalesPipelineRepository(session).record(
                lead_id=lead_id,
                from_stage=old_stage,
                to_stage=stage,
                changed_by=actor_id,
                notes=notes,
            )
            return AutomotiveSalesEngineV1._lead_snapshot(lead)

    @staticmethod
    async def create_reservation(
        actor_id: int,
        lead_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        *,
        reserved_until: datetime | None = None,
        deposit_amount: Decimal | None = None,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveSalesEngineV1.user_can_access(actor_id):
            raise AutomotiveSalesEngineError("Access denied")

        async with get_session() as session:
            lead = await LeadRepository(session).get_by_id(lead_id)
            if lead is None:
                raise AutomotiveSalesEngineError(f"Lead not found: {lead_id}")

            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveSalesEngineError(f"Vehicle not found: {vehicle_id}")

            reservation = await VehicleReservationRepository(session).create(
                lead_id=lead_id,
                vehicle_id=vehicle_id,
                reserved_until=reserved_until,
                deposit_amount=deposit_amount,
                **fields,
            )

            if lead.pipeline_stage != SalesPipelineStage.RESERVED.value:
                old_stage = lead.pipeline_stage
                await LeadRepository(session).update_stage(
                    lead_id,
                    SalesPipelineStage.RESERVED.value,
                )
                await SalesPipelineRepository(session).record(
                    lead_id=lead_id,
                    from_stage=old_stage,
                    to_stage=SalesPipelineStage.RESERVED.value,
                    changed_by=actor_id,
                    notes="Vehicle reserved",
                )

            return AutomotiveSalesEngineV1._reservation_snapshot(reservation)

    @staticmethod
    async def update_reservation_status(
        actor_id: int,
        reservation_id: uuid.UUID,
        status: str,
    ) -> dict[str, Any]:
        if not await AutomotiveSalesEngineV1.user_can_access(actor_id):
            raise AutomotiveSalesEngineError("Access denied")
        if status not in {s.value for s in ReservationStatus}:
            raise AutomotiveSalesEngineError(f"Invalid status: {status}")

        async with get_session() as session:
            reservation = await VehicleReservationRepository(session).update_status(
                reservation_id,
                status,
            )
            if reservation is None:
                raise AutomotiveSalesEngineError(
                    f"Reservation not found: {reservation_id}"
                )
            return AutomotiveSalesEngineV1._reservation_snapshot(reservation)

    @staticmethod
    async def schedule_test_drive(
        actor_id: int,
        lead_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        scheduled_at: datetime,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveSalesEngineV1.user_can_access(actor_id):
            raise AutomotiveSalesEngineError("Access denied")

        async with get_session() as session:
            lead = await LeadRepository(session).get_by_id(lead_id)
            if lead is None:
                raise AutomotiveSalesEngineError(f"Lead not found: {lead_id}")

            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveSalesEngineError(f"Vehicle not found: {vehicle_id}")

            test_drive = await TestDriveRepository(session).create(
                lead_id=lead_id,
                vehicle_id=vehicle_id,
                scheduled_at=scheduled_at,
                notes=notes,
            )
            return AutomotiveSalesEngineV1._test_drive_snapshot(test_drive)

    @staticmethod
    async def update_test_drive_status(
        actor_id: int,
        test_drive_id: uuid.UUID,
        status: str,
    ) -> dict[str, Any]:
        if not await AutomotiveSalesEngineV1.user_can_access(actor_id):
            raise AutomotiveSalesEngineError("Access denied")
        if status not in {s.value for s in TestDriveStatus}:
            raise AutomotiveSalesEngineError(f"Invalid status: {status}")

        async with get_session() as session:
            test_drive = await TestDriveRepository(session).update_status(
                test_drive_id,
                status,
            )
            if test_drive is None:
                raise AutomotiveSalesEngineError(
                    f"Test drive not found: {test_drive_id}"
                )
            return AutomotiveSalesEngineV1._test_drive_snapshot(test_drive)

    @staticmethod
    async def get_lead(
        actor_id: int,
        lead_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveSalesEngineV1.user_can_access(actor_id):
            raise AutomotiveSalesEngineError("Access denied")

        async with get_session() as session:
            lead = await LeadRepository(session).get_by_id(lead_id)
            if lead is None:
                raise AutomotiveSalesEngineError(f"Lead not found: {lead_id}")

            reservations = await VehicleReservationRepository(session).list_by_lead(
                lead_id
            )
            test_drives = await TestDriveRepository(session).list_by_lead(lead_id)
            pipeline = await SalesPipelineRepository(session).list_by_lead(lead_id)

            return {
                "lead": AutomotiveSalesEngineV1._lead_snapshot(lead),
                "reservations": [
                    AutomotiveSalesEngineV1._reservation_snapshot(r)
                    for r in reservations
                ],
                "test_drives": [
                    AutomotiveSalesEngineV1._test_drive_snapshot(td)
                    for td in test_drives
                ],
                "pipeline": [
                    {
                        "from_stage": p.from_stage,
                        "to_stage": p.to_stage,
                        "created_at": p.created_at.isoformat(),
                        "notes": p.notes,
                    }
                    for p in pipeline
                ],
            }

    @staticmethod
    async def list_leads(
        actor_id: int,
        *,
        stage: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveSalesEngineV1.user_can_access(actor_id):
            raise AutomotiveSalesEngineError("Access denied")

        async with get_session() as session:
            repo = LeadRepository(session)
            if stage:
                leads = await repo.list_by_stage(stage, limit=limit)
            else:
                leads = await repo.list_all(limit=limit)

            return [AutomotiveSalesEngineV1._lead_snapshot(lead) for lead in leads]
