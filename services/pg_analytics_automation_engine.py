# Analytics Automation Engine v1 — leads, conversion, profit, ROI metrics.

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select

from config import MANAGER_ID, OWNER_ID
from database.models.analytics_automation_engine import SnapshotPeriod
from database.models.auto_marketing_engine import MarketingCampaign
from database.models.car import Car, CarStatus
from database.models.lead_automation_engine import AutomationLead
from database.models.sales_pipeline_automation_engine import PipelineLead, PipelineStage
from database.session import get_session
from repositories.analytics_automation_repository import AnalyticsAutomationRepository
from repositories.user_role_repository import UserRoleRepository

ANALYTICS_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})


class AnalyticsAutomationEngineError(Exception):
    pass


class AnalyticsAutomationEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in ANALYTICS_ROLES for role in roles)

    @staticmethod
    async def compute_metrics(*, metric_date: date | None = None) -> dict[str, Any]:
        target_date = metric_date or datetime.now(timezone.utc).date()

        async with get_session() as session:
            leads_per_source = await AnalyticsAutomationEngineV1._leads_per_source(session)
            pipeline_counts = await AnalyticsAutomationEngineV1._pipeline_counts(session)
            total_leads = sum(leads_per_source.values())
            sold_count = pipeline_counts.get(PipelineStage.SOLD.value, 0)
            conversion_rate = (
                round(sold_count / total_leads * 100, 2) if total_leads else 0.0
            )

            cost_per_lead = await AnalyticsAutomationEngineV1._cost_per_lead(session, total_leads)
            profit_per_vehicle = await AnalyticsAutomationEngineV1._profit_per_vehicle(session)
            manager_efficiency = await AnalyticsAutomationEngineV1._manager_efficiency(session)
            campaign_roi = await AnalyticsAutomationEngineV1._campaign_roi(session)

            metrics = {
                "metric_date": target_date.isoformat(),
                "leads_per_source": leads_per_source,
                "total_leads": total_leads,
                "pipeline_by_stage": pipeline_counts,
                "conversion_rate_percent": conversion_rate,
                "sold_count": sold_count,
                "cost_per_lead": cost_per_lead,
                "profit_per_vehicle": profit_per_vehicle,
                "manager_efficiency": manager_efficiency,
                "campaign_roi": campaign_roi,
            }

            snapshot = await AnalyticsAutomationRepository(session).upsert_snapshot(
                metric_date=target_date,
                metrics=metrics,
                period=SnapshotPeriod.DAILY.value,
            )
            await session.refresh(snapshot)
            return AnalyticsAutomationRepository.snapshot_dict(snapshot)

    @staticmethod
    async def _leads_per_source(session) -> dict[str, int]:
        result = await session.execute(
            select(AutomationLead.source, func.count())
            .where(AutomationLead.is_duplicate.is_(False))
            .group_by(AutomationLead.source)
        )
        return {row[0]: int(row[1]) for row in result.all()}

    @staticmethod
    async def _pipeline_counts(session) -> dict[str, int]:
        result = await session.execute(
            select(PipelineLead.stage, func.count()).group_by(PipelineLead.stage)
        )
        counts = {stage.value: 0 for stage in PipelineStage}
        for stage, count in result.all():
            counts[stage] = int(count)
        return counts

    @staticmethod
    async def _cost_per_lead(session, total_leads: int) -> dict[str, Any]:
        result = await session.execute(
            select(
                func.coalesce(func.sum(Car.advertising_cost), 0),
                func.coalesce(func.sum(Car.total_cost), 0),
            )
        )
        row = result.one()
        total_advertising = Decimal(str(row[0] or 0))
        total_cost = Decimal(str(row[1] or 0))
        marketing_spend = total_advertising
        cpl = (
            str((marketing_spend / Decimal(total_leads)).quantize(Decimal("0.01")))
            if total_leads
            else None
        )
        return {
            "total_marketing_spend": str(marketing_spend),
            "total_inventory_cost": str(total_cost),
            "total_leads": total_leads,
            "cost_per_lead": cpl,
        }

    @staticmethod
    async def _profit_per_vehicle(session) -> dict[str, Any]:
        result = await session.execute(
            select(Car)
            .where(Car.expected_profit.is_not(None))
            .order_by(Car.updated_at.desc())
            .limit(50)
        )
        cars = list(result.scalars().all())
        items: list[dict[str, Any]] = []
        for car in cars:
            items.append({
                "car_id": str(car.id),
                "vin": car.vin,
                "make": car.make,
                "model": car.model,
                "year": car.year,
                "total_cost": str(car.total_cost) if car.total_cost else None,
                "sale_price": str(car.sale_price) if car.sale_price else None,
                "expected_profit": str(car.expected_profit) if car.expected_profit else None,
                "status": car.status,
            })
        sold_result = await session.execute(
            select(
                func.coalesce(func.sum(Car.expected_profit), 0),
                func.count(),
            ).where(Car.status == CarStatus.SOLD.value)
        )
        sold_row = sold_result.one()
        return {
            "vehicles": items,
            "sold_total_profit": str(sold_row[0] or 0),
            "sold_count": int(sold_row[1] or 0),
        }

    @staticmethod
    async def _manager_efficiency(session) -> dict[str, Any]:
        managers: dict[int, dict[str, int]] = {}
        result = await session.execute(
            select(
                AutomationLead.assigned_manager_id,
                AutomationLead.source,
                func.count(),
            )
            .where(
                AutomationLead.is_duplicate.is_(False),
                AutomationLead.assigned_manager_id.is_not(None),
            )
            .group_by(AutomationLead.assigned_manager_id, AutomationLead.source)
        )
        for manager_id, _source, count in result.all():
            entry = managers.setdefault(int(manager_id), {"leads": 0, "sold": 0})
            entry["leads"] += int(count)

        sold_result = await session.execute(
            select(PipelineLead.assigned_manager_id, func.count())
            .where(PipelineLead.stage == PipelineStage.SOLD.value)
            .group_by(PipelineLead.assigned_manager_id)
        )
        for manager_id, count in sold_result.all():
            if manager_id is None:
                continue
            entry = managers.setdefault(int(manager_id), {"leads": 0, "sold": 0})
            entry["sold"] = int(count)

        efficiency: dict[str, Any] = {}
        for manager_id, data in managers.items():
            leads = data["leads"]
            sold = data["sold"]
            efficiency[str(manager_id)] = {
                "leads": leads,
                "sold": sold,
                "conversion_rate_percent": round(sold / leads * 100, 2) if leads else 0.0,
            }
        if not efficiency:
            efficiency[str(MANAGER_ID)] = {"leads": 0, "sold": 0, "conversion_rate_percent": 0.0}
        return efficiency

    @staticmethod
    async def _campaign_roi(session) -> list[dict[str, Any]]:
        result = await session.execute(
            select(MarketingCampaign)
            .order_by(MarketingCampaign.created_at.desc())
            .limit(20)
        )
        campaigns = list(result.scalars().all())
        roi_items: list[dict[str, Any]] = []
        for campaign in campaigns:
            metrics = campaign.metrics or {}
            published = int(metrics.get("published", 0))
            failed = int(metrics.get("failed", 0))
            scheduled = int(metrics.get("scheduled", 0))
            spend_estimate = Decimal(str(scheduled + published)) * Decimal("10")
            revenue_estimate = Decimal(str(published)) * Decimal("100")
            roi = None
            if spend_estimate > 0:
                roi = str(
                    ((revenue_estimate - spend_estimate) / spend_estimate * 100).quantize(
                        Decimal("0.01")
                    )
                )
            roi_items.append({
                "campaign_id": str(campaign.id),
                "name": campaign.name,
                "status": campaign.status,
                "published": published,
                "failed": failed,
                "scheduled": scheduled,
                "estimated_spend": str(spend_estimate),
                "estimated_revenue": str(revenue_estimate),
                "roi_percent": roi,
            })
        return roi_items

    @staticmethod
    async def get_latest_snapshot(actor_id: int) -> dict[str, Any]:
        if not await AnalyticsAutomationEngineV1.user_can_access(actor_id):
            raise AnalyticsAutomationEngineError("Access denied")

        async with get_session() as session:
            snapshots = await AnalyticsAutomationRepository(session).list_snapshots(limit=1)
            if not snapshots:
                computed = await AnalyticsAutomationEngineV1.compute_metrics()
                return computed
            await session.refresh(snapshots[0])
            return AnalyticsAutomationRepository.snapshot_dict(snapshots[0])

    @staticmethod
    async def list_snapshots(actor_id: int, *, limit: int = 30) -> list[dict[str, Any]]:
        if not await AnalyticsAutomationEngineV1.user_can_access(actor_id):
            raise AnalyticsAutomationEngineError("Access denied")

        async with get_session() as session:
            rows = await AnalyticsAutomationRepository(session).list_snapshots(limit=limit)
            return [AnalyticsAutomationRepository.snapshot_dict(r) for r in rows]
