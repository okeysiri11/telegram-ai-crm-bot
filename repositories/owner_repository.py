# OwnerRepository — owner escalation persistence and KPI counts.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select

from config import PLATFORM_OWNER_NAME, PLATFORM_OWNER_TELEGRAM_ID
from platform_configuration.config_provider import config_provider
from database.models.request_sla import RequestSla
from repositories.escalation_repository import EscalationRepository
from repositories.sla_repository import SLARepository
from src.platform.layers.base_repository import BaseRepository

MIN_MANAGER_ESCALATION_LEVEL = 3


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _start_of_today_utc() -> datetime:
    now = _utcnow()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_week_utc() -> datetime:
    now = _utcnow()
    return (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_month_utc() -> datetime:
    now = _utcnow()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


class OwnerRepository(BaseRepository):
    @staticmethod
    def owner_config() -> dict[str, Any]:
        escalation = config_provider.owner_escalation_settings()
        return {
            "enabled": escalation["enabled"],
            "telegram_id": PLATFORM_OWNER_TELEGRAM_ID,
            "name": PLATFORM_OWNER_NAME,
            "delay_minutes": escalation["delay_minutes"],
        }

    @staticmethod
    def is_enabled() -> bool:
        escalation = config_provider.owner_escalation_settings()
        return escalation["enabled"] and PLATFORM_OWNER_TELEGRAM_ID is not None

    async def lock_owner_escalation_candidates(
        self,
        *,
        now: datetime | None = None,
        limit: int = 50,
    ) -> list[RequestSla]:
        now = now or _utcnow()
        delay_minutes = config_provider.owner_escalation_settings()["delay_minutes"]
        delay_threshold = now - timedelta(minutes=delay_minutes)

        result = await self.session.execute(
            select(RequestSla)
            .where(
                RequestSla.completed_at.is_(None),
                RequestSla.owner_escalated.is_(False),
                RequestSla.escalation_level >= MIN_MANAGER_ESCALATION_LEVEL,
                RequestSla.completion_deadline <= delay_threshold,
            )
            .order_by(RequestSla.completion_deadline.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(result.scalars().all())

    async def mark_owner_escalated(
        self,
        row: RequestSla,
        *,
        escalated_at: datetime | None = None,
    ) -> bool:
        if row.owner_escalated:
            return False
        now = escalated_at or _utcnow()
        row.owner_escalated = True
        row.owner_escalated_at = now
        row.escalation_level = max(row.escalation_level, 4)
        await self.session.flush()
        return True

    async def mark_owner_notification_sent(self, request_id: uuid.UUID | str) -> bool:
        row = await EscalationRepository(self.session).get_by_request_id(request_id)
        if row is None or row.owner_notification_sent:
            return False
        row.owner_notification_sent = True
        await self.session.flush()
        return True

    @staticmethod
    def minutes_overdue_since_completion(row: RequestSla, now: datetime | None = None) -> int:
        now = now or _utcnow()
        return max(0, int((now - row.completion_deadline).total_seconds() // 60))

    async def get_owner_escalated_requests(self, *, limit: int = 100) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(RequestSla)
            .where(RequestSla.owner_escalated.is_(True))
            .order_by(RequestSla.owner_escalated_at.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        sla_repo = SLARepository(self.session)
        now = _utcnow()
        items: list[dict[str, Any]] = []
        for row in rows:
            item = await sla_repo._serialize_sla_row(row, now=now, include_overdue=True)
            if item is None:
                continue
            item["owner_escalated_at"] = (
                row.owner_escalated_at.isoformat() if row.owner_escalated_at else None
            )
            item["owner_notification_sent"] = row.owner_notification_sent
            item["escalation_level"] = row.escalation_level
            items.append(item)
        return items

    async def get_owner_escalation_kpi(self) -> dict[str, int]:
        total = (
            await self.session.execute(
                select(func.count())
                .select_from(RequestSla)
                .where(RequestSla.owner_escalated.is_(True))
            )
        ).scalar_one()

        today_start = _start_of_today_utc()
        week_start = _start_of_week_utc()
        month_start = _start_of_month_utc()

        today = (
            await self.session.execute(
                select(func.count())
                .select_from(RequestSla)
                .where(
                    RequestSla.owner_escalated.is_(True),
                    RequestSla.owner_escalated_at >= today_start,
                )
            )
        ).scalar_one()

        week = (
            await self.session.execute(
                select(func.count())
                .select_from(RequestSla)
                .where(
                    RequestSla.owner_escalated.is_(True),
                    RequestSla.owner_escalated_at >= week_start,
                )
            )
        ).scalar_one()

        month = (
            await self.session.execute(
                select(func.count())
                .select_from(RequestSla)
                .where(
                    RequestSla.owner_escalated.is_(True),
                    RequestSla.owner_escalated_at >= month_start,
                )
            )
        ).scalar_one()

        return {
            "owner_escalations_total": int(total or 0),
            "owner_escalations_today": int(today or 0),
            "owner_escalations_this_week": int(week or 0),
            "owner_escalations_this_month": int(month or 0),
        }
