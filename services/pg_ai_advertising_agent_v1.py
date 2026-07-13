# AI Advertising Agent v1 — product layer over advertising engine.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from database.models.ai_advertising_agent import AdvertisingChannel
from services.pg_ai_advertising_agent_engine import (
    AiAdvertisingAgentError,
    AiAdvertisingAgentV1,
)
from services.pg_partner_tenant_engine import PartnerTenantEngineV1

ADVERTISING_FEATURES = frozenset({
    "ad_generation",
    "budget_allocation",
    "campaign_optimization",
    "audience_segmentation",
    "roi_tracking",
})

ADVERTISING_PLATFORMS = frozenset(ch.value for ch in AdvertisingChannel)


class AdvertisingAgentError(Exception):
    pass


class AdvertisingAgentV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        return await AiAdvertisingAgentV1.user_can_access(user_id)

    @staticmethod
    async def _require_access(actor_id: int, tenant_id: uuid.UUID):
        if not await AdvertisingAgentV1.user_can_access(actor_id):
            raise AdvertisingAgentError("Advertising agent access denied")
        return await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

    @staticmethod
    def list_features() -> list[dict[str, str]]:
        labels = {
            "ad_generation": "Ad Generation",
            "budget_allocation": "Budget Allocation",
            "campaign_optimization": "Campaign Optimization",
            "audience_segmentation": "Audience Segmentation",
            "roi_tracking": "ROI Tracking",
        }
        return [{"code": k, "label": labels[k]} for k in sorted(ADVERTISING_FEATURES)]

    @staticmethod
    def list_platforms() -> list[dict[str, str]]:
        return AiAdvertisingAgentV1.list_platforms()

    @staticmethod
    async def get_agent(actor_id: int, tenant_id: uuid.UUID) -> dict[str, Any]:
        ctx = await AdvertisingAgentV1._require_access(actor_id, tenant_id)
        dashboard = await AiAdvertisingAgentV1.get_dealer_dashboard(actor_id, tenant_id)

        return {
            "tenant_id": str(tenant_id),
            "company_id": str(ctx.company_id),
            "platforms": AdvertisingAgentV1.list_platforms(),
            "features": list(ADVERTISING_FEATURES),
            "summary": dashboard,
            "feature_data": {
                "ad_generation": await AdvertisingAgentV1.get_ad_generation_module(
                    actor_id, tenant_id
                ),
                "budget_allocation": await AdvertisingAgentV1.get_budget_allocation_module(
                    actor_id, tenant_id
                ),
                "campaign_optimization": await AdvertisingAgentV1.get_campaign_optimization_module(
                    actor_id, tenant_id
                ),
                "audience_segmentation": await AdvertisingAgentV1.get_audience_segmentation_module(
                    actor_id, tenant_id
                ),
                "roi_tracking": await AdvertisingAgentV1.get_roi_tracking_module(
                    actor_id, tenant_id
                ),
            },
        }

    @staticmethod
    async def get_feature(
        actor_id: int,
        tenant_id: uuid.UUID,
        feature: str,
    ) -> dict[str, Any]:
        if feature not in ADVERTISING_FEATURES:
            raise AdvertisingAgentError(f"Unknown feature: {feature}")
        return await {
            "ad_generation": lambda: AdvertisingAgentV1.get_ad_generation_module(actor_id, tenant_id),
            "budget_allocation": lambda: AdvertisingAgentV1.get_budget_allocation_module(
                actor_id, tenant_id
            ),
            "campaign_optimization": lambda: AdvertisingAgentV1.get_campaign_optimization_module(
                actor_id, tenant_id
            ),
            "audience_segmentation": lambda: AdvertisingAgentV1.get_audience_segmentation_module(
                actor_id, tenant_id
            ),
            "roi_tracking": lambda: AdvertisingAgentV1.get_roi_tracking_module(actor_id, tenant_id),
        }[feature]()

    @staticmethod
    async def get_ad_generation_module(actor_id: int, tenant_id: uuid.UUID) -> dict[str, Any]:
        await AdvertisingAgentV1._require_access(actor_id, tenant_id)
        campaigns = await AiAdvertisingAgentV1.list_campaigns(actor_id, tenant_id, limit=20)
        with_creatives = [c for c in campaigns if c.get("ad_creative")]
        return {
            "feature": "ad_generation",
            "platforms": AdvertisingAgentV1.list_platforms(),
            "campaigns_total": len(campaigns),
            "campaigns_with_creatives": len(with_creatives),
            "campaigns": with_creatives[:10],
        }

    @staticmethod
    async def get_budget_allocation_module(actor_id: int, tenant_id: uuid.UUID) -> dict[str, Any]:
        await AdvertisingAgentV1._require_access(actor_id, tenant_id)
        campaigns = await AiAdvertisingAgentV1.list_campaigns(actor_id, tenant_id, limit=50)
        allocated = [
            {
                "campaign_id": c["id"],
                "name": c["name"],
                "budget_total": c["budget_total"],
                "budget_allocated": c["budget_allocated"],
                "daily_budget": c["daily_budget"],
                "channels": c["channels"],
            }
            for c in campaigns
            if Decimal(c.get("budget_allocated", "0")) > 0
        ]
        return {
            "feature": "budget_allocation",
            "campaigns": allocated,
            "platforms": AdvertisingAgentV1.list_platforms(),
        }

    @staticmethod
    async def get_campaign_optimization_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await AdvertisingAgentV1._require_access(actor_id, tenant_id)
        campaigns = await AiAdvertisingAgentV1.list_campaigns(
            actor_id, tenant_id, status="ACTIVE", limit=10
        )
        optimizations: list[dict[str, Any]] = []
        for campaign in campaigns[:3]:
            try:
                result = await AiAdvertisingAgentV1.optimize_campaign(
                    actor_id, tenant_id, uuid.UUID(campaign["id"])
                )
                optimizations.append(result)
            except AiAdvertisingAgentError:
                continue
        return {
            "feature": "campaign_optimization",
            "optimizations": optimizations,
        }

    @staticmethod
    async def get_audience_segmentation_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await AdvertisingAgentV1._require_access(actor_id, tenant_id)
        campaigns = await AiAdvertisingAgentV1.list_campaigns(actor_id, tenant_id, limit=20)
        segmented = [
            {
                "campaign_id": c["id"],
                "name": c["name"],
                "audience_profile": c.get("audience_profile", {}),
                "channels": c["channels"],
            }
            for c in campaigns
            if c.get("audience_profile")
        ]
        return {
            "feature": "audience_segmentation",
            "segments": segmented,
            "platforms": AdvertisingAgentV1.list_platforms(),
        }

    @staticmethod
    async def get_roi_tracking_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        tracking = await AiAdvertisingAgentV1.track_roi(actor_id, tenant_id)
        return {"feature": "roi_tracking", **tracking}

    @staticmethod
    async def generate_ad(
        actor_id: int,
        tenant_id: uuid.UUID,
        campaign_id: uuid.UUID,
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            return await AiAdvertisingAgentV1.generate_ad(
                actor_id, tenant_id, campaign_id, **kwargs
            )
        except AiAdvertisingAgentError as exc:
            raise AdvertisingAgentError(str(exc)) from exc

    @staticmethod
    async def allocate_budget(
        actor_id: int,
        tenant_id: uuid.UUID,
        campaign_id: uuid.UUID,
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            return await AiAdvertisingAgentV1.allocate_budget(
                actor_id, tenant_id, campaign_id, **kwargs
            )
        except AiAdvertisingAgentError as exc:
            raise AdvertisingAgentError(str(exc)) from exc

    @staticmethod
    async def optimize_campaign(
        actor_id: int,
        tenant_id: uuid.UUID,
        campaign_id: uuid.UUID,
    ) -> dict[str, Any]:
        try:
            return await AiAdvertisingAgentV1.optimize_campaign(actor_id, tenant_id, campaign_id)
        except AiAdvertisingAgentError as exc:
            raise AdvertisingAgentError(str(exc)) from exc

    @staticmethod
    async def segment_audience(
        actor_id: int,
        tenant_id: uuid.UUID,
        campaign_id: uuid.UUID,
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            return await AiAdvertisingAgentV1.target_audience(
                actor_id, tenant_id, campaign_id, **kwargs
            )
        except AiAdvertisingAgentError as exc:
            raise AdvertisingAgentError(str(exc)) from exc

    @staticmethod
    async def track_roi(
        actor_id: int,
        tenant_id: uuid.UUID,
        campaign_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        try:
            return await AiAdvertisingAgentV1.track_roi(actor_id, tenant_id, campaign_id)
        except AiAdvertisingAgentError as exc:
            raise AdvertisingAgentError(str(exc)) from exc
