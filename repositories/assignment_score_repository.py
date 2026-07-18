# Assignment score repository — learning dataset and statistics.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select

from database.models.assignment_score import AssignmentScore
from database.models.platform_metrics import RequestMetric
from database.models.users import User
from models.assignment_score import AssignmentRecordSnapshot
from src.platform.layers.base_repository import BaseRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _record_snapshot(row: AssignmentScore) -> AssignmentRecordSnapshot:
    return AssignmentRecordSnapshot(
        id=str(row.id),
        request_id=str(row.request_id) if row.request_id else None,
        request_number=row.request_number,
        manager_pool_id=str(row.manager_pool_id),
        manager_user_id=str(row.manager_user_id) if row.manager_user_id else None,
        manager_telegram_id=int(row.manager_telegram_id),
        segment=row.segment,
        score=float(row.score),
        strategy=row.strategy,
        assignment_time=row.assignment_time,
        completed=bool(row.completed),
        response_time_seconds=row.response_time_seconds,
        resolution_time_seconds=row.resolution_time_seconds,
        specialization=row.specialization,
    )


class AssignmentScoreRepository(BaseRepository):
    async def create_record(
        self,
        *,
        request_id: uuid.UUID | str | None,
        request_number: str | None,
        manager_pool_id: uuid.UUID | str,
        manager_user_id: uuid.UUID | str | None,
        manager_telegram_id: int,
        segment: str,
        score: float,
        strategy: str,
        specialization: str | None = None,
        assignment_time: datetime | None = None,
    ) -> AssignmentRecordSnapshot:
        row = AssignmentScore(
            request_id=uuid.UUID(str(request_id)) if request_id else None,
            request_number=request_number,
            manager_pool_id=uuid.UUID(str(manager_pool_id)),
            manager_user_id=uuid.UUID(str(manager_user_id)) if manager_user_id else None,
            manager_telegram_id=manager_telegram_id,
            segment=segment,
            specialization=specialization,
            score=float(score),
            strategy=strategy,
            assignment_time=assignment_time or _utcnow(),
            completed=False,
        )
        self.session.add(row)
        await self.session.flush()
        return _record_snapshot(row)

    async def get_by_request_id(self, request_id: uuid.UUID | str) -> AssignmentRecordSnapshot | None:
        rid = uuid.UUID(str(request_id))
        result = await self.session.execute(
            select(AssignmentScore)
            .where(AssignmentScore.request_id == rid)
            .order_by(AssignmentScore.assignment_time.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return _record_snapshot(row) if row else None

    async def mark_completed(
        self,
        assignment_id: uuid.UUID | str,
        *,
        response_time_seconds: int | None = None,
        resolution_time_seconds: int | None = None,
    ) -> AssignmentRecordSnapshot | None:
        aid = uuid.UUID(str(assignment_id))
        result = await self.session.execute(
            select(AssignmentScore).where(AssignmentScore.id == aid)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.completed = True
        if response_time_seconds is not None:
            row.response_time_seconds = response_time_seconds
        if resolution_time_seconds is not None:
            row.resolution_time_seconds = resolution_time_seconds
        await self.session.flush()
        return _record_snapshot(row)

    async def mark_completed_by_request(
        self,
        request_id: uuid.UUID | str,
        *,
        response_time_seconds: int | None = None,
        resolution_time_seconds: int | None = None,
    ) -> AssignmentRecordSnapshot | None:
        record = await self.get_by_request_id(request_id)
        if record is None:
            return None
        return await self.mark_completed(
            record.id,
            response_time_seconds=response_time_seconds,
            resolution_time_seconds=resolution_time_seconds,
        )

    async def count_completed_for_manager(self, manager_pool_id: uuid.UUID | str) -> int:
        pid = uuid.UUID(str(manager_pool_id))
        result = await self.session.execute(
            select(func.count())
            .select_from(AssignmentScore)
            .where(
                AssignmentScore.manager_pool_id == pid,
                AssignmentScore.completed.is_(True),
            )
        )
        return int(result.scalar_one() or 0)

    async def average_response_for_manager(self, manager_telegram_id: int) -> float | None:
        result = await self.session.execute(
            select(func.avg(AssignmentScore.response_time_seconds)).where(
                AssignmentScore.manager_telegram_id == manager_telegram_id,
                AssignmentScore.response_time_seconds.is_not(None),
            )
        )
        val = result.scalar_one_or_none()
        return float(val) if val is not None else None

    async def average_response_from_metrics(self, manager_telegram_id: int) -> float | None:
        result = await self.session.execute(
            select(func.avg(RequestMetric.time_to_first_response_seconds)).where(
                RequestMetric.manager_id.in_(
                    select(User.id).where(User.telegram_id == manager_telegram_id)
                ),
                RequestMetric.time_to_first_response_seconds.is_not(None),
            )
        )
        val = result.scalar_one_or_none()
        return float(val) if val is not None else None

    async def get_statistics(self) -> dict[str, Any]:
        total = (
            await self.session.execute(select(func.count()).select_from(AssignmentScore))
        ).scalar_one()
        avg_score = (
            await self.session.execute(select(func.avg(AssignmentScore.score)))
        ).scalar_one()
        completed = (
            await self.session.execute(
                select(func.count())
                .select_from(AssignmentScore)
                .where(AssignmentScore.completed.is_(True))
            )
        ).scalar_one()
        failures = (
            await self.session.execute(
                select(func.count())
                .select_from(AssignmentScore)
                .where(AssignmentScore.score <= 0)
            )
        ).scalar_one()

        segment_rows = (
            await self.session.execute(
                select(AssignmentScore.segment, func.count())
                .group_by(AssignmentScore.segment)
                .order_by(func.count().desc())
            )
        ).all()
        segment_distribution = {row[0]: int(row[1]) for row in segment_rows}

        strategy_rows = (
            await self.session.execute(
                select(AssignmentScore.strategy, func.count())
                .group_by(AssignmentScore.strategy)
            )
        ).all()
        strategy_counts = {row[0]: int(row[1]) for row in strategy_rows}

        specialization_rows = (
            await self.session.execute(
                select(AssignmentScore.specialization, func.count(), func.avg(AssignmentScore.score))
                .where(AssignmentScore.specialization.is_not(None))
                .group_by(AssignmentScore.specialization)
            )
        ).all()
        specialization_efficiency = {
            row[0]: {"count": int(row[1]), "average_score": round(float(row[2] or 0), 4)}
            for row in specialization_rows
        }

        manager_rows = (
            await self.session.execute(
                select(
                    AssignmentScore.manager_pool_id,
                    func.count(),
                    func.avg(AssignmentScore.score),
                )
                .group_by(AssignmentScore.manager_pool_id)
            )
        ).all()
        manager_utilization = {
            str(row[0]): {
                "assignments": int(row[1]),
                "average_score": round(float(row[2] or 0), 4),
            }
            for row in manager_rows
        }

        matched = (
            await self.session.execute(
                select(func.count())
                .select_from(AssignmentScore)
                .where(
                    AssignmentScore.specialization.is_not(None),
                    AssignmentScore.segment == AssignmentScore.specialization,
                )
            )
        ).scalar_one()
        specialization_accuracy = round(float(matched) / max(int(total or 0), 1), 4)

        return {
            "total_assignments": int(total or 0),
            "average_score": round(float(avg_score or 0), 4),
            "completed_assignments": int(completed or 0),
            "assignment_failures": int(failures or 0),
            "segment_distribution": segment_distribution,
            "strategy_counts": strategy_counts,
            "specialization_efficiency": specialization_efficiency,
            "manager_utilization": manager_utilization,
            "specialization_accuracy": specialization_accuracy,
        }
