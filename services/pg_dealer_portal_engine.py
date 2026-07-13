# Dealer Portal Engine v1 — dashboard, metrics, financials, AI recommendations.

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import func, select

from config import OWNER_ID
from database.models.auto_marketing_engine import MarketingCampaign
from database.models.car import Car, CarStatus
from database.models.dealer_portal_engine import RecommendationPriority
from database.models.lead_automation_engine import AutomationLead
from database.models.sales_pipeline_automation_engine import PipelineLead, PipelineStage
from database.session import get_session
from repositories.car_repository import CarRepository
from repositories.dealer_portal_repository import (
    DealerPortalRecommendationRepository,
    DealerPortalSnapshotRepository,
)
from repositories.lead_automation_repository import LeadAutomationRepository
from repositories.user_role_repository import UserRoleRepository
from services.pg_partner_tenant_engine import PartnerTenantEngineV1

PORTAL_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
MONEY = Decimal("0.01")
ACTIVE_DEAL_STAGES = frozenset({
    PipelineStage.INTERESTED.value,
    PipelineStage.INSPECTION_SCHEDULED.value,
    PipelineStage.NEGOTIATION.value,
    PipelineStage.RESERVED.value,
})


class DealerPortalEngineError(Exception):
    pass


class DealerPortalEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in PORTAL_ROLES for role in roles)

    @staticmethod
    def _quantize(amount: Decimal) -> Decimal:
        return amount.quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def _month_bounds(reference: date | None = None) -> tuple[date, date]:
        today = reference or datetime.now(timezone.utc).date()
        start = today.replace(day=1)
        return start, today

    @staticmethod
    def _reco_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "category": row.category,
            "title": row.title,
            "body": row.body,
            "priority": row.priority,
            "status": row.status,
            "metadata": row.metadata_ or {},
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    async def _require_access(actor_id: int, tenant_id: uuid.UUID):
        if not await DealerPortalEngineV1.user_can_access(actor_id):
            raise DealerPortalEngineError("Dealer portal access denied")
        return await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

    @staticmethod
    async def get_active_leads(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        await DealerPortalEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            leads = await LeadAutomationRepository(session).list_leads(limit=limit)
            items: list[dict[str, Any]] = []
            for lead in leads:
                if lead.is_duplicate:
                    continue
                items.append({
                    "id": str(lead.id),
                    "source": lead.source,
                    "score": lead.score,
                    "status": lead.status,
                    "assigned_manager_id": lead.assigned_manager_id,
                    "created_at": lead.created_at.isoformat(),
                })
            return items[:limit]

    @staticmethod
    async def get_active_vehicles(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        await DealerPortalEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            cars = await CarRepository(session).list_cars(limit=limit)
            active = [c for c in cars if c.status != CarStatus.SOLD.value]
            return [
                {
                    "id": str(car.id),
                    "vin": car.vin,
                    "make": car.make,
                    "model": car.model,
                    "year": car.year,
                    "status": car.status,
                    "sale_price": str(car.sale_price) if car.sale_price else None,
                    "expected_profit": str(car.expected_profit) if car.expected_profit else None,
                }
                for car in active[:limit]
            ]

    @staticmethod
    async def get_conversion_metrics(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await DealerPortalEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            total_leads = await session.execute(
                select(func.count())
                .select_from(AutomationLead)
                .where(AutomationLead.is_duplicate.is_(False))
            )
            leads_count = int(total_leads.scalar_one() or 0)

            stage_result = await session.execute(
                select(PipelineLead.stage, func.count()).group_by(PipelineLead.stage)
            )
            by_stage = {row[0]: int(row[1]) for row in stage_result.all()}
            sold = by_stage.get(PipelineStage.SOLD.value, 0)
            conversion = round(sold / leads_count * 100, 2) if leads_count else 0.0

            return {
                "total_leads": leads_count,
                "sold_count": sold,
                "conversion_rate_percent": conversion,
                "pipeline_by_stage": by_stage,
            }

    @staticmethod
    async def get_advertising_statistics(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await DealerPortalEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            ad_spend_result = await session.execute(
                select(func.coalesce(func.sum(Car.advertising_cost), 0))
            )
            ad_spend = Decimal(str(ad_spend_result.scalar_one() or 0))

            campaigns = await session.execute(
                select(MarketingCampaign)
                .order_by(MarketingCampaign.created_at.desc())
                .limit(20)
            )
            campaign_items: list[dict[str, Any]] = []
            total_published = 0
            for campaign in campaigns.scalars().all():
                metrics = campaign.metrics or {}
                published = int(metrics.get("published", 0))
                total_published += published
                campaign_items.append({
                    "campaign_id": str(campaign.id),
                    "name": campaign.name,
                    "status": campaign.status,
                    "published": published,
                    "failed": int(metrics.get("failed", 0)),
                })

            estimated_roi = None
            if ad_spend > 0 and total_published > 0:
                revenue_est = Decimal(total_published) * Decimal("100")
                estimated_roi = str(
                    DealerPortalEngineV1._quantize(
                        (revenue_est - ad_spend) / ad_spend * Decimal("100")
                    )
                )

            return {
                "ad_spend": str(DealerPortalEngineV1._quantize(ad_spend)),
                "campaigns": campaign_items,
                "total_published": total_published,
                "estimated_roi_percent": estimated_roi,
            }

    @staticmethod
    async def get_financial_reports(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await DealerPortalEngineV1._require_access(actor_id, tenant_id)
        month_start, month_end = DealerPortalEngineV1._month_bounds()

        async with get_session() as session:
            profit_result = await session.execute(
                select(func.coalesce(func.sum(Car.expected_profit), 0))
                .where(
                    Car.status == CarStatus.SOLD.value,
                    func.date(Car.updated_at) >= month_start,
                    func.date(Car.updated_at) <= month_end,
                )
            )
            profit_month = Decimal(str(profit_result.scalar_one() or 0))

            inventory_result = await session.execute(
                select(func.coalesce(func.sum(Car.total_cost), 0))
                .where(Car.status != CarStatus.SOLD.value)
            )
            inventory_value = Decimal(str(inventory_result.scalar_one() or 0))

            revenue_result = await session.execute(
                select(func.coalesce(func.sum(Car.sale_price), 0))
                .where(
                    Car.status == CarStatus.SOLD.value,
                    func.date(Car.updated_at) >= month_start,
                )
            )
            revenue_month = Decimal(str(revenue_result.scalar_one() or 0))

            return {
                "period_start": month_start.isoformat(),
                "period_end": month_end.isoformat(),
                "profit_this_month": str(DealerPortalEngineV1._quantize(profit_month)),
                "revenue_this_month": str(DealerPortalEngineV1._quantize(revenue_month)),
                "inventory_value": str(DealerPortalEngineV1._quantize(inventory_value)),
                "currency": "USD",
            }

    @staticmethod
    async def _build_vehicle_aging(session) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(Car).where(Car.status != CarStatus.SOLD.value)
        )
        cars = list(result.scalars().all())
        if not cars:
            return {
                "avg_days": 0,
                "vehicles_over_90_days": 0,
                "oldest_days": 0,
            }

        days_list = [max(0, (now - car.created_at).days) for car in cars]
        return {
            "avg_days": round(sum(days_list) / len(days_list), 1),
            "vehicles_over_90_days": sum(1 for d in days_list if d >= 90),
            "oldest_days": max(days_list),
        }

    @staticmethod
    async def _build_widgets(session, *, today: date) -> dict[str, Any]:
        leads_today_result = await session.execute(
            select(func.count())
            .select_from(AutomationLead)
            .where(
                AutomationLead.is_duplicate.is_(False),
                func.date(AutomationLead.created_at) == today,
            )
        )
        leads_today = int(leads_today_result.scalar_one() or 0)

        active_deals_result = await session.execute(
            select(func.count())
            .select_from(PipelineLead)
            .where(PipelineLead.stage.in_(ACTIVE_DEAL_STAGES))
        )
        active_deals = int(active_deals_result.scalar_one() or 0)

        inventory_result = await session.execute(
            select(func.count())
            .select_from(Car)
            .where(Car.status != CarStatus.SOLD.value)
        )
        vehicle_inventory = int(inventory_result.scalar_one() or 0)

        inventory_value_result = await session.execute(
            select(func.coalesce(func.sum(Car.total_cost), 0))
            .where(Car.status != CarStatus.SOLD.value)
        )
        inventory_value = str(
            DealerPortalEngineV1._quantize(
                Decimal(str(inventory_value_result.scalar_one() or 0))
            )
        )

        vehicle_aging = await DealerPortalEngineV1._build_vehicle_aging(session)

        ad_spend_result = await session.execute(
            select(func.coalesce(func.sum(Car.advertising_cost), 0))
        )
        ad_spend = str(DealerPortalEngineV1._quantize(Decimal(str(ad_spend_result.scalar_one() or 0))))

        month_start, month_end = DealerPortalEngineV1._month_bounds(today)
        profit_result = await session.execute(
            select(func.coalesce(func.sum(Car.expected_profit), 0))
            .where(
                Car.status == CarStatus.SOLD.value,
                func.date(Car.updated_at) >= month_start,
                func.date(Car.updated_at) <= month_end,
            )
        )
        profit_month = str(
            DealerPortalEngineV1._quantize(Decimal(str(profit_result.scalar_one() or 0)))
        )

        total_leads_result = await session.execute(
            select(func.count())
            .select_from(AutomationLead)
            .where(AutomationLead.is_duplicate.is_(False))
        )
        total_leads = int(total_leads_result.scalar_one() or 0)
        sold_result = await session.execute(
            select(func.count())
            .select_from(PipelineLead)
            .where(PipelineLead.stage == PipelineStage.SOLD.value)
        )
        sold = int(sold_result.scalar_one() or 0)
        conversion = round(sold / total_leads * 100, 2) if total_leads else 0.0

        ad_decimal = Decimal(ad_spend)
        roi = None
        if ad_decimal > 0:
            roi = str(
                DealerPortalEngineV1._quantize(
                    (Decimal(profit_month) / ad_decimal) * Decimal("100")
                )
            )

        return {
            "leads_today": leads_today,
            "active_deals": active_deals,
            "vehicle_inventory": vehicle_inventory,
            "inventory_value": inventory_value,
            "ad_spend": ad_spend,
            "advertising_spend": ad_spend,
            "roi_percent": roi,
            "profit_this_month": profit_month,
            "monthly_profit": profit_month,
            "conversion_rate_percent": conversion,
            "conversion_rate": conversion,
            "vehicle_aging": vehicle_aging,
        }

    @staticmethod
    def _generate_rule_recommendations(widgets: dict[str, Any], sections: dict[str, Any]) -> list[dict[str, Any]]:
        recs: list[dict[str, Any]] = []

        if widgets.get("leads_today", 0) == 0:
            recs.append({
                "category": "leads",
                "title": "Boost lead generation",
                "body": "No leads today. Increase ad spend or publish inventory to Telegram/Instagram.",
                "priority": RecommendationPriority.HIGH.value,
            })

        if widgets.get("active_deals", 0) >= 5:
            recs.append({
                "category": "sales",
                "title": "Prioritize active deals",
                "body": f"You have {widgets['active_deals']} active deals. Focus manager follow-ups today.",
                "priority": RecommendationPriority.MEDIUM.value,
            })

        conversion = widgets.get("conversion_rate_percent", 0) or widgets.get("conversion_rate", 0)
        if conversion and conversion < 5:
            recs.append({
                "category": "conversion",
                "title": "Improve conversion funnel",
                "body": f"Conversion is {conversion}%. Review pipeline stages and objection handling scripts.",
                "priority": RecommendationPriority.HIGH.value,
            })

        ad_stats = sections.get("advertising_statistics", {})
        if ad_stats.get("estimated_roi_percent") is not None:
            try:
                roi_val = float(ad_stats["estimated_roi_percent"])
                if roi_val < 0:
                    recs.append({
                        "category": "marketing",
                        "title": "Review ad campaigns",
                        "body": "Negative campaign ROI detected. Pause low-performing channels and reallocate budget.",
                        "priority": RecommendationPriority.HIGH.value,
                    })
            except (TypeError, ValueError):
                pass

        aging = widgets.get("vehicle_aging", {})
        if aging.get("vehicles_over_90_days", 0) > 0:
            recs.append({
                "category": "inventory",
                "title": "Address aging inventory",
                "body": (
                    f"{aging['vehicles_over_90_days']} vehicles over 90 days in stock. "
                    "Consider price reductions or targeted ads."
                ),
                "priority": RecommendationPriority.MEDIUM.value,
            })

        if not recs:
            recs.append({
                "category": "general",
                "title": "Maintain momentum",
                "body": "Metrics look stable. Keep daily follow-ups and refresh top listings weekly.",
                "priority": RecommendationPriority.LOW.value,
            })

        return recs

    @staticmethod
    async def generate_ai_recommendations(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        widgets: dict[str, Any] | None = None,
        sections: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        ctx = await DealerPortalEngineV1._require_access(actor_id, tenant_id)

        if widgets is None or sections is None:
            dashboard = await DealerPortalEngineV1.refresh_dashboard(actor_id, tenant_id)
            widgets = dashboard["widgets"]
            sections = dashboard["sections"]

        recommendations = DealerPortalEngineV1._generate_rule_recommendations(widgets, sections)

        try:
            from openrouter import ask_openrouter

            prompt = (
                "You are a dealership AI advisor. Based on dashboard metrics, "
                "give 2 short actionable recommendations in Russian. Be concise.\n"
                f"Widgets: {widgets}\n"
            )
            ai_text = await ask_openrouter(
                [{"role": "user", "content": prompt}],
                ai_settings={"language": "ru", "tone": "professional"},
            )
            recommendations.insert(0, {
                "category": "ai",
                "title": "AI Insight",
                "body": ai_text.strip()[:800],
                "priority": RecommendationPriority.MEDIUM.value,
            })
        except Exception:
            pass

        async with get_session() as session:
            rows = await DealerPortalRecommendationRepository(session).replace_active(
                tenant_id,
                recommendations,
                company_id=ctx.company_id,
            )
            return [DealerPortalEngineV1._reco_snapshot(r) for r in rows]

    @staticmethod
    async def refresh_dashboard(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        ctx = await DealerPortalEngineV1._require_access(actor_id, tenant_id)
        today = datetime.now(timezone.utc).date()

        async with get_session() as session:
            widgets = await DealerPortalEngineV1._build_widgets(session, today=today)

        active_leads = await DealerPortalEngineV1.get_active_leads(actor_id, tenant_id, limit=20)
        active_vehicles = await DealerPortalEngineV1.get_active_vehicles(actor_id, tenant_id, limit=20)
        conversion = await DealerPortalEngineV1.get_conversion_metrics(actor_id, tenant_id)
        advertising = await DealerPortalEngineV1.get_advertising_statistics(actor_id, tenant_id)
        financial = await DealerPortalEngineV1.get_financial_reports(actor_id, tenant_id)

        sections = {
            "active_leads": active_leads,
            "active_vehicles": active_vehicles,
            "conversion_metrics": conversion,
            "advertising_statistics": advertising,
            "financial_reports": financial,
        }

        async with get_session() as session:
            snapshot = await DealerPortalSnapshotRepository(session).upsert(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                snapshot_date=today,
                widgets=widgets,
                sections=sections,
            )

        return {
            "tenant_id": str(tenant_id),
            "snapshot_date": today.isoformat(),
            "widgets": widgets,
            "sections": sections,
            "snapshot_id": str(snapshot.id),
        }

    @staticmethod
    async def get_dashboard(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        refresh: bool = False,
    ) -> dict[str, Any]:
        if refresh:
            dashboard = await DealerPortalEngineV1.refresh_dashboard(actor_id, tenant_id)
        else:
            await DealerPortalEngineV1._require_access(actor_id, tenant_id)
            async with get_session() as session:
                snapshot = await DealerPortalSnapshotRepository(session).get_latest(tenant_id)
            if snapshot is None:
                dashboard = await DealerPortalEngineV1.refresh_dashboard(actor_id, tenant_id)
            else:
                dashboard = {
                    "tenant_id": str(tenant_id),
                    "snapshot_date": snapshot.snapshot_date.isoformat(),
                    "widgets": snapshot.widgets,
                    "sections": snapshot.sections,
                    "snapshot_id": str(snapshot.id),
                }

        recommendations = await DealerPortalEngineV1.generate_ai_recommendations(
            actor_id,
            tenant_id,
            widgets=dashboard["widgets"],
            sections=dashboard["sections"],
        )
        dashboard["ai_recommendations"] = recommendations
        return dashboard

    @staticmethod
    async def list_recommendations(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        await DealerPortalEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            rows = await DealerPortalRecommendationRepository(session).list_active(
                tenant_id,
                limit=limit,
            )
            return [DealerPortalEngineV1._reco_snapshot(r) for r in rows]

    @staticmethod
    async def dismiss_recommendation(
        actor_id: int,
        tenant_id: uuid.UUID,
        recommendation_id: uuid.UUID,
    ) -> dict[str, Any]:
        await DealerPortalEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            row = await DealerPortalRecommendationRepository(session).dismiss(recommendation_id)
            if row is None:
                raise DealerPortalEngineError(f"Recommendation not found: {recommendation_id}")
            return DealerPortalEngineV1._reco_snapshot(row)
