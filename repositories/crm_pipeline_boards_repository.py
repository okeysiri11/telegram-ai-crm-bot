# CRM Pipeline Boards v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.crm_pipeline_boards_v1 import (
    CrmPipelineBoardStage,
    CrmPipelineBoardTransition,
    CrmPipelineEntityType,
)
from database.models.deal_engine_v1 import DealEngineV1Deal
from database.models.lead_engine import LeadEngineLead


class CrmPipelineBoardsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_stages(self, vertical: str) -> list[CrmPipelineBoardStage]:
        result = await self._session.execute(
            select(CrmPipelineBoardStage)
            .where(CrmPipelineBoardStage.vertical == vertical)
            .order_by(CrmPipelineBoardStage.order_index)
        )
        return list(result.scalars().all())

    async def get_stage(self, vertical: str, stage_code: str) -> CrmPipelineBoardStage | None:
        result = await self._session.execute(
            select(CrmPipelineBoardStage).where(
                CrmPipelineBoardStage.vertical == vertical,
                CrmPipelineBoardStage.stage_code == stage_code,
            )
        )
        return result.scalar_one_or_none()

    async def count_stages(self, vertical: str) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(CrmPipelineBoardStage)
            .where(CrmPipelineBoardStage.vertical == vertical)
        )
        return int(result.scalar_one())

    async def log_transition(
        self,
        *,
        vertical: str,
        entity_type: str,
        entity_id: uuid.UUID,
        previous_stage: str | None,
        new_stage: str,
        moved_by: int,
        pipeline_stage_id: uuid.UUID | None = None,
        moved_at: datetime | None = None,
    ) -> CrmPipelineBoardTransition:
        row = CrmPipelineBoardTransition(
            vertical=vertical,
            entity_type=entity_type,
            entity_id=entity_id,
            previous_stage=previous_stage,
            new_stage=new_stage,
            moved_by=moved_by,
            pipeline_stage_id=pipeline_stage_id,
            moved_at=moved_at or datetime.now(timezone.utc),
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_leads_by_stage(
        self,
        vertical: str,
        *,
        limit_per_stage: int = 5,
    ) -> dict[str, list[LeadEngineLead]]:
        stages = await self.list_stages(vertical)
        grouped: dict[str, list[LeadEngineLead]] = {}
        for stage in stages:
            result = await self._session.execute(
                select(LeadEngineLead)
                .where(
                    LeadEngineLead.vertical == vertical,
                    LeadEngineLead.pipeline_stage == stage.stage_code,
                )
                .order_by(LeadEngineLead.created_at.desc())
                .limit(limit_per_stage)
            )
            grouped[stage.stage_code] = list(result.scalars().all())
        return grouped

    async def list_deals_by_stage(
        self,
        vertical: str,
        *,
        limit_per_stage: int = 5,
    ) -> dict[str, list[DealEngineV1Deal]]:
        stages = await self.list_stages(vertical)
        grouped: dict[str, list[DealEngineV1Deal]] = {}
        for stage in stages:
            result = await self._session.execute(
                select(DealEngineV1Deal)
                .where(
                    DealEngineV1Deal.vertical == vertical,
                    DealEngineV1Deal.pipeline_stage == stage.stage_code,
                )
                .order_by(DealEngineV1Deal.created_at.desc())
                .limit(limit_per_stage)
            )
            grouped[stage.stage_code] = list(result.scalars().all())
        return grouped

    async def count_leads_by_stage(self, vertical: str) -> list[tuple[str, int]]:
        stmt = (
            select(LeadEngineLead.pipeline_stage, func.count())
            .where(LeadEngineLead.vertical == vertical)
            .group_by(LeadEngineLead.pipeline_stage)
            .order_by(func.count().desc())
        )
        result = await self._session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]

    async def count_deals_by_stage(self, vertical: str) -> list[tuple[str, int]]:
        stmt = (
            select(DealEngineV1Deal.pipeline_stage, func.count())
            .where(DealEngineV1Deal.vertical == vertical)
            .group_by(DealEngineV1Deal.pipeline_stage)
            .order_by(func.count().desc())
        )
        result = await self._session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]

    async def conversion_from_transitions(
        self,
        vertical: str,
        *,
        win_stages: frozenset[str],
    ) -> list[tuple[str | None, int, int]]:
        stmt = (
            select(
                CrmPipelineBoardTransition.previous_stage,
                func.count(),
            )
            .where(CrmPipelineBoardTransition.vertical == vertical)
            .group_by(CrmPipelineBoardTransition.previous_stage)
        )
        result = await self._session.execute(stmt)
        totals = {row[0]: int(row[1]) for row in result.all()}

        win_stmt = (
            select(
                CrmPipelineBoardTransition.previous_stage,
                func.count(),
            )
            .where(
                CrmPipelineBoardTransition.vertical == vertical,
                CrmPipelineBoardTransition.new_stage.in_(tuple(win_stages)),
                CrmPipelineBoardTransition.previous_stage.is_not(None),
            )
            .group_by(CrmPipelineBoardTransition.previous_stage)
        )
        win_result = await self._session.execute(win_stmt)
        wins = {row[0]: int(row[1]) for row in win_result.all()}

        rows: list[tuple[str | None, int, int]] = []
        for stage, total in totals.items():
            rows.append((stage, total, wins.get(stage, 0)))
        return rows

    async def get_lead(self, lead_id: uuid.UUID) -> LeadEngineLead | None:
        result = await self._session.execute(
            select(LeadEngineLead).where(LeadEngineLead.id == lead_id)
        )
        return result.scalar_one_or_none()

    async def get_deal(self, deal_id: uuid.UUID) -> DealEngineV1Deal | None:
        result = await self._session.execute(
            select(DealEngineV1Deal).where(DealEngineV1Deal.id == deal_id)
        )
        return result.scalar_one_or_none()

    async def update_lead_stage(self, lead_id: uuid.UUID, stage_code: str) -> LeadEngineLead | None:
        row = await self.get_lead(lead_id)
        if row is None:
            return None
        row.pipeline_stage = stage_code
        if stage_code in {"WON", "LOST"}:
            row.status = stage_code
        elif stage_code == "CLOSED":
            row.status = "WON"
        await self._session.flush()
        return row

    async def update_deal_stage(self, deal_id: uuid.UUID, stage_code: str) -> DealEngineV1Deal | None:
        row = await self.get_deal(deal_id)
        if row is None:
            return None
        row.pipeline_stage = stage_code
        if stage_code in {"WON", "CLOSED"}:
            row.status = "COMPLETED"
        elif stage_code == "LOST":
            row.status = "CANCELLED"
        await self._session.flush()
        return row

    async def count_entities_in_stage(
        self,
        vertical: str,
        entity_type: str,
        stage_code: str,
    ) -> int:
        if entity_type == CrmPipelineEntityType.LEAD.value:
            stmt = (
                select(func.count())
                .select_from(LeadEngineLead)
                .where(
                    LeadEngineLead.vertical == vertical,
                    LeadEngineLead.pipeline_stage == stage_code,
                )
            )
        else:
            stmt = (
                select(func.count())
                .select_from(DealEngineV1Deal)
                .where(
                    DealEngineV1Deal.vertical == vertical,
                    DealEngineV1Deal.pipeline_stage == stage_code,
                )
            )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
