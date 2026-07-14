# Marketing Analytics v1 repository.

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.deal_engine_v1 import DealEngineV1Deal, DealEngineV1Status
from database.models.lead_engine import LeadEngineLead, LeadEngineStatus
from database.models.marketing_analytics_v1 import MarketingAnalyticsV1SourceCost
from database.models.revenue_engine_v1 import RevenueEngineV1Entry


class MarketingAnalyticsV1Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_source_costs(self) -> list[MarketingAnalyticsV1SourceCost]:
        result = await self._session.execute(
            select(MarketingAnalyticsV1SourceCost).order_by(
                MarketingAnalyticsV1SourceCost.display_name
            )
        )
        return list(result.scalars().all())

    async def source_metrics(
        self,
        *,
        since: datetime | None = None,
    ) -> list[dict]:
        source_col = func.coalesce(LeadEngineLead.marketing_source, "other").label("source_key")
        leads_stmt = (
            select(
                source_col,
                func.count().label("leads"),
                func.sum(
                    case((LeadEngineLead.status == LeadEngineStatus.WON.value, 1), else_=0)
                ).label("won"),
            )
            .where(
                LeadEngineLead.is_duplicate.is_(False),
                LeadEngineLead.merged_into_id.is_(None),
            )
            .group_by(source_col)
        )
        if since is not None:
            leads_stmt = leads_stmt.where(LeadEngineLead.created_at >= since)
        leads_result = await self._session.execute(leads_stmt)
        lead_rows = {
            row.source_key: {"leads": int(row.leads), "won": int(row.won or 0)}
            for row in leads_result.all()
        }

        revenue_stmt = (
            select(
                func.coalesce(LeadEngineLead.marketing_source, "other").label("source_key"),
                func.coalesce(func.sum(RevenueEngineV1Entry.platform_income), 0).label("revenue"),
                func.count(func.distinct(DealEngineV1Deal.id)).label("deals"),
            )
            .join(DealEngineV1Deal, DealEngineV1Deal.lead_id == LeadEngineLead.id)
            .join(RevenueEngineV1Entry, RevenueEngineV1Entry.deal_id == DealEngineV1Deal.id)
            .where(
                DealEngineV1Deal.status == DealEngineV1Status.COMPLETED.value,
                LeadEngineLead.is_duplicate.is_(False),
            )
            .group_by(func.coalesce(LeadEngineLead.marketing_source, "other"))
        )
        if since is not None:
            revenue_stmt = revenue_stmt.where(RevenueEngineV1Entry.created_at >= since)
        revenue_result = await self._session.execute(revenue_stmt)
        revenue_rows = {
            row.source_key: {
                "revenue": Decimal(row.revenue),
                "deals": int(row.deals),
            }
            for row in revenue_result.all()
        }

        keys = set(lead_rows) | set(revenue_rows)
        metrics: list[dict] = []
        for key in keys:
            lead_data = lead_rows.get(key, {"leads": 0, "won": 0})
            rev_data = revenue_rows.get(key, {"revenue": Decimal("0"), "deals": 0})
            leads = lead_data["leads"]
            won = lead_data["won"]
            revenue = rev_data["revenue"]
            conversion = round((won / leads) * 100, 1) if leads else 0.0
            metrics.append({
                "source_key": key,
                "leads": leads,
                "won": won,
                "deals": rev_data["deals"],
                "revenue": revenue,
                "conversion_rate": conversion,
            })
        return metrics

    async def campaign_metrics(
        self,
        *,
        since: datetime | None = None,
        limit: int = 15,
    ) -> list[dict]:
        campaign_col = func.coalesce(LeadEngineLead.utm_campaign, "—").label("campaign")
        stmt = (
            select(
                campaign_col,
                func.coalesce(LeadEngineLead.marketing_source, "other").label("source_key"),
                func.count().label("leads"),
                func.sum(
                    case((LeadEngineLead.status == LeadEngineStatus.WON.value, 1), else_=0)
                ).label("won"),
            )
            .where(
                LeadEngineLead.is_duplicate.is_(False),
                LeadEngineLead.merged_into_id.is_(None),
            )
            .group_by(campaign_col, func.coalesce(LeadEngineLead.marketing_source, "other"))
            .order_by(func.count().desc())
            .limit(limit)
        )
        if since is not None:
            stmt = stmt.where(LeadEngineLead.created_at >= since)
        result = await self._session.execute(stmt)
        rows: list[dict] = []
        for row in result.all():
            leads = int(row.leads)
            won = int(row.won or 0)
            rows.append({
                "campaign": row.campaign,
                "source_key": row.source_key,
                "leads": leads,
                "won": won,
                "conversion_rate": round((won / leads) * 100, 1) if leads else 0.0,
            })
        return rows

    async def revenue_by_campaign(
        self,
        *,
        since: datetime | None = None,
        limit: int = 15,
    ) -> list[tuple[str | None, str | None, Decimal]]:
        campaign_col = func.coalesce(LeadEngineLead.utm_campaign, "—").label("campaign")
        stmt = (
            select(
                campaign_col,
                func.coalesce(LeadEngineLead.marketing_source, "other").label("source_key"),
                func.coalesce(func.sum(RevenueEngineV1Entry.platform_income), 0),
            )
            .join(DealEngineV1Deal, DealEngineV1Deal.lead_id == LeadEngineLead.id)
            .join(RevenueEngineV1Entry, RevenueEngineV1Entry.deal_id == DealEngineV1Deal.id)
            .where(DealEngineV1Deal.status == DealEngineV1Status.COMPLETED.value)
            .group_by(campaign_col, func.coalesce(LeadEngineLead.marketing_source, "other"))
            .order_by(func.sum(RevenueEngineV1Entry.platform_income).desc())
            .limit(limit)
        )
        if since is not None:
            stmt = stmt.where(RevenueEngineV1Entry.created_at >= since)
        result = await self._session.execute(stmt)
        return [
            (row[0], row[1], Decimal(row[2]))
            for row in result.all()
        ]

    async def attribution_breakdown(
        self,
        *,
        since: datetime | None = None,
        limit: int = 10,
    ) -> list[dict]:
        stmt = (
            select(
                LeadEngineLead.source_link,
                LeadEngineLead.utm_source,
                LeadEngineLead.utm_campaign,
                LeadEngineLead.utm_medium,
                LeadEngineLead.referrer,
                func.count(),
            )
            .where(
                LeadEngineLead.is_duplicate.is_(False),
                LeadEngineLead.merged_into_id.is_(None),
            )
            .group_by(
                LeadEngineLead.source_link,
                LeadEngineLead.utm_source,
                LeadEngineLead.utm_campaign,
                LeadEngineLead.utm_medium,
                LeadEngineLead.referrer,
            )
            .order_by(func.count().desc())
            .limit(limit)
        )
        if since is not None:
            stmt = stmt.where(LeadEngineLead.created_at >= since)
        result = await self._session.execute(stmt)
        return [
            {
                "source_link": row[0],
                "utm_source": row[1],
                "utm_campaign": row[2],
                "utm_medium": row[3],
                "referrer": row[4],
                "leads": int(row[5]),
            }
            for row in result.all()
        ]

    async def count_leads(self, *, since: datetime | None = None) -> int:
        stmt = select(func.count()).select_from(LeadEngineLead).where(
            LeadEngineLead.is_duplicate.is_(False),
            LeadEngineLead.merged_into_id.is_(None),
        )
        if since is not None:
            stmt = stmt.where(LeadEngineLead.created_at >= since)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
