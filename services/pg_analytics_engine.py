# Analytics Engine v1 — CPL, CAC, conversion, manager performance, vehicle turnover.

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select

from config import MANAGER_ID, OWNER_ID
from database.models.ai_sales_agent import SalesLead, SalesLeadStatus
from database.models.auto_marketing_engine import MarketingCampaign
from database.models.car import Car, CarStatus
from database.models.cross_posting_engine import PostingResult
from database.models.deal_pipeline_engine import DealStatus, PipelineDeal
from database.models.lead_automation_engine import AutomationLead
from database.session import get_session
from repositories.analytics_engine_repository import (
    AdvertisingStatisticsRepository,
    LeadStatisticsRepository,
    ManagerStatisticsRepository,
    SalesStatisticsRepository,
)
from repositories.user_role_repository import UserRoleRepository
from services.pg_partner_tenant_engine import PartnerTenantEngineV1

ANALYTICS_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})


class AnalyticsEngineError(Exception):
    pass


class AnalyticsEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in ANALYTICS_ROLES for role in roles)

    @staticmethod
    async def _require_access(actor_id: int, tenant_id: uuid.UUID):
        if not await AnalyticsEngineV1.user_can_access(actor_id):
            raise AnalyticsEngineError("Analytics access denied")
        return await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

    @staticmethod
    def _pct(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.0001"))

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))

    @staticmethod
    async def aggregate_daily(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        metric_date: date | None = None,
    ) -> dict[str, Any]:
        ctx = await AnalyticsEngineV1._require_access(actor_id, tenant_id)
        target = metric_date or datetime.now(timezone.utc).date()

        async with get_session() as session:
            lead_stats = await AnalyticsEngineV1._compute_lead_stats(session, tenant_id, target)
            sales_stats = await AnalyticsEngineV1._compute_sales_stats(session, tenant_id, target)
            ad_stats = await AnalyticsEngineV1._compute_ad_stats(
                session, tenant_id, target, lead_stats["total_leads"]
            )
            manager_stats = await AnalyticsEngineV1._compute_manager_stats(session, tenant_id, target)

            lead_row = await LeadStatisticsRepository(session).upsert(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                metric_date=target,
                **lead_stats,
            )
            sales_row = await SalesStatisticsRepository(session).upsert(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                metric_date=target,
                **sales_stats,
            )
            ad_row = await AdvertisingStatisticsRepository(session).upsert(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                metric_date=target,
                **ad_stats,
            )
            manager_rows: list[dict[str, Any]] = []
            for mgr in manager_stats:
                row = await ManagerStatisticsRepository(session).upsert(
                    tenant_id=tenant_id,
                    company_id=ctx.company_id,
                    metric_date=target,
                    **mgr,
                )
                manager_rows.append(ManagerStatisticsRepository.snapshot(row))

            await session.refresh(lead_row)
            await session.refresh(sales_row)
            await session.refresh(ad_row)

            return {
                "metric_date": target.isoformat(),
                "lead_statistics": ManagerStatisticsRepository.lead_snapshot(lead_row),
                "sales_statistics": ManagerStatisticsRepository.sales_snapshot(sales_row),
                "advertising_statistics": ManagerStatisticsRepository.advertising_snapshot(ad_row),
                "manager_statistics": manager_rows,
            }

    @staticmethod
    async def _compute_lead_stats(session, tenant_id: uuid.UUID, target: date) -> dict[str, Any]:
        result = await session.execute(
            select(AutomationLead.source, func.count())
            .where(
                AutomationLead.is_duplicate.is_(False),
                func.date(AutomationLead.created_at) == target,
            )
            .group_by(AutomationLead.source)
        )
        leads_by_source = {row[0]: int(row[1]) for row in result.all()}

        sales_result = await session.execute(
            select(func.count())
            .select_from(SalesLead)
            .where(
                SalesLead.tenant_id == tenant_id,
                func.date(SalesLead.created_at) == target,
            )
        )
        sales_leads = int(sales_result.scalar_one() or 0)
        for source, count in leads_by_source.items():
            leads_by_source[source] = leads_by_source.get(source, 0) + count
        if sales_leads and "SALES_AGENT" not in leads_by_source:
            leads_by_source["SALES_AGENT"] = sales_leads

        total_leads = sum(leads_by_source.values())

        qualified_result = await session.execute(
            select(func.count())
            .select_from(SalesLead)
            .where(
                SalesLead.tenant_id == tenant_id,
                SalesLead.status.in_([
                    SalesLeadStatus.QUALIFIED.value,
                    SalesLeadStatus.NEGOTIATION.value,
                    SalesLeadStatus.RESERVED.value,
                    SalesLeadStatus.SOLD.value,
                ]),
                func.date(SalesLead.updated_at) == target,
            )
        )
        qualified_leads = int(qualified_result.scalar_one() or 0)

        spend_result = await session.execute(
            select(func.coalesce(func.sum(Car.advertising_cost), 0))
        )
        total_spend = Decimal(str(spend_result.scalar_one() or 0))
        cpl = (
            AnalyticsEngineV1._money(total_spend / Decimal(total_leads))
            if total_leads
            else None
        )

        won_result = await session.execute(
            select(func.count())
            .select_from(PipelineDeal)
            .where(
                PipelineDeal.tenant_id == tenant_id,
                PipelineDeal.status == DealStatus.WON.value,
                func.date(PipelineDeal.updated_at) == target,
            )
        )
        won = int(won_result.scalar_one() or 0)
        conversion_rate = (
            AnalyticsEngineV1._pct(Decimal(won) / Decimal(total_leads) * 100)
            if total_leads
            else None
        )

        lead_source_roi: dict[str, Any] = {}
        for source, count in leads_by_source.items():
            if count == 0:
                continue
            source_spend = AnalyticsEngineV1._money(total_spend * Decimal(count) / Decimal(total_leads))
            lead_source_roi[source] = {
                "leads": count,
                "estimated_spend": str(source_spend),
                "roi_percent": str(
                    AnalyticsEngineV1._pct(
                        (Decimal(count) * Decimal("100") - source_spend) / source_spend * 100
                    )
                )
                if source_spend > 0
                else None,
            }

        return {
            "total_leads": total_leads,
            "qualified_leads": qualified_leads,
            "leads_by_source": leads_by_source or None,
            "cpl": cpl,
            "conversion_rate": conversion_rate,
            "lead_source_roi": lead_source_roi or None,
        }

    @staticmethod
    async def _compute_sales_stats(session, tenant_id: uuid.UUID, target: date) -> dict[str, Any]:
        won_result = await session.execute(
            select(func.count(), func.coalesce(func.sum(PipelineDeal.deal_value), 0))
            .select_from(PipelineDeal)
            .where(
                PipelineDeal.tenant_id == tenant_id,
                PipelineDeal.status == DealStatus.WON.value,
                func.date(PipelineDeal.updated_at) == target,
            )
        )
        won_row = won_result.one()
        deals_won = int(won_row[0] or 0)
        total_revenue = Decimal(str(won_row[1] or 0))

        lost_result = await session.execute(
            select(func.count())
            .select_from(PipelineDeal)
            .where(
                PipelineDeal.tenant_id == tenant_id,
                PipelineDeal.status == DealStatus.LOST.value,
                func.date(PipelineDeal.updated_at) == target,
            )
        )
        deals_lost = int(lost_result.scalar_one() or 0)

        total_deals = deals_won + deals_lost
        average_deal_size = (
            AnalyticsEngineV1._money(total_revenue / Decimal(deals_won)) if deals_won else None
        )
        conversion_rate = (
            AnalyticsEngineV1._pct(Decimal(deals_won) / Decimal(total_deals) * 100)
            if total_deals
            else None
        )

        sold_cars = await session.execute(
            select(func.count())
            .select_from(Car)
            .where(Car.status == CarStatus.SOLD.value, func.date(Car.updated_at) == target)
        )
        sold_count = int(sold_cars.scalar_one() or 0)
        inventory_result = await session.execute(
            select(func.count()).select_from(Car).where(
                Car.status == CarStatus.READY_FOR_SALE.value
            )
        )
        inventory_count = int(inventory_result.scalar_one() or 0)
        vehicle_turnover = (
            AnalyticsEngineV1._pct(Decimal(sold_count) / Decimal(inventory_count + sold_count) * 100)
            if (inventory_count + sold_count)
            else None
        )

        return {
            "deals_won": deals_won,
            "deals_lost": deals_lost,
            "total_revenue": total_revenue if deals_won else None,
            "average_deal_size": average_deal_size,
            "conversion_rate": conversion_rate,
            "vehicle_turnover": vehicle_turnover,
        }

    @staticmethod
    async def _compute_ad_stats(
        session,
        tenant_id: uuid.UUID,
        target: date,
        total_leads: int,
    ) -> dict[str, Any]:
        spend_result = await session.execute(
            select(func.coalesce(func.sum(Car.advertising_cost), 0))
        )
        total_spend = Decimal(str(spend_result.scalar_one() or 0))

        posting_result = await session.execute(
            select(
                func.coalesce(func.sum(PostingResult.views), 0),
                func.coalesce(func.sum(PostingResult.clicks), 0),
            )
            .where(
                PostingResult.tenant_id == tenant_id,
                func.date(PostingResult.created_at) == target,
            )
        )
        impressions, clicks = posting_result.one()
        total_impressions = int(impressions or 0)
        total_clicks = int(clicks or 0)

        campaign_result = await session.execute(
            select(MarketingCampaign)
            .order_by(MarketingCampaign.created_at.desc())
            .limit(10)
        )
        campaigns = list(campaign_result.scalars().all())
        campaign_metrics = [
            {
                "campaign_id": str(c.id),
                "name": c.name,
                "metrics": c.metrics or {},
            }
            for c in campaigns
        ]

        leads_from_ads = max(total_clicks // 10, 0)
        customers_acquired = max(leads_from_ads // 3, 1) if leads_from_ads else 0
        cac = (
            AnalyticsEngineV1._money(total_spend / Decimal(customers_acquired))
            if customers_acquired and total_spend
            else None
        )
        cpl = (
            AnalyticsEngineV1._money(total_spend / Decimal(total_leads))
            if total_leads and total_spend
            else None
        )

        return {
            "total_spend": total_spend if total_spend else None,
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "leads_from_ads": leads_from_ads,
            "cac": cac,
            "cpl": cpl,
            "campaign_metrics": campaign_metrics or None,
        }

    @staticmethod
    async def _compute_manager_stats(
        session,
        tenant_id: uuid.UUID,
        target: date,
    ) -> list[dict[str, Any]]:
        leads_result = await session.execute(
            select(PipelineDeal.assigned_manager_id, func.count())
            .where(
                PipelineDeal.tenant_id == tenant_id,
                PipelineDeal.assigned_manager_id.is_not(None),
                func.date(PipelineDeal.created_at) == target,
            )
            .group_by(PipelineDeal.assigned_manager_id)
        )
        managers: dict[int, dict[str, Any]] = {}
        for manager_id, count in leads_result.all():
            managers[int(manager_id)] = {"leads_assigned": int(count), "deals_closed": 0, "revenue": Decimal(0)}

        closed_result = await session.execute(
            select(
                PipelineDeal.assigned_manager_id,
                func.count(),
                func.coalesce(func.sum(PipelineDeal.deal_value), 0),
            )
            .where(
                PipelineDeal.tenant_id == tenant_id,
                PipelineDeal.status == DealStatus.WON.value,
                PipelineDeal.assigned_manager_id.is_not(None),
                func.date(PipelineDeal.updated_at) == target,
            )
            .group_by(PipelineDeal.assigned_manager_id)
        )
        for manager_id, count, revenue in closed_result.all():
            entry = managers.setdefault(int(manager_id), {"leads_assigned": 0, "deals_closed": 0, "revenue": Decimal(0)})
            entry["deals_closed"] = int(count)
            entry["revenue"] = Decimal(str(revenue or 0))

        if not managers:
            managers[MANAGER_ID] = {"leads_assigned": 0, "deals_closed": 0, "revenue": Decimal(0)}

        rows: list[dict[str, Any]] = []
        for manager_id, data in managers.items():
            leads = data["leads_assigned"]
            closed = data["deals_closed"]
            revenue = data["revenue"]
            conversion = (
                AnalyticsEngineV1._pct(Decimal(closed) / Decimal(leads) * 100) if leads else None
            )
            performance = (
                AnalyticsEngineV1._pct(Decimal(closed) * Decimal("10") + (revenue / Decimal("1000")))
                if closed or revenue
                else Decimal("0")
            )
            rows.append({
                "manager_id": manager_id,
                "leads_assigned": leads,
                "deals_closed": closed,
                "revenue": revenue if closed else None,
                "conversion_rate": conversion,
                "performance_score": performance,
            })
        return rows

    @staticmethod
    async def get_dashboard(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        metric_date: date | None = None,
    ) -> dict[str, Any]:
        await AnalyticsEngineV1._require_access(actor_id, tenant_id)
        target = metric_date or datetime.now(timezone.utc).date()

        async with get_session() as session:
            lead_row = await LeadStatisticsRepository(session).get_by_date(tenant_id, target)
            sales_row = await SalesStatisticsRepository(session).get_by_date(tenant_id, target)
            ad_rows = await AdvertisingStatisticsRepository(session).list_by_tenant(tenant_id, limit=1)
            mgr_rows = await ManagerStatisticsRepository(session).list_by_tenant(
                tenant_id, metric_date=target
            )

        if lead_row is None or sales_row is None:
            return await AnalyticsEngineV1.aggregate_daily(actor_id, tenant_id, metric_date=target)

        ad_row = ad_rows[0] if ad_rows else None
        return {
            "tenant_id": str(tenant_id),
            "metric_date": target.isoformat(),
            "metrics": [
                "CPL",
                "CAC",
                "Conversion Rate",
                "Average Deal Size",
                "Lead Source ROI",
                "Manager Performance",
                "Vehicle Turnover",
            ],
            "lead_statistics": ManagerStatisticsRepository.lead_snapshot(lead_row),
            "sales_statistics": ManagerStatisticsRepository.sales_snapshot(sales_row),
            "advertising_statistics": (
                ManagerStatisticsRepository.advertising_snapshot(ad_row) if ad_row else None
            ),
            "manager_statistics": [
                ManagerStatisticsRepository.snapshot(r) for r in mgr_rows
            ],
        }

    @staticmethod
    async def export_report(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        format: str = "json",
        days: int = 30,
    ) -> dict[str, Any]:
        await AnalyticsEngineV1._require_access(actor_id, tenant_id)

        async with get_session() as session:
            leads = await LeadStatisticsRepository(session).list_by_tenant(tenant_id, limit=days)
            sales = await SalesStatisticsRepository(session).list_by_tenant(tenant_id, limit=days)
            ads = await AdvertisingStatisticsRepository(session).list_by_tenant(tenant_id, limit=days)
            managers = await ManagerStatisticsRepository(session).list_by_tenant(tenant_id, limit=days * 5)

        payload = {
            "tenant_id": str(tenant_id),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "lead_statistics": [ManagerStatisticsRepository.lead_snapshot(r) for r in leads],
            "sales_statistics": [ManagerStatisticsRepository.sales_snapshot(r) for r in sales],
            "advertising_statistics": [
                ManagerStatisticsRepository.advertising_snapshot(r) for r in ads
            ],
            "manager_statistics": [ManagerStatisticsRepository.snapshot(r) for r in managers],
        }

        if format == "csv":
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["section", "metric_date", "key", "value"])
            for section, rows in (
                ("lead", payload["lead_statistics"]),
                ("sales", payload["sales_statistics"]),
                ("advertising", payload["advertising_statistics"]),
            ):
                for row in rows:
                    writer.writerow([section, row.get("metric_date"), "summary", json.dumps(row)])
            for row in payload["manager_statistics"]:
                writer.writerow([
                    "manager",
                    row.get("metric_date"),
                    str(row.get("manager_id")),
                    json.dumps(row),
                ])
            return {"format": "csv", "content": buffer.getvalue(), "row_count": len(leads) + len(sales)}

        return {"format": "json", "report": payload}
