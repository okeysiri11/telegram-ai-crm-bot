# Workflow execution repository — PostgreSQL persistence for workflow engine.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select

from database.models.workflow_execution import WorkflowExecution, WorkflowStepLog
from src.platform.layers.base_repository import BaseRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowExecutionRepository(BaseRepository):
    async def upsert(self, context) -> WorkflowExecution:
        eid = uuid.UUID(str(context.execution_id))
        result = await self.session.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == eid)
        )
        row = result.scalar_one_or_none()
        payload = context.to_dict()
        if row is None:
            row = WorkflowExecution(
                id=eid,
                workflow_id=context.workflow_id,
                vertical=context.vertical,
                status=context.status.value,
                current_step=context.current_step,
                context_json=payload,
                started_at=context.started_at,
                completed_at=context.completed_at,
                error=context.error,
            )
            self.session.add(row)
        else:
            row.workflow_id = context.workflow_id
            row.vertical = context.vertical
            row.status = context.status.value
            row.current_step = context.current_step
            row.context_json = payload
            row.completed_at = context.completed_at
            row.error = context.error
        await self.session.flush()
        return row

    async def get_by_id(self, execution_id: str) -> dict[str, Any] | None:
        eid = uuid.UUID(str(execution_id))
        result = await self.session.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == eid)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        data = dict(row.context_json or {})
        data["execution_id"] = str(row.id)
        data["workflow_id"] = row.workflow_id
        data["vertical"] = row.vertical
        data["status"] = row.status
        data["current_step"] = row.current_step
        data["error"] = row.error
        if row.started_at:
            data["started_at"] = row.started_at.isoformat()
        if row.completed_at:
            data["completed_at"] = row.completed_at.isoformat()
        return data

    async def log_step(
        self,
        *,
        execution_id: str,
        step_id: str,
        step_type: str,
        duration_ms: float,
        status: str,
    ) -> WorkflowStepLog:
        row = WorkflowStepLog(
            execution_id=uuid.UUID(str(execution_id)),
            step_id=step_id,
            step_type=step_type,
            duration_ms=float(duration_ms),
            status=status,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_statistics(self) -> dict[str, Any]:
        now = _utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total = (
            await self.session.execute(select(func.count()).select_from(WorkflowExecution))
        ).scalar_one()

        completed_today = (
            await self.session.execute(
                select(func.count())
                .select_from(WorkflowExecution)
                .where(
                    WorkflowExecution.status == "COMPLETED",
                    WorkflowExecution.completed_at >= today_start,
                )
            )
        ).scalar_one()

        failed_today = (
            await self.session.execute(
                select(func.count())
                .select_from(WorkflowExecution)
                .where(
                    WorkflowExecution.status.in_(("FAILED", "CANCELLED")),
                    WorkflowExecution.completed_at >= today_start,
                )
            )
        ).scalar_one()

        avg_duration = (
            await self.session.execute(
                select(
                    func.avg(
                        func.extract(
                            "epoch",
                            WorkflowExecution.completed_at - WorkflowExecution.started_at,
                        )
                    )
                ).where(
                    WorkflowExecution.completed_at.is_not(None),
                    WorkflowExecution.status == "COMPLETED",
                )
            )
        ).scalar_one()

        active = (
            await self.session.execute(
                select(func.count())
                .select_from(WorkflowExecution)
                .where(WorkflowExecution.status.in_(("RUNNING", "WAITING", "PENDING")))
            )
        ).scalar_one()

        return {
            "total_executions": int(total or 0),
            "completed_today": int(completed_today or 0),
            "failed_today": int(failed_today or 0),
            "active_executions_db": int(active or 0),
            "average_execution_time_ms": round(float(avg_duration or 0) * 1000.0, 2),
        }
