# Automotive Operations Engine v1 — unified vehicle lifecycle orchestration.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from config import MANAGER_ID, OWNER_ID
from database.models.audit_log import AuditAction
from database.models.automotive_inventory import VehicleStatus
from database.models.automotive_operations import (
    VehicleAttachmentType,
    VehicleOperationState,
    VehicleTaskPriority,
    VehicleTaskStatus,
    VehicleTaskType,
)
from database.models.notification import NotificationChannel, NotificationType
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.automotive_inventory_repository import VehicleRepository
from repositories.automotive_operations_repository import (
    VehicleAttachmentRepository,
    VehicleChecklistRepository,
    VehicleOperationRepository,
    VehicleStateHistoryRepository,
    VehicleTaskRepository,
)
from repositories.notification_repository import NotificationRepository
from repositories.user_role_repository import UserRoleRepository

OPERATIONS_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})

STATE_TRANSITIONS: dict[str, frozenset[str]] = {
    VehicleOperationState.PROCUREMENT.value: frozenset({
        VehicleOperationState.IN_TRANSIT.value,
    }),
    VehicleOperationState.IN_TRANSIT.value: frozenset({
        VehicleOperationState.CUSTOMS.value,
    }),
    VehicleOperationState.CUSTOMS.value: frozenset({
        VehicleOperationState.WAREHOUSE.value,
    }),
    VehicleOperationState.WAREHOUSE.value: frozenset({
        VehicleOperationState.PREPARATION.value,
    }),
    VehicleOperationState.PREPARATION.value: frozenset({
        VehicleOperationState.LISTED_FOR_SALE.value,
    }),
    VehicleOperationState.LISTED_FOR_SALE.value: frozenset({
        VehicleOperationState.RESERVED.value,
    }),
    VehicleOperationState.RESERVED.value: frozenset({
        VehicleOperationState.SOLD.value,
        VehicleOperationState.LISTED_FOR_SALE.value,
    }),
    VehicleOperationState.SOLD.value: frozenset({
        VehicleOperationState.DELIVERED.value,
    }),
    VehicleOperationState.DELIVERED.value: frozenset({
        VehicleOperationState.CLOSED.value,
    }),
    VehicleOperationState.CLOSED.value: frozenset(),
}

STATE_SLA_DAYS: dict[str, int] = {
    VehicleOperationState.PROCUREMENT.value: 7,
    VehicleOperationState.IN_TRANSIT.value: 14,
    VehicleOperationState.CUSTOMS.value: 5,
    VehicleOperationState.WAREHOUSE.value: 3,
    VehicleOperationState.PREPARATION.value: 7,
    VehicleOperationState.LISTED_FOR_SALE.value: 30,
    VehicleOperationState.RESERVED.value: 7,
    VehicleOperationState.SOLD.value: 14,
    VehicleOperationState.DELIVERED.value: 3,
}

TASK_SLA_HOURS: dict[str, int] = {
    VehicleTaskType.LOGISTICS_ORDER.value: 24,
    VehicleTaskType.TREASURY_RESERVE.value: 12,
    VehicleTaskType.CUSTOMS_CLEARANCE.value: 72,
    VehicleTaskType.INSPECTION.value: 48,
    VehicleTaskType.DETAILING.value: 24,
    VehicleTaskType.PHOTOGRAPHY.value: 24,
    VehicleTaskType.MARKETPLACE_PUBLISH.value: 12,
    VehicleTaskType.SALES_NOTIFY.value: 4,
    VehicleTaskType.SETTLEMENT.value: 48,
    VehicleTaskType.DELIVERY.value: 72,
    VehicleTaskType.RELEASE_RESERVATION.value: 24,
    VehicleTaskType.ACCOUNTING_ENTRY.value: 24,
}

INVENTORY_STATUS_MAP: dict[str, str] = {
    VehicleOperationState.IN_TRANSIT.value: VehicleStatus.IN_TRANSIT.value,
    VehicleOperationState.CUSTOMS.value: VehicleStatus.IN_CUSTOMS.value,
    VehicleOperationState.WAREHOUSE.value: VehicleStatus.IN_STOCK.value,
    VehicleOperationState.PREPARATION.value: VehicleStatus.IN_STOCK.value,
    VehicleOperationState.LISTED_FOR_SALE.value: VehicleStatus.IN_STOCK.value,
    VehicleOperationState.RESERVED.value: VehicleStatus.RESERVED.value,
    VehicleOperationState.SOLD.value: VehicleStatus.SOLD.value,
    VehicleOperationState.DELIVERED.value: VehicleStatus.DELIVERED.value,
    VehicleOperationState.CLOSED.value: VehicleStatus.DELIVERED.value,
}

ARRIVAL_CHECKLIST: tuple[tuple[str, str], ...] = (
    ("exterior_inspection", "Exterior inspection completed"),
    ("interior_inspection", "Interior inspection completed"),
    ("mechanical_check", "Mechanical check completed"),
    ("documents_received", "Import documents received"),
)

PREPARATION_CHECKLIST: tuple[tuple[str, str], ...] = (
    ("detailing_done", "Detailing completed"),
    ("photos_taken", "Photography completed"),
    ("pricing_set", "Pricing approved"),
    ("listing_ready", "Listing materials ready"),
)


class AutomotiveOperationsEngineError(Exception):
    pass


class AutomotiveOperationsEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in OPERATIONS_ROLES for role in roles)

    @staticmethod
    def _operation_snapshot(operation) -> dict[str, Any]:
        return {
            "id": str(operation.id),
            "vehicle_id": str(operation.vehicle_id),
            "current_state": operation.current_state,
            "assigned_manager_id": operation.assigned_manager_id,
            "state_entered_at": operation.state_entered_at.isoformat(),
            "sla_deadline": (
                operation.sla_deadline.isoformat() if operation.sla_deadline else None
            ),
            "is_active": operation.is_active,
            "metadata": operation.metadata_,
            "notes": operation.notes,
            "created_at": operation.created_at.isoformat(),
            "updated_at": operation.updated_at.isoformat(),
        }

    @staticmethod
    def _state_history_snapshot(entry) -> dict[str, Any]:
        return {
            "id": str(entry.id),
            "from_state": entry.from_state,
            "to_state": entry.to_state,
            "changed_by": entry.changed_by,
            "notes": entry.notes,
            "created_at": entry.created_at.isoformat(),
        }

    @staticmethod
    def _task_snapshot(task) -> dict[str, Any]:
        return {
            "id": str(task.id),
            "operation_id": str(task.operation_id),
            "vehicle_id": str(task.vehicle_id),
            "task_type": task.task_type,
            "title": task.title,
            "status": task.status,
            "priority": task.priority,
            "assigned_to": task.assigned_to,
            "sla_deadline": (
                task.sla_deadline.isoformat() if task.sla_deadline else None
            ),
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
            "auto_generated": task.auto_generated,
            "metadata": task.metadata_,
            "notes": task.notes,
        }

    @staticmethod
    def _checklist_snapshot(item) -> dict[str, Any]:
        return {
            "id": str(item.id),
            "item_key": item.item_key,
            "label": item.label,
            "is_required": item.is_required,
            "is_completed": item.is_completed,
            "completed_at": (
                item.completed_at.isoformat() if item.completed_at else None
            ),
            "sort_order": item.sort_order,
        }

    @staticmethod
    def _attachment_snapshot(attachment) -> dict[str, Any]:
        return {
            "id": str(attachment.id),
            "file_url": attachment.file_url,
            "attachment_type": attachment.attachment_type,
            "filename": attachment.filename,
            "uploaded_by": attachment.uploaded_by,
            "created_at": attachment.created_at.isoformat(),
        }

    @staticmethod
    def _state_sla_deadline(state: str) -> datetime:
        days = STATE_SLA_DAYS.get(state, 7)
        return datetime.now(timezone.utc) + timedelta(days=days)

    @staticmethod
    def _task_sla_deadline(task_type: str) -> datetime:
        hours = TASK_SLA_HOURS.get(task_type, 24)
        return datetime.now(timezone.utc) + timedelta(hours=hours)

    @staticmethod
    async def _publish_event(
        event_type: str,
        aggregate_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> None:
        try:
            from events.crm_publisher import publish_crm_event

            await publish_crm_event(event_type, "vehicle", aggregate_id, payload)
        except Exception:
            pass

    @staticmethod
    async def _audit(
        session,
        *,
        user_id: int,
        entity_id: str,
        action: str,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> None:
        await AuditRepository(session).create_log(
            user_id=user_id,
            entity_type="vehicle_operation",
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )

    @staticmethod
    async def _notify(
        session,
        *,
        user_id: int | None,
        title: str,
        message: str,
    ) -> None:
        await NotificationRepository(session).create(
            user_id=user_id,
            notification_type=NotificationType.STATUS_CHANGED.value,
            channel=NotificationChannel.INTERNAL.value,
            title=title,
            message=message,
        )

    @staticmethod
    async def _create_task(
        session,
        *,
        operation_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        task_type: str,
        title: str,
        assigned_to: int | None = None,
        auto_generated: bool = True,
        priority: str = VehicleTaskPriority.NORMAL.value,
        metadata: dict | None = None,
        notes: str | None = None,
    ):
        return await VehicleTaskRepository(session).create(
            operation_id=operation_id,
            vehicle_id=vehicle_id,
            task_type=task_type,
            title=title,
            assigned_to=assigned_to,
            sla_deadline=AutomotiveOperationsEngineV1._task_sla_deadline(task_type),
            auto_generated=auto_generated,
            priority=priority,
            metadata=metadata,
            notes=notes,
        )

    @staticmethod
    async def _create_checklist_items(
        session,
        *,
        operation_id: uuid.UUID,
        items: tuple[tuple[str, str], ...],
        task_id: uuid.UUID | None = None,
    ) -> None:
        repo = VehicleChecklistRepository(session)
        for index, (key, label) in enumerate(items):
            await repo.create(
                operation_id=operation_id,
                task_id=task_id,
                item_key=key,
                label=label,
                sort_order=index,
            )

    @staticmethod
    async def _sync_inventory_status(
        actor_id: int,
        vehicle_id: uuid.UUID,
        operation_state: str,
    ) -> None:
        inventory_status = INVENTORY_STATUS_MAP.get(operation_state)
        if inventory_status is None:
            return
        try:
            from services.pg_automotive_inventory_engine import (
                AutomotiveInventoryEngineV1,
            )

            await AutomotiveInventoryEngineV1.update_status(
                actor_id,
                vehicle_id,
                inventory_status,
                notes=f"Synced from operations state {operation_state}",
            )
        except Exception:
            pass

    @staticmethod
    async def _run_purchased_workflow(
        session,
        actor_id: int,
        operation,
        vehicle,
        manager_id: int | None,
    ) -> list[dict[str, Any]]:
        tasks: list = []
        assignee = manager_id or MANAGER_ID

        tasks.append(await AutomotiveOperationsEngineV1._create_task(
            session,
            operation_id=operation.id,
            vehicle_id=vehicle.id,
            task_type=VehicleTaskType.LOGISTICS_ORDER.value,
            title=f"Create logistics order for {vehicle.stock_number}",
            assigned_to=assignee,
        ))
        tasks.append(await AutomotiveOperationsEngineV1._create_task(
            session,
            operation_id=operation.id,
            vehicle_id=vehicle.id,
            task_type=VehicleTaskType.TREASURY_RESERVE.value,
            title=f"Reserve treasury funds for {vehicle.stock_number}",
            assigned_to=assignee,
            priority=VehicleTaskPriority.HIGH.value,
        ))
        tasks.append(await AutomotiveOperationsEngineV1._create_task(
            session,
            operation_id=operation.id,
            vehicle_id=vehicle.id,
            task_type=VehicleTaskType.CUSTOMS_CLEARANCE.value,
            title=f"Prepare customs clearance for {vehicle.vin}",
            assigned_to=assignee,
        ))

        await VehicleOperationRepository(session).assign_manager(
            operation.id,
            assignee,
        )

        try:
            from services.pg_automotive_procurement_engine import (
                AutomotiveProcurementEngineV1,
            )

            order_number = f"PO-{vehicle.stock_number}"
            await AutomotiveProcurementEngineV1.create_purchase_order(
                actor_id,
                order_number=order_number,
                source="LOCAL_DEALER",
                make=vehicle.make,
                model=vehicle.model,
                year=vehicle.year,
                vehicle_id=vehicle.id,
                vin=vehicle.vin,
                agreed_price=vehicle.purchase_price,
                currency=vehicle.currency,
            )
        except Exception:
            pass

        try:
            from services.pg_settlement_engine import SettlementEngineV1

            amount = vehicle.purchase_price or Decimal("0")
            if amount > 0:
                await SettlementEngineV1.create_settlement(
                    actor_id,
                    settlement_type="BANK",
                    asset=vehicle.currency,
                    amount=amount,
                    reference=f"treasury-reserve-{vehicle.stock_number}",
                )
        except Exception:
            pass

        await AutomotiveOperationsEngineV1._notify(
            session,
            user_id=assignee,
            title="Vehicle purchased — logistics assigned",
            message=(
                f"Vehicle {vehicle.stock_number} ({vehicle.vin}) entered procurement. "
                f"Logistics tasks created."
            ),
        )

        return [AutomotiveOperationsEngineV1._task_snapshot(t) for t in tasks]

    @staticmethod
    async def _run_arrived_workflow(
        session,
        actor_id: int,
        operation,
        vehicle,
    ) -> list[dict[str, Any]]:
        tasks: list = []
        manager = operation.assigned_manager_id or MANAGER_ID

        inspection = await AutomotiveOperationsEngineV1._create_task(
            session,
            operation_id=operation.id,
            vehicle_id=vehicle.id,
            task_type=VehicleTaskType.INSPECTION.value,
            title=f"Inspect {vehicle.stock_number}",
            assigned_to=manager,
        )
        tasks.append(inspection)

        tasks.append(await AutomotiveOperationsEngineV1._create_task(
            session,
            operation_id=operation.id,
            vehicle_id=vehicle.id,
            task_type=VehicleTaskType.DETAILING.value,
            title=f"Detail {vehicle.stock_number}",
            assigned_to=manager,
        ))
        tasks.append(await AutomotiveOperationsEngineV1._create_task(
            session,
            operation_id=operation.id,
            vehicle_id=vehicle.id,
            task_type=VehicleTaskType.PHOTOGRAPHY.value,
            title=f"Photograph {vehicle.stock_number}",
            assigned_to=manager,
        ))

        await AutomotiveOperationsEngineV1._create_checklist_items(
            session,
            operation_id=operation.id,
            items=ARRIVAL_CHECKLIST,
            task_id=inspection.id,
        )

        return [AutomotiveOperationsEngineV1._task_snapshot(t) for t in tasks]

    @staticmethod
    async def _run_listed_workflow(
        session,
        actor_id: int,
        operation,
        vehicle,
    ) -> list[dict[str, Any]]:
        tasks: list = []
        manager = operation.assigned_manager_id or MANAGER_ID

        tasks.append(await AutomotiveOperationsEngineV1._create_task(
            session,
            operation_id=operation.id,
            vehicle_id=vehicle.id,
            task_type=VehicleTaskType.MARKETPLACE_PUBLISH.value,
            title=f"Publish {vehicle.stock_number} to marketplaces",
            assigned_to=manager,
            priority=VehicleTaskPriority.HIGH.value,
        ))
        tasks.append(await AutomotiveOperationsEngineV1._create_task(
            session,
            operation_id=operation.id,
            vehicle_id=vehicle.id,
            task_type=VehicleTaskType.SALES_NOTIFY.value,
            title=f"Notify sales managers about {vehicle.stock_number}",
            assigned_to=manager,
            priority=VehicleTaskPriority.URGENT.value,
        ))

        await AutomotiveOperationsEngineV1._create_checklist_items(
            session,
            operation_id=operation.id,
            items=PREPARATION_CHECKLIST,
        )

        try:
            from database.models.automotive_marketplace import ConnectorType
            from services.pg_automotive_marketplace_engine import (
                AutomotiveMarketplaceEngineV1,
            )

            for connector in ConnectorType:
                await AutomotiveMarketplaceEngineV1.schedule_import_job(
                    actor_id,
                    connector.value,
                )
        except Exception:
            pass

        await AutomotiveOperationsEngineV1._notify(
            session,
            user_id=manager,
            title="Vehicle listed for sale",
            message=(
                f"{vehicle.make} {vehicle.model} ({vehicle.vin}) is now listed. "
                f"Marketplace publish tasks created."
            ),
        )

        return [AutomotiveOperationsEngineV1._task_snapshot(t) for t in tasks]

    @staticmethod
    async def _run_sold_workflow(
        session,
        actor_id: int,
        operation,
        vehicle,
    ) -> list[dict[str, Any]]:
        tasks: list = []
        manager = operation.assigned_manager_id or MANAGER_ID

        tasks.append(await AutomotiveOperationsEngineV1._create_task(
            session,
            operation_id=operation.id,
            vehicle_id=vehicle.id,
            task_type=VehicleTaskType.SETTLEMENT.value,
            title=f"Create settlement for {vehicle.stock_number}",
            assigned_to=manager,
            priority=VehicleTaskPriority.HIGH.value,
        ))
        tasks.append(await AutomotiveOperationsEngineV1._create_task(
            session,
            operation_id=operation.id,
            vehicle_id=vehicle.id,
            task_type=VehicleTaskType.DELIVERY.value,
            title=f"Schedule delivery for {vehicle.stock_number}",
            assigned_to=manager,
        ))
        tasks.append(await AutomotiveOperationsEngineV1._create_task(
            session,
            operation_id=operation.id,
            vehicle_id=vehicle.id,
            task_type=VehicleTaskType.RELEASE_RESERVATION.value,
            title=f"Release reservations for {vehicle.stock_number}",
            assigned_to=manager,
        ))
        tasks.append(await AutomotiveOperationsEngineV1._create_task(
            session,
            operation_id=operation.id,
            vehicle_id=vehicle.id,
            task_type=VehicleTaskType.ACCOUNTING_ENTRY.value,
            title=f"Create accounting entries for {vehicle.stock_number}",
            assigned_to=manager,
        ))

        try:
            from services.pg_settlement_engine import SettlementEngineV1

            amount = vehicle.sale_price or vehicle.target_price or Decimal("0")
            if amount > 0:
                await SettlementEngineV1.create_settlement(
                    actor_id,
                    settlement_type="BANK",
                    asset=vehicle.currency,
                    amount=amount,
                    reference=f"sale-{vehicle.stock_number}",
                )
        except Exception:
            pass

        try:
            from services.pg_automotive_cost_engine import AutomotiveCostEngineV1

            await AutomotiveCostEngineV1.recalculate_vehicle_costs(
                actor_id,
                vehicle.id,
            )
        except Exception:
            pass

        return [AutomotiveOperationsEngineV1._task_snapshot(t) for t in tasks]

    @staticmethod
    async def create_operation(
        actor_id: int,
        vehicle_id: uuid.UUID,
        *,
        assigned_manager_id: int | None = None,
        initial_state: str = VehicleOperationState.PROCUREMENT.value,
        metadata: dict | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveOperationsEngineV1.user_can_access(actor_id):
            raise AutomotiveOperationsEngineError("Access denied")

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveOperationsEngineError(f"Vehicle not found: {vehicle_id}")

            op_repo = VehicleOperationRepository(session)
            if await op_repo.get_by_vehicle(vehicle_id):
                raise AutomotiveOperationsEngineError(
                    f"Operation already exists for vehicle: {vehicle_id}"
                )

            operation = await op_repo.create(
                vehicle_id=vehicle_id,
                current_state=initial_state,
                assigned_manager_id=assigned_manager_id,
                sla_deadline=AutomotiveOperationsEngineV1._state_sla_deadline(
                    initial_state
                ),
                metadata=metadata,
                notes=notes,
            )

            await VehicleStateHistoryRepository(session).record(
                operation_id=operation.id,
                vehicle_id=vehicle_id,
                from_state=None,
                to_state=initial_state,
                changed_by=actor_id,
                notes="Operation created",
            )

            workflow_tasks: list[dict[str, Any]] = []
            if initial_state == VehicleOperationState.PROCUREMENT.value:
                workflow_tasks = await AutomotiveOperationsEngineV1._run_purchased_workflow(
                    session,
                    actor_id,
                    operation,
                    vehicle,
                    assigned_manager_id,
                )

            await AutomotiveOperationsEngineV1._audit(
                session,
                user_id=actor_id,
                entity_id=str(operation.id),
                action=AuditAction.CREATE.value,
                new_value={"vehicle_id": str(vehicle_id), "state": initial_state},
            )

            snapshot = AutomotiveOperationsEngineV1._operation_snapshot(operation)

        await AutomotiveOperationsEngineV1._publish_event(
            "vehicle.created",
            vehicle_id,
            {
                "vehicle_id": str(vehicle_id),
                "operation_id": snapshot["id"],
                "state": initial_state,
            },
        )

        return {
            "operation": snapshot,
            "workflow_tasks": workflow_tasks,
        }

    @staticmethod
    async def transition_state(
        actor_id: int,
        operation_id: uuid.UUID,
        new_state: str,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveOperationsEngineV1.user_can_access(actor_id):
            raise AutomotiveOperationsEngineError("Access denied")

        if new_state not in {s.value for s in VehicleOperationState}:
            raise AutomotiveOperationsEngineError(f"Invalid state: {new_state}")

        workflow_tasks: list[dict[str, Any]] = []
        event_type: str | None = None
        vehicle_id: uuid.UUID

        async with get_session() as session:
            op_repo = VehicleOperationRepository(session)
            operation = await op_repo.get_by_id(operation_id)
            if operation is None:
                raise AutomotiveOperationsEngineError(
                    f"Operation not found: {operation_id}"
                )

            allowed = STATE_TRANSITIONS.get(operation.current_state, frozenset())
            if new_state not in allowed:
                raise AutomotiveOperationsEngineError(
                    f"Invalid transition: {operation.current_state} -> {new_state}"
                )

            old_state = operation.current_state
            vehicle_id = operation.vehicle_id
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveOperationsEngineError(f"Vehicle not found: {vehicle_id}")

            operation = await op_repo.update_state(
                operation_id,
                current_state=new_state,
                sla_deadline=AutomotiveOperationsEngineV1._state_sla_deadline(new_state),
            )

            await VehicleStateHistoryRepository(session).record(
                operation_id=operation_id,
                vehicle_id=vehicle_id,
                from_state=old_state,
                to_state=new_state,
                changed_by=actor_id,
                notes=notes,
            )

            if new_state == VehicleOperationState.WAREHOUSE.value:
                workflow_tasks = await AutomotiveOperationsEngineV1._run_arrived_workflow(
                    session, actor_id, operation, vehicle
                )
                event_type = "vehicle.arrived"
            elif new_state == VehicleOperationState.LISTED_FOR_SALE.value:
                workflow_tasks = await AutomotiveOperationsEngineV1._run_listed_workflow(
                    session, actor_id, operation, vehicle
                )
                event_type = "vehicle.listed"
            elif new_state == VehicleOperationState.RESERVED.value:
                event_type = "vehicle.reserved"
            elif new_state == VehicleOperationState.SOLD.value:
                workflow_tasks = await AutomotiveOperationsEngineV1._run_sold_workflow(
                    session, actor_id, operation, vehicle
                )
                event_type = "vehicle.sold"
            elif new_state == VehicleOperationState.DELIVERED.value:
                event_type = "vehicle.delivered"

            await AutomotiveOperationsEngineV1._audit(
                session,
                user_id=actor_id,
                entity_id=str(operation_id),
                action=AuditAction.STATUS_CHANGE.value,
                old_value={"state": old_state},
                new_value={"state": new_state},
            )

            snapshot = AutomotiveOperationsEngineV1._operation_snapshot(operation)

        await AutomotiveOperationsEngineV1._sync_inventory_status(
            actor_id, vehicle_id, new_state
        )

        if event_type:
            await AutomotiveOperationsEngineV1._publish_event(
                event_type,
                vehicle_id,
                {
                    "vehicle_id": str(vehicle_id),
                    "operation_id": str(operation_id),
                    "from_state": old_state,
                    "to_state": new_state,
                },
            )

        return {
            "operation": snapshot,
            "workflow_tasks": workflow_tasks,
        }

    @staticmethod
    async def assign_manager(
        actor_id: int,
        operation_id: uuid.UUID,
        manager_id: int,
    ) -> dict[str, Any]:
        if not await AutomotiveOperationsEngineV1.user_can_access(actor_id):
            raise AutomotiveOperationsEngineError("Access denied")

        async with get_session() as session:
            operation = await VehicleOperationRepository(session).assign_manager(
                operation_id,
                manager_id,
            )
            if operation is None:
                raise AutomotiveOperationsEngineError(
                    f"Operation not found: {operation_id}"
                )

            await AutomotiveOperationsEngineV1._audit(
                session,
                user_id=actor_id,
                entity_id=str(operation_id),
                action=AuditAction.ASSIGN.value,
                new_value={"assigned_manager_id": manager_id},
            )

            return AutomotiveOperationsEngineV1._operation_snapshot(operation)

    @staticmethod
    async def create_task(
        actor_id: int,
        operation_id: uuid.UUID,
        *,
        task_type: str,
        title: str,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveOperationsEngineV1.user_can_access(actor_id):
            raise AutomotiveOperationsEngineError("Access denied")

        async with get_session() as session:
            operation = await VehicleOperationRepository(session).get_by_id(operation_id)
            if operation is None:
                raise AutomotiveOperationsEngineError(
                    f"Operation not found: {operation_id}"
                )

            task = await AutomotiveOperationsEngineV1._create_task(
                session,
                operation_id=operation_id,
                vehicle_id=operation.vehicle_id,
                task_type=task_type,
                title=title,
                auto_generated=False,
                assigned_to=fields.get("assigned_to"),
                priority=fields.get("priority", VehicleTaskPriority.NORMAL.value),
                metadata=fields.get("metadata"),
                notes=fields.get("notes"),
            )
            return AutomotiveOperationsEngineV1._task_snapshot(task)

    @staticmethod
    async def complete_task(
        actor_id: int,
        task_id: uuid.UUID,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveOperationsEngineV1.user_can_access(actor_id):
            raise AutomotiveOperationsEngineError("Access denied")

        async with get_session() as session:
            repo = VehicleTaskRepository(session)
            task = await repo.get_by_id(task_id)
            if task is None:
                raise AutomotiveOperationsEngineError(f"Task not found: {task_id}")

            task = await repo.update_status(
                task_id,
                VehicleTaskStatus.COMPLETED.value,
            )
            if notes:
                task.notes = notes
                await session.flush()

            await AutomotiveOperationsEngineV1._audit(
                session,
                user_id=actor_id,
                entity_id=str(task_id),
                action=AuditAction.STATUS_CHANGE.value,
                new_value={"status": VehicleTaskStatus.COMPLETED.value},
            )

            return AutomotiveOperationsEngineV1._task_snapshot(task)

    @staticmethod
    async def complete_checklist_item(
        actor_id: int,
        checklist_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveOperationsEngineV1.user_can_access(actor_id):
            raise AutomotiveOperationsEngineError("Access denied")

        async with get_session() as session:
            item = await VehicleChecklistRepository(session).complete(
                checklist_id,
                actor_id,
            )
            if item is None:
                raise AutomotiveOperationsEngineError(
                    f"Checklist item not found: {checklist_id}"
                )
            return AutomotiveOperationsEngineV1._checklist_snapshot(item)

    @staticmethod
    async def add_attachment(
        actor_id: int,
        operation_id: uuid.UUID,
        *,
        file_url: str,
        attachment_type: str,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveOperationsEngineV1.user_can_access(actor_id):
            raise AutomotiveOperationsEngineError("Access denied")

        async with get_session() as session:
            operation = await VehicleOperationRepository(session).get_by_id(operation_id)
            if operation is None:
                raise AutomotiveOperationsEngineError(
                    f"Operation not found: {operation_id}"
                )

            attachment = await VehicleAttachmentRepository(session).create(
                operation_id=operation_id,
                vehicle_id=operation.vehicle_id,
                file_url=file_url,
                attachment_type=attachment_type,
                uploaded_by=actor_id,
                **fields,
            )

            await AutomotiveOperationsEngineV1._audit(
                session,
                user_id=actor_id,
                entity_id=str(operation_id),
                action=AuditAction.DOCUMENT_UPLOADED.value,
                new_value={"file_url": file_url, "type": attachment_type},
            )

            return AutomotiveOperationsEngineV1._attachment_snapshot(attachment)

    @staticmethod
    async def mark_overdue_tasks(actor_id: int) -> list[dict[str, Any]]:
        if not await AutomotiveOperationsEngineV1.user_can_access(actor_id):
            raise AutomotiveOperationsEngineError("Access denied")

        now = datetime.now(timezone.utc)
        updated: list[dict[str, Any]] = []

        async with get_session() as session:
            repo = VehicleTaskRepository(session)
            overdue = await repo.list_overdue(now)
            for task in overdue:
                if task.status == VehicleTaskStatus.OVERDUE.value:
                    continue
                task = await repo.update_status(
                    task.id,
                    VehicleTaskStatus.OVERDUE.value,
                )
                updated.append(AutomotiveOperationsEngineV1._task_snapshot(task))

        return updated

    @staticmethod
    async def get_operation(
        actor_id: int,
        operation_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveOperationsEngineV1.user_can_access(actor_id):
            raise AutomotiveOperationsEngineError("Access denied")

        async with get_session() as session:
            operation = await VehicleOperationRepository(session).get_by_id(operation_id)
            if operation is None:
                raise AutomotiveOperationsEngineError(
                    f"Operation not found: {operation_id}"
                )

            history = await VehicleStateHistoryRepository(session).list_by_operation(
                operation_id
            )
            tasks = await VehicleTaskRepository(session).list_by_operation(operation_id)
            checklists = await VehicleChecklistRepository(session).list_by_operation(
                operation_id
            )
            attachments = await VehicleAttachmentRepository(session).list_by_operation(
                operation_id
            )

            return {
                "operation": AutomotiveOperationsEngineV1._operation_snapshot(operation),
                "state_history": [
                    AutomotiveOperationsEngineV1._state_history_snapshot(h)
                    for h in history
                ],
                "tasks": [AutomotiveOperationsEngineV1._task_snapshot(t) for t in tasks],
                "checklists": [
                    AutomotiveOperationsEngineV1._checklist_snapshot(c) for c in checklists
                ],
                "attachments": [
                    AutomotiveOperationsEngineV1._attachment_snapshot(a)
                    for a in attachments
                ],
            }

    @staticmethod
    async def list_operations_by_state(
        actor_id: int,
        state: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveOperationsEngineV1.user_can_access(actor_id):
            raise AutomotiveOperationsEngineError("Access denied")

        async with get_session() as session:
            operations = await VehicleOperationRepository(session).list_by_state(
                state,
                limit=limit,
            )
            return [
                AutomotiveOperationsEngineV1._operation_snapshot(op) for op in operations
            ]

    @staticmethod
    async def advance_lifecycle(
        actor_id: int,
        operation_id: uuid.UUID,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveOperationsEngineV1.user_can_access(actor_id):
            raise AutomotiveOperationsEngineError("Access denied")

        async with get_session() as session:
            operation = await VehicleOperationRepository(session).get_by_id(operation_id)
            if operation is None:
                raise AutomotiveOperationsEngineError(
                    f"Operation not found: {operation_id}"
                )
            allowed = STATE_TRANSITIONS.get(operation.current_state, frozenset())
            if not allowed:
                raise AutomotiveOperationsEngineError(
                    f"No forward transition from {operation.current_state}"
                )
            next_state = sorted(allowed)[0]

        return await AutomotiveOperationsEngineV1.transition_state(
            actor_id,
            operation_id,
            next_state,
            notes=notes,
        )
