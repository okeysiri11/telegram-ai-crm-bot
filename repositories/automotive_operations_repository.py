# Automotive Operations Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_operations import (
    VehicleAttachment,
    VehicleAttachmentType,
    VehicleChecklist,
    VehicleOperation,
    VehicleOperationState,
    VehicleStateHistory,
    VehicleTask,
    VehicleTaskPriority,
    VehicleTaskStatus,
    VehicleTaskType,
)


class VehicleOperationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        vehicle_id: uuid.UUID,
        current_state: str = VehicleOperationState.PROCUREMENT.value,
        assigned_manager_id: int | None = None,
        state_entered_at: datetime | None = None,
        sla_deadline: datetime | None = None,
        metadata: dict | None = None,
        notes: str | None = None,
        **extra: Any,
    ) -> VehicleOperation:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if current_state not in {s.value for s in VehicleOperationState}:
            raise ValueError(f"Invalid current_state: {current_state}")

        operation = VehicleOperation(
            vehicle_id=vehicle_id,
            current_state=current_state,
            assigned_manager_id=assigned_manager_id,
            state_entered_at=state_entered_at or datetime.now(timezone.utc),
            sla_deadline=sla_deadline,
            metadata_=metadata,
            notes=notes,
        )
        self._session.add(operation)
        await self._session.flush()
        return operation

    async def get_by_id(self, operation_id: uuid.UUID) -> VehicleOperation | None:
        result = await self._session.execute(
            select(VehicleOperation).where(VehicleOperation.id == operation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_vehicle(self, vehicle_id: uuid.UUID) -> VehicleOperation | None:
        result = await self._session.execute(
            select(VehicleOperation).where(VehicleOperation.vehicle_id == vehicle_id)
        )
        return result.scalar_one_or_none()

    async def update_state(
        self,
        operation_id: uuid.UUID,
        *,
        current_state: str,
        state_entered_at: datetime | None = None,
        sla_deadline: datetime | None = None,
    ) -> VehicleOperation | None:
        operation = await self.get_by_id(operation_id)
        if operation is None:
            return None
        if current_state not in {s.value for s in VehicleOperationState}:
            raise ValueError(f"Invalid current_state: {current_state}")

        operation.current_state = current_state
        operation.state_entered_at = state_entered_at or datetime.now(timezone.utc)
        if sla_deadline is not None:
            operation.sla_deadline = sla_deadline
        operation.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return operation

    async def assign_manager(
        self,
        operation_id: uuid.UUID,
        manager_id: int,
    ) -> VehicleOperation | None:
        operation = await self.get_by_id(operation_id)
        if operation is None:
            return None
        operation.assigned_manager_id = manager_id
        operation.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return operation

    async def list_by_state(
        self,
        current_state: str,
        *,
        limit: int = 100,
    ) -> list[VehicleOperation]:
        result = await self._session.execute(
            select(VehicleOperation)
            .where(
                VehicleOperation.current_state == current_state,
                VehicleOperation.is_active.is_(True),
            )
            .order_by(VehicleOperation.state_entered_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_overdue_sla(
        self,
        now: datetime,
        *,
        limit: int = 100,
    ) -> list[VehicleOperation]:
        result = await self._session.execute(
            select(VehicleOperation)
            .where(
                VehicleOperation.is_active.is_(True),
                VehicleOperation.sla_deadline.is_not(None),
                VehicleOperation.sla_deadline < now,
            )
            .order_by(VehicleOperation.sla_deadline.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


class VehicleStateHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        operation_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        to_state: str,
        from_state: str | None = None,
        changed_by: int | None = None,
        notes: str | None = None,
    ) -> VehicleStateHistory:
        entry = VehicleStateHistory(
            operation_id=operation_id,
            vehicle_id=vehicle_id,
            from_state=from_state,
            to_state=to_state,
            changed_by=changed_by,
            notes=notes,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_by_operation(
        self,
        operation_id: uuid.UUID,
    ) -> list[VehicleStateHistory]:
        result = await self._session.execute(
            select(VehicleStateHistory)
            .where(VehicleStateHistory.operation_id == operation_id)
            .order_by(VehicleStateHistory.created_at.asc())
        )
        return list(result.scalars().all())


class VehicleTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        operation_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        task_type: str,
        title: str,
        status: str = VehicleTaskStatus.PENDING.value,
        priority: str = VehicleTaskPriority.NORMAL.value,
        assigned_to: int | None = None,
        sla_deadline: datetime | None = None,
        auto_generated: bool = False,
        metadata: dict | None = None,
        notes: str | None = None,
        **extra: Any,
    ) -> VehicleTask:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if task_type not in {t.value for t in VehicleTaskType}:
            raise ValueError(f"Invalid task_type: {task_type}")
        if status not in {s.value for s in VehicleTaskStatus}:
            raise ValueError(f"Invalid status: {status}")

        task = VehicleTask(
            operation_id=operation_id,
            vehicle_id=vehicle_id,
            task_type=task_type,
            title=title,
            status=status,
            priority=priority,
            assigned_to=assigned_to,
            sla_deadline=sla_deadline,
            auto_generated=auto_generated,
            metadata_=metadata,
            notes=notes,
        )
        self._session.add(task)
        await self._session.flush()
        return task

    async def get_by_id(self, task_id: uuid.UUID) -> VehicleTask | None:
        result = await self._session.execute(
            select(VehicleTask).where(VehicleTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        task_id: uuid.UUID,
        status: str,
        *,
        completed_at: datetime | None = None,
    ) -> VehicleTask | None:
        task = await self.get_by_id(task_id)
        if task is None:
            return None
        if status not in {s.value for s in VehicleTaskStatus}:
            raise ValueError(f"Invalid status: {status}")

        task.status = status
        if status == VehicleTaskStatus.COMPLETED.value:
            task.completed_at = completed_at or datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return task

    async def assign(
        self,
        task_id: uuid.UUID,
        assigned_to: int,
    ) -> VehicleTask | None:
        task = await self.get_by_id(task_id)
        if task is None:
            return None
        task.assigned_to = assigned_to
        task.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return task

    async def list_by_operation(
        self,
        operation_id: uuid.UUID,
    ) -> list[VehicleTask]:
        result = await self._session.execute(
            select(VehicleTask)
            .where(VehicleTask.operation_id == operation_id)
            .order_by(VehicleTask.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_overdue(
        self,
        now: datetime,
        *,
        limit: int = 100,
    ) -> list[VehicleTask]:
        result = await self._session.execute(
            select(VehicleTask)
            .where(
                VehicleTask.status.in_([
                    VehicleTaskStatus.PENDING.value,
                    VehicleTaskStatus.IN_PROGRESS.value,
                ]),
                VehicleTask.sla_deadline.is_not(None),
                VehicleTask.sla_deadline < now,
            )
            .order_by(VehicleTask.sla_deadline.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


class VehicleChecklistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        operation_id: uuid.UUID,
        item_key: str,
        label: str,
        task_id: uuid.UUID | None = None,
        is_required: bool = True,
        sort_order: int = 0,
    ) -> VehicleChecklist:
        item = VehicleChecklist(
            operation_id=operation_id,
            task_id=task_id,
            item_key=item_key,
            label=label,
            is_required=is_required,
            sort_order=sort_order,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def complete(
        self,
        checklist_id: uuid.UUID,
        completed_by: int,
    ) -> VehicleChecklist | None:
        result = await self._session.execute(
            select(VehicleChecklist).where(VehicleChecklist.id == checklist_id)
        )
        item = result.scalar_one_or_none()
        if item is None:
            return None
        item.is_completed = True
        item.completed_at = datetime.now(timezone.utc)
        item.completed_by = completed_by
        item.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return item

    async def list_by_operation(
        self,
        operation_id: uuid.UUID,
    ) -> list[VehicleChecklist]:
        result = await self._session.execute(
            select(VehicleChecklist)
            .where(VehicleChecklist.operation_id == operation_id)
            .order_by(VehicleChecklist.sort_order.asc())
        )
        return list(result.scalars().all())


class VehicleAttachmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        operation_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        file_url: str,
        attachment_type: str,
        task_id: uuid.UUID | None = None,
        filename: str | None = None,
        uploaded_by: int | None = None,
        notes: str | None = None,
    ) -> VehicleAttachment:
        if attachment_type not in {t.value for t in VehicleAttachmentType}:
            raise ValueError(f"Invalid attachment_type: {attachment_type}")

        attachment = VehicleAttachment(
            operation_id=operation_id,
            vehicle_id=vehicle_id,
            task_id=task_id,
            file_url=file_url,
            attachment_type=attachment_type,
            filename=filename,
            uploaded_by=uploaded_by,
            notes=notes,
        )
        self._session.add(attachment)
        await self._session.flush()
        return attachment

    async def list_by_operation(
        self,
        operation_id: uuid.UUID,
    ) -> list[VehicleAttachment]:
        result = await self._session.execute(
            select(VehicleAttachment)
            .where(VehicleAttachment.operation_id == operation_id)
            .order_by(VehicleAttachment.created_at.asc())
        )
        return list(result.scalars().all())
