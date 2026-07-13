# Dealer Portal v1 — unified dealer portal with modules and widgets.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select

from database.models.sales_pipeline_automation_engine import PipelineLead, PipelineStage
from database.session import get_session
from services.pg_dealer_portal_engine import DealerPortalEngineV1, DealerPortalEngineError
from services.pg_partner_tenant_engine import PartnerTenantEngineV1

PORTAL_MODULES = frozenset({
    "dashboard",
    "leads",
    "inventory",
    "sales",
    "marketing",
    "finance",
    "ai_recommendations",
})

PORTAL_WIDGETS = (
    "leads_today",
    "active_deals",
    "inventory_value",
    "advertising_spend",
    "monthly_profit",
    "conversion_rate",
    "vehicle_aging",
    "ai_insights",
)

ACTIVE_DEAL_STAGES = frozenset({
    PipelineStage.INTERESTED.value,
    PipelineStage.INSPECTION_SCHEDULED.value,
    PipelineStage.NEGOTIATION.value,
    PipelineStage.RESERVED.value,
})


class DealerPortalError(Exception):
    pass


class DealerPortalV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        return await DealerPortalEngineV1.user_can_access(user_id)

    @staticmethod
    async def _require_access(actor_id: int, tenant_id: uuid.UUID):
        if not await DealerPortalV1.user_can_access(actor_id):
            raise DealerPortalError("Dealer portal access denied")
        return await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

    @staticmethod
    def list_modules() -> list[dict[str, str]]:
        labels = {
            "dashboard": "Dashboard",
            "leads": "Leads",
            "inventory": "Inventory",
            "sales": "Sales",
            "marketing": "Marketing",
            "finance": "Finance",
            "ai_recommendations": "AI Recommendations",
        }
        return [{"code": code, "label": labels[code]} for code in sorted(PORTAL_MODULES)]

    @staticmethod
    def _normalize_widgets(raw: dict[str, Any], recommendations: list[dict[str, Any]]) -> dict[str, Any]:
        aging = raw.get("vehicle_aging") or {}
        top_insight = None
        if recommendations:
            top_insight = {
                "title": recommendations[0].get("title"),
                "category": recommendations[0].get("category"),
                "priority": recommendations[0].get("priority"),
            }

        return {
            "leads_today": raw.get("leads_today", 0),
            "active_deals": raw.get("active_deals", 0),
            "inventory_value": raw.get("inventory_value"),
            "advertising_spend": raw.get("advertising_spend") or raw.get("ad_spend"),
            "monthly_profit": raw.get("monthly_profit") or raw.get("profit_this_month"),
            "conversion_rate": raw.get("conversion_rate") or raw.get("conversion_rate_percent"),
            "vehicle_aging": {
                "avg_days": aging.get("avg_days", 0),
                "vehicles_over_90_days": aging.get("vehicles_over_90_days", 0),
                "oldest_days": aging.get("oldest_days", 0),
            },
            "ai_insights": {
                "count": len(recommendations),
                "top_insight": top_insight,
            },
        }

    @staticmethod
    async def get_portal(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        refresh: bool = False,
    ) -> dict[str, Any]:
        ctx = await DealerPortalV1._require_access(actor_id, tenant_id)
        dashboard = await DealerPortalEngineV1.get_dashboard(
            actor_id, tenant_id, refresh=refresh
        )
        recommendations = dashboard.get("ai_recommendations", [])
        widgets = DealerPortalV1._normalize_widgets(dashboard.get("widgets", {}), recommendations)

        modules = {
            "dashboard": await DealerPortalV1.get_dashboard_module(actor_id, tenant_id, dashboard=dashboard, widgets=widgets),
            "leads": await DealerPortalV1.get_leads_module(actor_id, tenant_id),
            "inventory": await DealerPortalV1.get_inventory_module(actor_id, tenant_id),
            "sales": await DealerPortalV1.get_sales_module(actor_id, tenant_id),
            "marketing": await DealerPortalV1.get_marketing_module(actor_id, tenant_id),
            "finance": await DealerPortalV1.get_finance_module(actor_id, tenant_id),
            "ai_recommendations": await DealerPortalV1.get_ai_recommendations_module(
                actor_id, tenant_id, recommendations=recommendations
            ),
        }

        return {
            "tenant_id": str(tenant_id),
            "company_id": str(ctx.company_id),
            "snapshot_date": dashboard.get("snapshot_date"),
            "modules": list(PORTAL_MODULES),
            "widgets": widgets,
            "module_data": modules,
        }

    @staticmethod
    async def get_module(
        actor_id: int,
        tenant_id: uuid.UUID,
        module: str,
        *,
        refresh: bool = False,
    ) -> dict[str, Any]:
        if module not in PORTAL_MODULES:
            raise DealerPortalError(f"Unknown module: {module}")

        getters = {
            "dashboard": lambda: DealerPortalV1.get_portal(actor_id, tenant_id, refresh=refresh),
            "leads": lambda: DealerPortalV1.get_leads_module(actor_id, tenant_id),
            "inventory": lambda: DealerPortalV1.get_inventory_module(actor_id, tenant_id),
            "sales": lambda: DealerPortalV1.get_sales_module(actor_id, tenant_id),
            "marketing": lambda: DealerPortalV1.get_marketing_module(actor_id, tenant_id),
            "finance": lambda: DealerPortalV1.get_finance_module(actor_id, tenant_id),
            "ai_recommendations": lambda: DealerPortalV1.get_ai_recommendations_module(actor_id, tenant_id),
        }
        if module == "dashboard":
            portal = await getters[module]()
            return portal["module_data"]["dashboard"]
        return await getters[module]()

    @staticmethod
    async def get_dashboard_module(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        dashboard: dict[str, Any] | None = None,
        widgets: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if dashboard is None:
            dashboard = await DealerPortalEngineV1.get_dashboard(actor_id, tenant_id)
        if widgets is None:
            widgets = DealerPortalV1._normalize_widgets(
                dashboard.get("widgets", {}),
                dashboard.get("ai_recommendations", []),
            )
        return {
            "module": "dashboard",
            "widgets": widgets,
            "snapshot_id": dashboard.get("snapshot_id"),
            "snapshot_date": dashboard.get("snapshot_date"),
        }

    @staticmethod
    async def get_leads_module(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> dict[str, Any]:
        await DealerPortalV1._require_access(actor_id, tenant_id)
        leads = await DealerPortalEngineV1.get_active_leads(actor_id, tenant_id, limit=limit)
        conversion = await DealerPortalEngineV1.get_conversion_metrics(actor_id, tenant_id)
        return {
            "module": "leads",
            "active_leads": leads,
            "total_leads": conversion.get("total_leads", 0),
            "conversion_rate": conversion.get("conversion_rate_percent"),
        }

    @staticmethod
    async def get_inventory_module(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> dict[str, Any]:
        await DealerPortalV1._require_access(actor_id, tenant_id)
        vehicles = await DealerPortalEngineV1.get_active_vehicles(actor_id, tenant_id, limit=limit)
        financial = await DealerPortalEngineV1.get_financial_reports(actor_id, tenant_id)

        async with get_session() as session:
            aging = await DealerPortalEngineV1._build_vehicle_aging(session)

        return {
            "module": "inventory",
            "vehicles": vehicles,
            "inventory_value": financial.get("inventory_value"),
            "vehicle_count": len(vehicles),
            "vehicle_aging": aging,
        }

    @staticmethod
    async def get_sales_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await DealerPortalV1._require_access(actor_id, tenant_id)
        conversion = await DealerPortalEngineV1.get_conversion_metrics(actor_id, tenant_id)

        async with get_session() as session:
            active_deals_result = await session.execute(
                select(func.count())
                .select_from(PipelineLead)
                .where(PipelineLead.stage.in_(ACTIVE_DEAL_STAGES))
            )
            active_deals = int(active_deals_result.scalar_one() or 0)

            recent_result = await session.execute(
                select(PipelineLead)
                .where(PipelineLead.stage.in_(ACTIVE_DEAL_STAGES))
                .order_by(PipelineLead.last_activity_at.desc().nullslast())
                .limit(20)
            )
            recent_deals = [
                {
                    "id": str(row.id),
                    "stage": row.stage,
                    "car_id": str(row.car_id) if row.car_id else None,
                    "assigned_manager_id": row.assigned_manager_id,
                    "last_activity_at": (
                        row.last_activity_at.isoformat() if row.last_activity_at else None
                    ),
                }
                for row in recent_result.scalars().all()
            ]

        return {
            "module": "sales",
            "active_deals": active_deals,
            "sold_total": conversion.get("sold_count", 0),
            "pipeline_by_stage": conversion.get("pipeline_by_stage", {}),
            "recent_active_deals": recent_deals,
        }

    @staticmethod
    async def get_marketing_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await DealerPortalV1._require_access(actor_id, tenant_id)
        advertising = await DealerPortalEngineV1.get_advertising_statistics(actor_id, tenant_id)
        return {
            "module": "marketing",
            "advertising_spend": advertising.get("ad_spend"),
            "campaigns": advertising.get("campaigns", []),
            "total_published": advertising.get("total_published", 0),
            "estimated_roi_percent": advertising.get("estimated_roi_percent"),
        }

    @staticmethod
    async def get_finance_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await DealerPortalV1._require_access(actor_id, tenant_id)
        financial = await DealerPortalEngineV1.get_financial_reports(actor_id, tenant_id)
        return {
            "module": "finance",
            "monthly_profit": financial.get("profit_this_month"),
            "revenue_this_month": financial.get("revenue_this_month"),
            "inventory_value": financial.get("inventory_value"),
            "period_start": financial.get("period_start"),
            "period_end": financial.get("period_end"),
            "currency": financial.get("currency", "USD"),
        }

    @staticmethod
    async def get_ai_recommendations_module(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        recommendations: list[dict[str, Any]] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        await DealerPortalV1._require_access(actor_id, tenant_id)
        if recommendations is None:
            recommendations = await DealerPortalEngineV1.list_recommendations(
                actor_id, tenant_id, limit=limit
            )
        return {
            "module": "ai_recommendations",
            "recommendations": recommendations,
            "count": len(recommendations),
        }

    @staticmethod
    async def dismiss_recommendation(
        actor_id: int,
        tenant_id: uuid.UUID,
        recommendation_id: uuid.UUID,
    ) -> dict[str, Any]:
        try:
            return await DealerPortalEngineV1.dismiss_recommendation(
                actor_id, tenant_id, recommendation_id
            )
        except DealerPortalEngineError as exc:
            raise DealerPortalError(str(exc)) from exc

    @staticmethod
    async def refresh_portal(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        return await DealerPortalV1.get_portal(actor_id, tenant_id, refresh=True)
