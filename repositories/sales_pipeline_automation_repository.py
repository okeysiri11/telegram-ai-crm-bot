# Sales Pipeline Automation Engine v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.sales_pipeline_automation_engine import (
    FOLLOW_UP_STATUSES,
    INACTIVITY_STATUSES,
    PIPELINE_STAGES,
    REMINDER_STATUSES,
    FollowUpTask,
    FollowUpStatus,
    InactivityAlert,
    InactivityAlertStatus,
    PipelineLead,
    PipelineReminder,
    PipelineStage,
    ReminderStatus,
    StageTransition,
)


class PipelineLeadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        automation_lead_id: uuid.UUID,
        car_id: uuid.UUID | None = None,
        stage: str = PipelineStage.NEW_LEAD.value,
        assigned_manager_id: int | None = None,
        last_activity_at: datetime | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> PipelineLead:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if stage not in PIPELINE_STAGES:
            raise ValueError(f"Invalid stage: {stage}")

        now = last_activity_at or datetime.now(timezone.utc)
        lead = PipelineLead(
            automation_lead_id=automation_lead_id,
            car_id=car_id,
            stage=stage,
            assigned_manager_id=assigned_manager_id,
            last_activity_at=now,
            metadata_=metadata,
        )
        self._session.add(lead)
        await self._session.flush()
        return lead

    async def get_by_id(self, pipeline_lead_id: uuid.UUID) -> PipelineLead | None:
        result = await self._session.execute(
            select(PipelineLead).where(PipelineLead.id == pipeline_lead_id)
        )
        return result.scalar_one_or_none()

    async def get_by_automation_lead(
        self,
        automation_lead_id: uuid.UUID,
    ) -> PipelineLead | None:
        result = await self._session.execute(
            select(PipelineLead).where(
                PipelineLead.automation_lead_id == automation_lead_id
            )
        )
        return result.scalar_one_or_none()

    async def list_by_stage(
        self,
        stage: str,
        *,
        limit: int = 100,
    ) -> list[PipelineLead]:
        result = await self._session.execute(
            select(PipelineLead)
            .where(PipelineLead.stage == stage)
            .order_by(PipelineLead.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_inactive(
        self,
        *,
        before: datetime,
        exclude_stages: tuple[str, ...] = (PipelineStage.SOLD.value,),
        limit: int = 100,
    ) -> list[PipelineLead]:
        query = (
            select(PipelineLead)
            .where(
                PipelineLead.last_activity_at.is_not(None),
                PipelineLead.last_activity_at <= before,
            )
            .order_by(PipelineLead.last_activity_at.asc())
            .limit(limit)
        )
        if exclude_stages:
            query = query.where(PipelineLead.stage.not_in(exclude_stages))
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        lead: PipelineLead,
        **fields: Any,
    ) -> PipelineLead:
        allowed = {
            "stage",
            "car_id",
            "assigned_manager_id",
            "last_activity_at",
            "next_follow_up_at",
            "metadata_",
        }
        unknown = set(fields) - allowed
        if unknown:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(unknown))}")
        for key, value in fields.items():
            setattr(lead, key, value)
        await self._session.flush()
        return lead


class StageTransitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        pipeline_lead_id: uuid.UUID,
        to_stage: str,
        from_stage: str | None = None,
        changed_by: int | None = None,
        notes: str | None = None,
    ) -> StageTransition:
        if to_stage not in PIPELINE_STAGES:
            raise ValueError(f"Invalid stage: {to_stage}")
        entry = StageTransition(
            pipeline_lead_id=pipeline_lead_id,
            from_stage=from_stage,
            to_stage=to_stage,
            changed_by=changed_by,
            notes=notes,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry


class PipelineReminderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        pipeline_lead_id: uuid.UUID,
        reminder_type: str,
        message: str,
        due_at: datetime,
        status: str = ReminderStatus.PENDING.value,
    ) -> PipelineReminder:
        if status not in REMINDER_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        reminder = PipelineReminder(
            pipeline_lead_id=pipeline_lead_id,
            reminder_type=reminder_type,
            message=message,
            due_at=due_at,
            status=status,
        )
        self._session.add(reminder)
        await self._session.flush()
        return reminder

    async def list_due(
        self,
        *,
        now: datetime | None = None,
        limit: int = 50,
    ) -> list[PipelineReminder]:
        due_at = now or datetime.now(timezone.utc)
        result = await self._session.execute(
            select(PipelineReminder)
            .where(
                PipelineReminder.status == ReminderStatus.PENDING.value,
                PipelineReminder.due_at <= due_at,
            )
            .order_by(PipelineReminder.due_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_sent(self, reminder: PipelineReminder) -> PipelineReminder:
        reminder.status = ReminderStatus.SENT.value
        reminder.sent_at = datetime.now(timezone.utc)
        await self._session.flush()
        return reminder


class FollowUpTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        pipeline_lead_id: uuid.UUID,
        title: str,
        description: str | None = None,
        due_at: datetime | None = None,
        assigned_to: int | None = None,
    ) -> FollowUpTask:
        task = FollowUpTask(
            pipeline_lead_id=pipeline_lead_id,
            title=title,
            description=description,
            due_at=due_at,
            assigned_to=assigned_to,
            status=FollowUpStatus.OPEN.value,
        )
        self._session.add(task)
        await self._session.flush()
        return task

    async def list_open(
        self,
        *,
        assigned_to: int | None = None,
        limit: int = 50,
    ) -> list[FollowUpTask]:
        query = (
            select(FollowUpTask)
            .where(FollowUpTask.status == FollowUpStatus.OPEN.value)
            .order_by(FollowUpTask.due_at.asc().nullsfirst())
            .limit(limit)
        )
        if assigned_to is not None:
            query = query.where(FollowUpTask.assigned_to == assigned_to)
        result = await self._session.execute(query)
        return list(result.scalars().all())


class InactivityAlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        pipeline_lead_id: uuid.UUID,
        inactive_days: int,
        message: str | None = None,
    ) -> InactivityAlert:
        alert = InactivityAlert(
            pipeline_lead_id=pipeline_lead_id,
            inactive_days=inactive_days,
            message=message,
            status=InactivityAlertStatus.OPEN.value,
            alerted_at=datetime.now(timezone.utc),
        )
        self._session.add(alert)
        await self._session.flush()
        return alert

    async def has_open_alert(self, pipeline_lead_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(InactivityAlert).where(
                InactivityAlert.pipeline_lead_id == pipeline_lead_id,
                InactivityAlert.status == InactivityAlertStatus.OPEN.value,
            )
        )
        return result.scalar_one_or_none() is not None

    async def list_open(self, *, limit: int = 50) -> list[InactivityAlert]:
        result = await self._session.execute(
            select(InactivityAlert)
            .where(InactivityAlert.status == InactivityAlertStatus.OPEN.value)
            .order_by(InactivityAlert.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
