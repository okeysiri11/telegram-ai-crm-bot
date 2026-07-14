# SLA Tracking v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.lead_engine import LeadEngineLead
from database.models.sla_tracking_v1 import (
    SLA_GREEN_MAX_MINUTES,
    SLA_OVERDUE_MINUTES,
    SlaTrackingV1Entry,
)


class SlaTrackingV1Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_lead_id(self, lead_id: uuid.UUID) -> SlaTrackingV1Entry | None:
        result = await self._session.execute(
            select(SlaTrackingV1Entry).where(SlaTrackingV1Entry.lead_id == lead_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        lead_id: uuid.UUID,
        vertical: str,
        lead_created_at: datetime,
        manager_id: uuid.UUID | None = None,
    ) -> SlaTrackingV1Entry:
        row = SlaTrackingV1Entry(
            lead_id=lead_id,
            vertical=vertical,
            lead_created_at=lead_created_at,
            manager_id=manager_id,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def update(self, entry_id: uuid.UUID, **fields) -> SlaTrackingV1Entry | None:
        result = await self._session.execute(
            select(SlaTrackingV1Entry).where(SlaTrackingV1Entry.id == entry_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row

    async def update_by_lead(self, lead_id: uuid.UUID, **fields) -> SlaTrackingV1Entry | None:
        row = await self.get_by_lead_id(lead_id)
        if row is None:
            return None
        return await self.update(row.id, **fields)

    async def refresh_overdue_flags(self) -> int:
        now = datetime.now(timezone.utc)
        threshold = now - timedelta(minutes=SLA_OVERDUE_MINUTES)
        result = await self._session.execute(
            select(SlaTrackingV1Entry).where(
                SlaTrackingV1Entry.first_contact_at.is_(None),
                SlaTrackingV1Entry.lead_created_at < threshold,
                SlaTrackingV1Entry.is_overdue.is_(False),
            )
        )
        rows = list(result.scalars().all())
        for row in rows:
            row.is_overdue = True
        await self._session.flush()
        return len(rows)

    async def count_overdue(self) -> int:
        await self.refresh_overdue_flags()
        result = await self._session.execute(
            select(func.count())
            .select_from(SlaTrackingV1Entry)
            .where(SlaTrackingV1Entry.is_overdue.is_(True))
        )
        return int(result.scalar_one())

    async def avg_response_minutes(self) -> float | None:
        result = await self._session.execute(
            select(func.avg(SlaTrackingV1Entry.first_response_minutes)).where(
                SlaTrackingV1Entry.first_response_minutes.is_not(None)
            )
        )
        value = result.scalar_one()
        return round(float(value), 1) if value is not None else None

    async def avg_close_minutes(self) -> float | None:
        result = await self._session.execute(
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        SlaTrackingV1Entry.deal_closed_at - SlaTrackingV1Entry.lead_created_at,
                    )
                    / 60
                )
            ).where(SlaTrackingV1Entry.deal_closed_at.is_not(None))
        )
        value = result.scalar_one()
        return round(float(value), 1) if value is not None else None

    async def count_sla_violations(self) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(SlaTrackingV1Entry)
            .where(
                SlaTrackingV1Entry.first_response_minutes.is_not(None),
                SlaTrackingV1Entry.first_response_minutes > SLA_GREEN_MAX_MINUTES,
            )
        )
        violations = int(result.scalar_one())
        overdue = await self.count_overdue()
        return violations + overdue

    async def manager_stats_simple(self) -> list[dict]:
        result = await self._session.execute(
            select(SlaTrackingV1Entry).where(SlaTrackingV1Entry.manager_id.is_not(None))
        )
        rows = list(result.scalars().all())
        buckets: dict[str, dict] = {}
        for row in rows:
            key = str(row.manager_id)
            if key not in buckets:
                buckets[key] = {
                    "manager_id": key,
                    "leads": 0,
                    "response_sum": 0,
                    "response_count": 0,
                    "closed_deals": 0,
                }
            buckets[key]["leads"] += 1
            if row.first_response_minutes is not None:
                buckets[key]["response_sum"] += row.first_response_minutes
                buckets[key]["response_count"] += 1
            if row.deal_closed_at is not None:
                buckets[key]["closed_deals"] += 1

        stats: list[dict] = []
        for data in buckets.values():
            rc = data["response_count"]
            avg = round(data["response_sum"] / rc, 1) if rc else None
            leads = data["leads"]
            closed = data["closed_deals"]
            stats.append({
                "manager_id": data["manager_id"],
                "leads": leads,
                "avg_response_minutes": avg,
                "closed_deals": closed,
                "conversion_rate": round((closed / leads) * 100, 1) if leads else 0.0,
            })
        return stats

    async def traffic_light_counts(self) -> dict[str, int]:
        result = await self._session.execute(
            select(SlaTrackingV1Entry.response_traffic_light, func.count())
            .where(SlaTrackingV1Entry.response_traffic_light.is_not(None))
            .group_by(SlaTrackingV1Entry.response_traffic_light)
        )
        return {row[0]: int(row[1]) for row in result.all()}

    async def list_overdue(self, *, limit: int = 10) -> list[SlaTrackingV1Entry]:
        await self.refresh_overdue_flags()
        result = await self._session.execute(
            select(SlaTrackingV1Entry)
            .where(SlaTrackingV1Entry.is_overdue.is_(True))
            .order_by(SlaTrackingV1Entry.lead_created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def open_leads_without_sla(self) -> list[LeadEngineLead]:
        subq = select(SlaTrackingV1Entry.lead_id)
        result = await self._session.execute(
            select(LeadEngineLead).where(~LeadEngineLead.id.in_(subq))
        )
        return list(result.scalars().all())
