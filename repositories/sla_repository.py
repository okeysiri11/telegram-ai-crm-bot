# SLARepository — read-only dashboard queries from request_sla, audit_events, request_metrics.

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select

from database.models.audit_events import AuditEventRow
from database.models.auto_client_request import AutoClientRequest
from database.models.client_request import ClientRequest
from database.models.platform_metrics import RequestMetric
from database.models.request_sla import RequestSla
from database.models.users import User
from src.platform.layers.base_repository import BaseRepository

RISK_WINDOW_MINUTES = int(os.getenv("SLA_RISK_MINUTES", "30"))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _start_of_today_utc() -> datetime:
    now = _utcnow()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _vertical_label(request_type: str, *, fallback: str = "UNKNOWN") -> str:
    prefix = (request_type or "").split("_", 1)[0].upper()
    return prefix if prefix else fallback


class SLARepository(BaseRepository):
    async def get_overdue_requests(self, *, limit: int = 100) -> list[dict[str, Any]]:
        now = _utcnow()
        result = await self.session.execute(
            select(RequestSla)
            .where(
                RequestSla.completed_at.is_(None),
                RequestSla.first_response_at.is_(None),
                RequestSla.first_response_deadline < now,
            )
            .order_by(RequestSla.first_response_deadline.asc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        return await self._serialize_open_sla_rows(rows, now=now, include_overdue=True)

    async def get_risk_requests(self, *, limit: int = 100) -> list[dict[str, Any]]:
        now = _utcnow()
        risk_until = now + timedelta(minutes=RISK_WINDOW_MINUTES)
        result = await self.session.execute(
            select(RequestSla)
            .where(
                RequestSla.completed_at.is_(None),
                RequestSla.first_response_at.is_(None),
                RequestSla.first_response_deadline >= now,
                RequestSla.first_response_deadline <= risk_until,
            )
            .order_by(RequestSla.first_response_deadline.asc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        return await self._serialize_open_sla_rows(rows, now=now, include_risk=True)

    async def get_sla_statistics(self) -> dict[str, Any]:
        now = _utcnow()
        today_start = _start_of_today_utc()
        risk_until = now + timedelta(minutes=RISK_WINDOW_MINUTES)

        active = (
            await self.session.execute(
                select(func.count())
                .select_from(RequestSla)
                .where(
                    RequestSla.completed_at.is_(None),
                    RequestSla.first_response_at.is_(None),
                )
            )
        ).scalar_one()

        overdue = (
            await self.session.execute(
                select(func.count())
                .select_from(RequestSla)
                .where(
                    RequestSla.completed_at.is_(None),
                    RequestSla.first_response_at.is_(None),
                    RequestSla.first_response_deadline < now,
                )
            )
        ).scalar_one()

        risk = (
            await self.session.execute(
                select(func.count())
                .select_from(RequestSla)
                .where(
                    RequestSla.completed_at.is_(None),
                    RequestSla.first_response_at.is_(None),
                    RequestSla.first_response_deadline >= now,
                    RequestSla.first_response_deadline <= risk_until,
                )
            )
        ).scalar_one()

        completed_today_sla = (
            await self.session.execute(
                select(func.count())
                .select_from(RequestSla)
                .where(RequestSla.completed_at >= today_start)
            )
        ).scalar_one()

        completed_today_audit = (
            await self.session.execute(
                select(func.count())
                .select_from(AuditEventRow)
                .where(
                    AuditEventRow.event_type == "REQUEST_COMPLETED",
                    AuditEventRow.created_at >= today_start,
                )
            )
        ).scalar_one()

        avg_response_seconds = (
            await self.session.execute(
                select(func.avg(RequestMetric.time_to_first_response_seconds)).where(
                    RequestMetric.first_response_at.is_not(None),
                    RequestMetric.time_to_first_response_seconds.is_not(None),
                )
            )
        ).scalar_one()

        avg_minutes = None
        if avg_response_seconds is not None:
            avg_minutes = round(float(avg_response_seconds) / 60.0, 1)

        return {
            "active": int(active or 0),
            "overdue": int(overdue or 0),
            "risk": int(risk or 0),
            "completed_today": int(max(completed_today_sla or 0, completed_today_audit or 0)),
            "avg_response_minutes": avg_minutes,
        }

    async def get_owner_escalated_requests(self, *, limit: int = 100) -> list[dict[str, Any]]:
        from repositories.owner_repository import OwnerRepository

        return await OwnerRepository(self.session).get_owner_escalated_requests(limit=limit)

    async def _serialize_open_sla_rows(
        self,
        rows: list[RequestSla],
        *,
        now: datetime,
        include_overdue: bool = False,
        include_risk: bool = False,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for row in rows:
            item = await self._serialize_sla_row(
                row,
                now=now,
                include_overdue=include_overdue,
                include_risk=include_risk,
            )
            if item is not None:
                items.append(item)
        return items

    async def _serialize_sla_row(
        self,
        row: RequestSla,
        *,
        now: datetime,
        include_overdue: bool = False,
        include_risk: bool = False,
    ) -> dict[str, Any] | None:
        context = await self._load_request_context(row)
        if context is None:
            return None

        payload: dict[str, Any] = {
            "request_id": str(row.request_id),
            "request_number": context["request_number"],
            "manager": context["manager"],
            "vertical": context["vertical"],
            "deadline": row.first_response_deadline.isoformat(),
            "escalation_level": row.escalation_level,
        }

        if include_overdue:
            payload["minutes_overdue"] = max(
                0,
                int((now - row.first_response_deadline).total_seconds() // 60),
            )
        if include_risk:
            payload["minutes_remaining"] = max(
                0,
                int((row.first_response_deadline - now).total_seconds() // 60),
            )
        return payload

    async def _load_request_context(self, sla_row: RequestSla) -> dict[str, Any] | None:
        request_id = sla_row.request_id
        crm = (
            await self.session.execute(
                select(ClientRequest).where(ClientRequest.id == request_id)
            )
        ).scalar_one_or_none()
        if crm is not None:
            manager_name = await self._resolve_manager_name(
                manager_uuid=crm.manager_id,
                telegram_id=sla_row.manager_id,
            )
            return {
                "request_number": crm.request_number,
                "vertical": _vertical_label(crm.request_type),
                "manager": manager_name,
            }

        auto = (
            await self.session.execute(
                select(AutoClientRequest).where(AutoClientRequest.id == request_id)
            )
        ).scalar_one_or_none()
        if auto is not None:
            manager_name = await self._resolve_manager_name(
                manager_uuid=auto.manager_id,
                telegram_id=sla_row.manager_id,
            )
            return {
                "request_number": auto.request_number,
                "vertical": "AUTO",
                "manager": manager_name,
            }
        return None

    async def _resolve_manager_name(
        self,
        *,
        manager_uuid: uuid.UUID | None,
        telegram_id: int | None,
    ) -> str:
        if manager_uuid is not None:
            user = (
                await self.session.execute(select(User).where(User.id == manager_uuid))
            ).scalar_one_or_none()
            if user is not None:
                return user.full_name or user.username or str(user.telegram_id or manager_uuid)
        if telegram_id is not None:
            user = (
                await self.session.execute(select(User).where(User.telegram_id == telegram_id))
            ).scalar_one_or_none()
            if user is not None:
                return user.full_name or user.username or str(telegram_id)
            return str(telegram_id)
        return "Unassigned"
