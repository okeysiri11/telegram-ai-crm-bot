# Deal Pipeline Engine v2 repositories.

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.deal_pipeline_engine import (
    DEAL_PIPELINE_STAGE_CODES,
    DEAL_STATUSES,
    DEAL_TASK_STATUSES,
    DealComment,
    DealPipelineStageCode,
    DealStage,
    DealStageHistory,
    DealStatus,
    DealTask,
    DealTaskStatus,
    PipelineDeal,
)


DEFAULT_ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    DealPipelineStageCode.NEW_LEAD.value: [
        DealPipelineStageCode.CONTACTED.value,
        DealPipelineStageCode.LOST.value,
    ],
    DealPipelineStageCode.CONTACTED.value: [
        DealPipelineStageCode.QUALIFIED.value,
        DealPipelineStageCode.LOST.value,
    ],
    DealPipelineStageCode.QUALIFIED.value: [
        DealPipelineStageCode.VIEWING.value,
        DealPipelineStageCode.LOST.value,
    ],
    DealPipelineStageCode.VIEWING.value: [
        DealPipelineStageCode.NEGOTIATION.value,
        DealPipelineStageCode.LOST.value,
    ],
    DealPipelineStageCode.NEGOTIATION.value: [
        DealPipelineStageCode.RESERVED.value,
        DealPipelineStageCode.LOST.value,
    ],
    DealPipelineStageCode.RESERVED.value: [
        DealPipelineStageCode.DOCUMENTS.value,
        DealPipelineStageCode.LOST.value,
    ],
    DealPipelineStageCode.DOCUMENTS.value: [
        DealPipelineStageCode.PAYMENT.value,
        DealPipelineStageCode.LOST.value,
    ],
    DealPipelineStageCode.PAYMENT.value: [
        DealPipelineStageCode.DELIVERED.value,
        DealPipelineStageCode.LOST.value,
    ],
    DealPipelineStageCode.DELIVERED.value: [],
    DealPipelineStageCode.LOST.value: [DealPipelineStageCode.CONTACTED.value],
}


class PipelineDealRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        title: str,
        current_stage: str = DealPipelineStageCode.NEW_LEAD.value,
        sales_lead_id: uuid.UUID | None = None,
        car_id: uuid.UUID | None = None,
        assigned_manager_id: int | None = None,
        deal_value: Decimal | None = None,
        currency: str = "USD",
        sla_due_at: datetime | None = None,
        last_activity_at: datetime | None = None,
        customer_name: str | None = None,
        notes: str | None = None,
        created_by: int | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> PipelineDeal:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if current_stage not in DEAL_PIPELINE_STAGE_CODES:
            raise ValueError(f"Invalid stage: {current_stage}")

        row = PipelineDeal(
            tenant_id=tenant_id,
            company_id=company_id,
            title=title,
            current_stage=current_stage,
            sales_lead_id=sales_lead_id,
            car_id=car_id,
            assigned_manager_id=assigned_manager_id,
            deal_value=deal_value,
            currency=currency,
            sla_due_at=sla_due_at,
            last_activity_at=last_activity_at,
            customer_name=customer_name,
            notes=notes,
            created_by=created_by,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, deal_id: uuid.UUID) -> PipelineDeal | None:
        result = await self._session.execute(
            select(PipelineDeal).where(PipelineDeal.id == deal_id)
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        stage: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[PipelineDeal]:
        stmt = (
            select(PipelineDeal)
            .where(PipelineDeal.tenant_id == tenant_id)
            .order_by(PipelineDeal.updated_at.desc())
            .limit(limit)
        )
        if stage is not None:
            stmt = stmt.where(PipelineDeal.current_stage == stage)
        if status is not None:
            stmt = stmt.where(PipelineDeal.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_overdue_sla(
        self,
        tenant_id: uuid.UUID,
        *,
        before: datetime,
        limit: int = 100,
    ) -> list[PipelineDeal]:
        result = await self._session.execute(
            select(PipelineDeal)
            .where(
                PipelineDeal.tenant_id == tenant_id,
                PipelineDeal.status == DealStatus.ACTIVE.value,
                PipelineDeal.sla_due_at.is_not(None),
                PipelineDeal.sla_due_at < before,
            )
            .order_by(PipelineDeal.sla_due_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_fields(self, deal_id: uuid.UUID, **fields: Any) -> PipelineDeal | None:
        row = await self.get_by_id(deal_id)
        if row is None:
            return None
        allowed = {
            "current_stage",
            "status",
            "assigned_manager_id",
            "deal_value",
            "sla_due_at",
            "last_activity_at",
            "customer_name",
            "notes",
            "metadata_",
            "car_id",
            "sales_lead_id",
        }
        for key, value in fields.items():
            attr = "metadata_" if key == "metadata" else key
            if attr not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(row, attr, value)
        await self._session.flush()
        return row


class DealStageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        stage_code: str,
        label: str,
        sort_order: int,
        sla_hours: int,
        allowed_next_stages: list[str],
        is_terminal: bool = False,
        metadata: dict | None = None,
        **extra: Any,
    ) -> DealStage:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if stage_code not in DEAL_PIPELINE_STAGE_CODES:
            raise ValueError(f"Invalid stage_code: {stage_code}")

        row = DealStage(
            tenant_id=tenant_id,
            company_id=company_id,
            stage_code=stage_code,
            label=label,
            sort_order=sort_order,
            sla_hours=sla_hours,
            allowed_next_stages=allowed_next_stages,
            is_terminal=is_terminal,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_code(
        self,
        tenant_id: uuid.UUID,
        stage_code: str,
    ) -> DealStage | None:
        result = await self._session.execute(
            select(DealStage).where(
                DealStage.tenant_id == tenant_id,
                DealStage.stage_code == stage_code,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(self, tenant_id: uuid.UUID) -> list[DealStage]:
        result = await self._session.execute(
            select(DealStage)
            .where(DealStage.tenant_id == tenant_id)
            .order_by(DealStage.sort_order.asc())
        )
        return list(result.scalars().all())


class DealStageHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        deal_id: uuid.UUID,
        tenant_id: uuid.UUID,
        to_stage: str,
        from_stage: str | None = None,
        changed_by: int | None = None,
        validation_passed: bool = True,
        notes: str | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> DealStageHistory:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        row = DealStageHistory(
            deal_id=deal_id,
            tenant_id=tenant_id,
            from_stage=from_stage,
            to_stage=to_stage,
            changed_by=changed_by,
            validation_passed=validation_passed,
            notes=notes,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_by_deal(self, deal_id: uuid.UUID, *, limit: int = 50) -> list[DealStageHistory]:
        result = await self._session.execute(
            select(DealStageHistory)
            .where(DealStageHistory.deal_id == deal_id)
            .order_by(DealStageHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class DealTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        deal_id: uuid.UUID,
        tenant_id: uuid.UUID,
        title: str,
        task_type: str,
        description: str | None = None,
        assigned_to: int | None = None,
        due_at: datetime | None = None,
        status: str = DealTaskStatus.OPEN.value,
        auto_created: bool = False,
        created_by: int | None = None,
        **extra: Any,
    ) -> DealTask:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in DEAL_TASK_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        row = DealTask(
            deal_id=deal_id,
            tenant_id=tenant_id,
            title=title,
            task_type=task_type,
            description=description,
            assigned_to=assigned_to,
            due_at=due_at,
            status=status,
            auto_created=auto_created,
            created_by=created_by,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_by_deal(self, deal_id: uuid.UUID, *, limit: int = 50) -> list[DealTask]:
        result = await self._session.execute(
            select(DealTask)
            .where(DealTask.deal_id == deal_id)
            .order_by(DealTask.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_overdue(
        self,
        tenant_id: uuid.UUID,
        *,
        before: datetime,
        limit: int = 100,
    ) -> list[DealTask]:
        result = await self._session.execute(
            select(DealTask)
            .where(
                DealTask.tenant_id == tenant_id,
                DealTask.status == DealTaskStatus.OPEN.value,
                DealTask.due_at.is_not(None),
                DealTask.due_at < before,
            )
            .order_by(DealTask.due_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_fields(self, task_id: uuid.UUID, **fields: Any) -> DealTask | None:
        result = await self._session.execute(
            select(DealTask).where(DealTask.id == task_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        allowed = {"status", "completed_at", "assigned_to", "due_at"}
        for key, value in fields.items():
            if key not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(row, key, value)
        await self._session.flush()
        return row


class DealCommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        deal_id: uuid.UUID,
        tenant_id: uuid.UUID,
        body: str,
        author_id: int | None = None,
        is_internal: bool = True,
        metadata: dict | None = None,
        **extra: Any,
    ) -> DealComment:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        row = DealComment(
            deal_id=deal_id,
            tenant_id=tenant_id,
            body=body.strip(),
            author_id=author_id,
            is_internal=is_internal,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_by_deal(self, deal_id: uuid.UUID, *, limit: int = 50) -> list[DealComment]:
        result = await self._session.execute(
            select(DealComment)
            .where(DealComment.deal_id == deal_id)
            .order_by(DealComment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
