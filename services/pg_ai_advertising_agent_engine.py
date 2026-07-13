# AI Advertising Agent v1 — ad generation, targeting, budget, bids, campaign monitoring.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import func, select

from config import OWNER_ID
from database.models.ai_advertising_agent import (
    AdvertisingActionType,
    AdvertisingCampaignStatus,
    AdvertisingChannel,
)
from database.models.audit_log import AuditAction
from database.models.auto_marketing_engine import MarketingCampaign
from database.models.car import Car, CarStatus
from database.models.lead_automation_engine import AutomationLead, OPEN_LEAD_STATUSES
from database.session import get_session
from repositories.ai_advertising_agent_repository import (
    AdvertisingAgentActionRepository,
    AdvertisingAgentCampaignRepository,
)
from repositories.audit_repository import AuditRepository
from repositories.auto_marketing_repository import MarketingCampaignRepository
from repositories.car_repository import CarRepository
from repositories.user_role_repository import UserRoleRepository
from services.pg_partner_tenant_engine import PartnerTenantEngineV1

ADVERTISING_AGENT_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
MODEL_VERSION = "ai-advertising-agent-v1.0.0"
MONEY = Decimal("0.01")
CONF = Decimal("0.0001")

CHANNEL_BUDGET_WEIGHTS: dict[str, Decimal] = {
    AdvertisingChannel.FACEBOOK.value: Decimal("0.35"),
    AdvertisingChannel.INSTAGRAM.value: Decimal("0.30"),
    AdvertisingChannel.TIKTOK.value: Decimal("0.20"),
    AdvertisingChannel.TELEGRAM.value: Decimal("0.15"),
}

DEFAULT_BIDS: dict[str, Decimal] = {
    AdvertisingChannel.FACEBOOK.value: Decimal("1.20"),
    AdvertisingChannel.INSTAGRAM.value: Decimal("1.50"),
    AdvertisingChannel.TIKTOK.value: Decimal("0.90"),
    AdvertisingChannel.TELEGRAM.value: Decimal("0.40"),
}


class AiAdvertisingAgentError(Exception):
    pass


class AiAdvertisingAgentV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in ADVERTISING_AGENT_ROLES for role in roles)

    @staticmethod
    async def _require_access(actor_id: int, tenant_id: uuid.UUID):
        if not await AiAdvertisingAgentV1.user_can_access(actor_id):
            raise AiAdvertisingAgentError("Advertising agent access denied")
        return await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

    @staticmethod
    def _quantize(amount: Decimal) -> Decimal:
        return amount.quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def _confidence(score: float) -> Decimal:
        return Decimal(str(max(0.0, min(1.0, score)))).quantize(CONF)

    @staticmethod
    def _campaign_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "company_id": str(row.company_id),
            "marketing_campaign_id": (
                str(row.marketing_campaign_id) if row.marketing_campaign_id else None
            ),
            "car_id": str(row.car_id) if row.car_id else None,
            "name": row.name,
            "status": row.status,
            "channels": row.channels or [],
            "budget_total": str(row.budget_total),
            "budget_allocated": str(row.budget_allocated),
            "budget_spent": str(row.budget_spent),
            "daily_budget": str(row.daily_budget) if row.daily_budget is not None else None,
            "currency": row.currency,
            "audience_profile": row.audience_profile or {},
            "bid_config": row.bid_config or {},
            "ad_creative": row.ad_creative or {},
            "performance_metrics": row.performance_metrics or {},
            "last_monitored_at": (
                row.last_monitored_at.isoformat() if row.last_monitored_at else None
            ),
            "created_by": row.created_by,
            "notes": row.notes,
            "metadata": row.metadata_ or {},
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _action_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "campaign_id": str(row.campaign_id),
            "tenant_id": str(row.tenant_id),
            "action_type": row.action_type,
            "input_context": row.input_context,
            "result": row.result,
            "confidence_score": str(row.confidence_score),
            "model_version": row.model_version,
            "summary": row.summary,
            "created_by": row.created_by,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    async def _get_campaign_or_raise(
        session,
        campaign_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ):
        row = await AdvertisingAgentCampaignRepository(session).get_by_id(campaign_id)
        if row is None or row.tenant_id != tenant_id:
            raise AiAdvertisingAgentError(f"Campaign not found: {campaign_id}")
        return row

    @staticmethod
    async def _log_action(
        session,
        *,
        campaign,
        action_type: str,
        input_context: dict,
        result: dict,
        confidence: float,
        summary: str,
        actor_id: int,
    ) -> dict[str, Any]:
        row = await AdvertisingAgentActionRepository(session).create(
            campaign_id=campaign.id,
            tenant_id=campaign.tenant_id,
            company_id=campaign.company_id,
            action_type=action_type,
            input_context=input_context,
            result=result,
            confidence_score=AiAdvertisingAgentV1._confidence(confidence),
            model_version=MODEL_VERSION,
            summary=summary,
            created_by=actor_id,
        )
        await session.refresh(row)
        return AiAdvertisingAgentV1._action_snapshot(row)

    @staticmethod
    def _rule_based_ad_copy(car) -> dict[str, str]:
        price = str(car.sale_price or car.expected_profit or "Contact for price")
        return {
            "headline": f"{car.year} {car.make} {car.model} — Available Now",
            "primary_text": (
                f"Premium {car.make} {car.model} ({car.year}). "
                f"VIN {car.vin}. Mileage: {car.mileage or 'N/A'} km. "
                f"Price: {price}."
            ),
            "call_to_action": "Contact dealer",
            "hashtags": f"#{car.make.lower()} #{car.model.lower().replace(' ', '')} #forsale #auto",
        }

    @staticmethod
    async def create_campaign(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        name: str,
        channels: list[str],
        budget_total: Decimal | float | int = 0,
        car_id: uuid.UUID | None = None,
        marketing_campaign_id: uuid.UUID | None = None,
        daily_budget: Decimal | float | int | None = None,
        currency: str = "USD",
        activate: bool = False,
    ) -> dict[str, Any]:
        ctx = await AiAdvertisingAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            if car_id is not None:
                car = await CarRepository(session).get_car(car_id)
                if car is None:
                    raise AiAdvertisingAgentError(f"Car not found: {car_id}")
            if marketing_campaign_id is not None:
                mc = await MarketingCampaignRepository(session).get_by_id(marketing_campaign_id)
                if mc is None:
                    raise AiAdvertisingAgentError(
                        f"Marketing campaign not found: {marketing_campaign_id}"
                    )

            status = (
                AdvertisingCampaignStatus.ACTIVE.value
                if activate
                else AdvertisingCampaignStatus.DRAFT.value
            )
            row = await AdvertisingAgentCampaignRepository(session).create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                name=name,
                channels=channels,
                budget_total=Decimal(str(budget_total)),
                car_id=car_id,
                marketing_campaign_id=marketing_campaign_id,
                status=status,
                daily_budget=Decimal(str(daily_budget)) if daily_budget is not None else None,
                currency=currency,
                created_by=actor_id,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="ai_advertising_campaign",
                entity_id=str(row.id),
                action=AuditAction.CREATE.value,
                new_value={"name": name, "channels": channels, "budget_total": str(budget_total)},
            )
            await session.refresh(row)
            return AiAdvertisingAgentV1._campaign_snapshot(row)

    @staticmethod
    async def generate_ad(
        actor_id: int,
        tenant_id: uuid.UUID,
        campaign_id: uuid.UUID,
        *,
        language: str = "en",
    ) -> dict[str, Any]:
        ctx = await AiAdvertisingAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            campaign = await AiAdvertisingAgentV1._get_campaign_or_raise(
                session, campaign_id, tenant_id
            )
            car = None
            if campaign.car_id:
                car = await CarRepository(session).get_car(campaign.car_id)

            creatives: dict[str, Any] = {}
            if car is not None:
                base = AiAdvertisingAgentV1._rule_based_ad_copy(car)
                for channel in campaign.channels:
                    creatives[channel] = {
                        **base,
                        "channel": channel,
                        "format": "single_image" if channel != AdvertisingChannel.TIKTOK.value else "video",
                    }
            else:
                for channel in campaign.channels:
                    creatives[channel] = {
                        "headline": campaign.name,
                        "primary_text": campaign.notes or f"Promotional campaign: {campaign.name}",
                        "call_to_action": "Learn more",
                        "channel": channel,
                    }

            ai_enhancement = await AiAdvertisingAgentV1._optional_ai_ad_copy(
                campaign_name=campaign.name,
                car=car,
                channels=campaign.channels,
                language=language,
            )
            if ai_enhancement:
                creatives["ai_enhanced"] = ai_enhancement

            campaign = await AdvertisingAgentCampaignRepository(session).update_fields(
                campaign_id,
                ad_creative=creatives,
            )

            result = {"creatives": creatives, "channel_count": len(campaign.channels)}
            action = await AiAdvertisingAgentV1._log_action(
                session,
                campaign=campaign,
                action_type=AdvertisingActionType.AD_GENERATION.value,
                input_context={"campaign_id": str(campaign_id), "language": language},
                result=result,
                confidence=0.85 if car else 0.65,
                summary=f"Generated ads for {len(campaign.channels)} channels",
                actor_id=actor_id,
            )

            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="ai_advertising_campaign",
                entity_id=str(campaign_id),
                action=AuditAction.UPDATE.value,
                new_value={"ad_generation": True, "channels": len(campaign.channels)},
            )
            await session.refresh(campaign)
            return {
                "campaign": AiAdvertisingAgentV1._campaign_snapshot(campaign),
                "action": action,
            }

    @staticmethod
    async def target_audience(
        actor_id: int,
        tenant_id: uuid.UUID,
        campaign_id: uuid.UUID,
        *,
        radius_km: int = 50,
        age_min: int = 25,
        age_max: int = 55,
    ) -> dict[str, Any]:
        ctx = await AiAdvertisingAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            campaign = await AiAdvertisingAgentV1._get_campaign_or_raise(
                session, campaign_id, tenant_id
            )

            lead_rows = await session.execute(
                select(
                    AutomationLead.source,
                    func.count().label("cnt"),
                )
                .where(AutomationLead.status.in_(OPEN_LEAD_STATUSES))
                .group_by(AutomationLead.source)
                .order_by(func.count().desc())
                .limit(10)
            )
            source_counts = {row.source: int(row.cnt) for row in lead_rows}

            car = None
            interest_makes: list[str] = []
            if campaign.car_id:
                car = await CarRepository(session).get_car(campaign.car_id)
                if car:
                    interest_makes = [car.make]

            inventory_rows = await session.execute(
                select(Car.make, func.count())
                .where(Car.status == CarStatus.READY_FOR_SALE.value)
                .group_by(Car.make)
                .order_by(func.count().desc())
                .limit(5)
            )
            top_makes = [row[0] for row in inventory_rows if row[0]]
            if not interest_makes:
                interest_makes = top_makes

            audience = {
                "demographics": {
                    "age_min": age_min,
                    "age_max": age_max,
                    "radius_km": radius_km,
                },
                "interests": {
                    "vehicle_makes": interest_makes,
                    "top_inventory_makes": top_makes,
                    "lead_sources": source_counts,
                },
                "behaviors": {
                    "auto_intenders": True,
                    "recent_vehicle_searchers": True,
                    "lookalike_from_leads": bool(source_counts),
                },
                "recommended_channels": AiAdvertisingAgentV1._rank_channels(source_counts, campaign.channels),
            }

            campaign = await AdvertisingAgentCampaignRepository(session).update_fields(
                campaign_id,
                audience_profile=audience,
            )

            action = await AiAdvertisingAgentV1._log_action(
                session,
                campaign=campaign,
                action_type=AdvertisingActionType.AUDIENCE_TARGETING.value,
                input_context={"radius_km": radius_km, "age_min": age_min, "age_max": age_max},
                result=audience,
                confidence=0.78 if source_counts else 0.55,
                summary=f"Audience profile built with {len(interest_makes)} make interests",
                actor_id=actor_id,
            )

            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="ai_advertising_campaign",
                entity_id=str(campaign_id),
                action=AuditAction.UPDATE.value,
                new_value={"audience_targeting": True},
            )
            return {
                "campaign": AiAdvertisingAgentV1._campaign_snapshot(campaign),
                "action": action,
            }

    @staticmethod
    def _rank_channels(
        source_counts: dict[str, int],
        campaign_channels: list[str],
    ) -> list[dict[str, Any]]:
        channel_scores: dict[str, float] = {}
        source_to_channel = {
            "facebook": AdvertisingChannel.FACEBOOK.value,
            "instagram": AdvertisingChannel.INSTAGRAM.value,
            "tiktok": AdvertisingChannel.TIKTOK.value,
            "telegram": AdvertisingChannel.TELEGRAM.value,
        }
        for source, count in source_counts.items():
            mapped = source_to_channel.get(source.lower())
            if mapped:
                channel_scores[mapped] = channel_scores.get(mapped, 0) + count

        ranked = sorted(
            campaign_channels,
            key=lambda ch: channel_scores.get(ch, 0),
            reverse=True,
        )
        return [
            {"channel": ch, "lead_signal_score": channel_scores.get(ch, 0)}
            for ch in ranked
        ]

    @staticmethod
    async def allocate_budget(
        actor_id: int,
        tenant_id: uuid.UUID,
        campaign_id: uuid.UUID,
        *,
        total_budget: Decimal | float | int | None = None,
        duration_days: int = 30,
    ) -> dict[str, Any]:
        ctx = await AiAdvertisingAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            campaign = await AiAdvertisingAgentV1._get_campaign_or_raise(
                session, campaign_id, tenant_id
            )

            budget = Decimal(str(total_budget if total_budget is not None else campaign.budget_total))
            if budget <= 0:
                raise AiAdvertisingAgentError("total_budget must be positive")

            weights_sum = sum(
                CHANNEL_BUDGET_WEIGHTS.get(ch, Decimal("0.25")) for ch in campaign.channels
            )
            allocation: dict[str, str] = {}
            for channel in campaign.channels:
                weight = CHANNEL_BUDGET_WEIGHTS.get(channel, Decimal("0.25")) / weights_sum
                amount = AiAdvertisingAgentV1._quantize(budget * weight)
                allocation[channel] = str(amount)

            daily = AiAdvertisingAgentV1._quantize(budget / Decimal(str(max(duration_days, 1))))

            result = {
                "total_budget": str(budget),
                "duration_days": duration_days,
                "daily_budget": str(daily),
                "channel_allocation": allocation,
                "currency": campaign.currency,
            }

            campaign = await AdvertisingAgentCampaignRepository(session).update_fields(
                campaign_id,
                budget_total=budget,
                budget_allocated=budget,
                daily_budget=daily,
                metadata={"budget_allocation": result},
            )

            action = await AiAdvertisingAgentV1._log_action(
                session,
                campaign=campaign,
                action_type=AdvertisingActionType.BUDGET_ALLOCATION.value,
                input_context={"total_budget": str(budget), "duration_days": duration_days},
                result=result,
                confidence=0.9,
                summary=f"Allocated {budget} {campaign.currency} across {len(campaign.channels)} channels",
                actor_id=actor_id,
            )

            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="ai_advertising_campaign",
                entity_id=str(campaign_id),
                action=AuditAction.UPDATE.value,
                new_value={"budget_allocation": result},
            )
            return {
                "campaign": AiAdvertisingAgentV1._campaign_snapshot(campaign),
                "action": action,
            }

    @staticmethod
    async def optimize_bids(
        actor_id: int,
        tenant_id: uuid.UUID,
        campaign_id: uuid.UUID,
    ) -> dict[str, Any]:
        ctx = await AiAdvertisingAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            campaign = await AiAdvertisingAgentV1._get_campaign_or_raise(
                session, campaign_id, tenant_id
            )

            metrics = campaign.performance_metrics or {}
            channel_metrics = metrics.get("by_channel", {})
            optimized: dict[str, dict[str, str]] = {}
            previous = campaign.bid_config or {}

            for channel in campaign.channels:
                base_bid = Decimal(str(previous.get(channel, {}).get("cpc", DEFAULT_BIDS.get(channel, Decimal("1")))))
                ch_metrics = channel_metrics.get(channel, {})
                ctr = Decimal(str(ch_metrics.get("ctr", "0.02")))
                conversions = int(ch_metrics.get("conversions", 0))
                spend = Decimal(str(ch_metrics.get("spend", "0")))

                if conversions > 0 and spend > 0:
                    cpa = spend / Decimal(str(conversions))
                    new_bid = AiAdvertisingAgentV1._quantize(base_bid * Decimal("1.10"))
                    strategy = "SCALE_WINNER"
                    confidence = 0.88
                elif ctr >= Decimal("0.03"):
                    new_bid = AiAdvertisingAgentV1._quantize(base_bid * Decimal("1.05"))
                    strategy = "INCREASE_ENGAGEMENT"
                    confidence = 0.75
                elif ctr < Decimal("0.01") and spend > Decimal("50"):
                    new_bid = AiAdvertisingAgentV1._quantize(base_bid * Decimal("0.85"))
                    strategy = "REDUCE_WASTE"
                    confidence = 0.82
                else:
                    new_bid = base_bid
                    strategy = "HOLD"
                    confidence = 0.6

                optimized[channel] = {
                    "cpc": str(new_bid),
                    "previous_cpc": str(base_bid),
                    "strategy": strategy,
                    "ctr": str(ctr),
                }

            bid_config = {
                "optimized_at": datetime.now(timezone.utc).isoformat(),
                "channels": optimized,
            }

            campaign = await AdvertisingAgentCampaignRepository(session).update_fields(
                campaign_id,
                bid_config=bid_config,
            )

            action = await AiAdvertisingAgentV1._log_action(
                session,
                campaign=campaign,
                action_type=AdvertisingActionType.BID_OPTIMIZATION.value,
                input_context={"previous_bids": previous},
                result=bid_config,
                confidence=sum(
                    0.88 if v["strategy"] == "SCALE_WINNER" else 0.7 for v in optimized.values()
                ) / max(len(optimized), 1),
                summary=f"Optimized bids for {len(optimized)} channels",
                actor_id=actor_id,
            )

            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="ai_advertising_campaign",
                entity_id=str(campaign_id),
                action=AuditAction.UPDATE.value,
                new_value={"bid_optimization": True},
            )
            return {
                "campaign": AiAdvertisingAgentV1._campaign_snapshot(campaign),
                "action": action,
            }

    @staticmethod
    async def monitor_campaign(
        actor_id: int,
        tenant_id: uuid.UUID,
        campaign_id: uuid.UUID,
    ) -> dict[str, Any]:
        ctx = await AiAdvertisingAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            campaign = await AiAdvertisingAgentV1._get_campaign_or_raise(
                session, campaign_id, tenant_id
            )

            by_channel: dict[str, dict[str, Any]] = {}
            total_spend = Decimal("0")
            total_clicks = 0
            total_impressions = 0
            total_conversions = 0

            if campaign.marketing_campaign_id:
                mc = await MarketingCampaignRepository(session).get_by_id(
                    campaign.marketing_campaign_id
                )
                if mc and mc.metrics:
                    for ch in campaign.channels:
                        ch_data = (mc.metrics or {}).get(ch, {})
                        spend = Decimal(str(ch_data.get("spend", 0)))
                        clicks = int(ch_data.get("clicks", 0))
                        impressions = int(ch_data.get("impressions", 0))
                        conversions = int(ch_data.get("conversions", 0))
                        ctr = Decimal(str(clicks / impressions)) if impressions else Decimal("0")
                        by_channel[ch] = {
                            "spend": str(spend),
                            "clicks": clicks,
                            "impressions": impressions,
                            "conversions": conversions,
                            "ctr": str(AiAdvertisingAgentV1._quantize(ctr)),
                        }
                        total_spend += spend
                        total_clicks += clicks
                        total_impressions += impressions
                        total_conversions += conversions

            if not by_channel:
                for ch in campaign.channels:
                    alloc = Decimal(str((campaign.metadata_ or {}).get("budget_allocation", {}).get("channel_allocation", {}).get(ch, 0)))
                    simulated_spend = alloc * Decimal("0.35")
                    clicks = int(simulated_spend / DEFAULT_BIDS.get(ch, Decimal("1")))
                    impressions = clicks * 40
                    by_channel[ch] = {
                        "spend": str(AiAdvertisingAgentV1._quantize(simulated_spend)),
                        "clicks": clicks,
                        "impressions": impressions,
                        "conversions": max(0, clicks // 25),
                        "ctr": str(AiAdvertisingAgentV1._quantize(Decimal("0.025"))),
                        "simulated": True,
                    }
                    total_spend += simulated_spend
                    total_clicks += clicks
                    total_impressions += impressions
                    total_conversions += max(0, clicks // 25)

            budget_used_pct = (
                float(total_spend / campaign.budget_total * 100)
                if campaign.budget_total > 0
                else 0.0
            )
            alerts: list[str] = []
            if budget_used_pct > 90:
                alerts.append("Budget nearly exhausted")
            if total_conversions == 0 and total_spend > Decimal("100"):
                alerts.append("No conversions recorded — review targeting and creatives")
            if campaign.status == AdvertisingCampaignStatus.ACTIVE.value and not campaign.ad_creative:
                alerts.append("Active campaign missing ad creatives")

            health = "HEALTHY"
            if alerts:
                health = "WARNING" if budget_used_pct < 95 else "CRITICAL"

            performance = {
                "health": health,
                "alerts": alerts,
                "totals": {
                    "spend": str(AiAdvertisingAgentV1._quantize(total_spend)),
                    "clicks": total_clicks,
                    "impressions": total_impressions,
                    "conversions": total_conversions,
                    "budget_used_percent": round(budget_used_pct, 2),
                },
                "by_channel": by_channel,
                "monitored_at": datetime.now(timezone.utc).isoformat(),
            }

            now = datetime.now(timezone.utc)
            campaign = await AdvertisingAgentCampaignRepository(session).update_fields(
                campaign_id,
                budget_spent=AiAdvertisingAgentV1._quantize(total_spend),
                performance_metrics=performance,
                last_monitored_at=now,
            )

            action = await AiAdvertisingAgentV1._log_action(
                session,
                campaign=campaign,
                action_type=AdvertisingActionType.CAMPAIGN_MONITORING.value,
                input_context={"campaign_id": str(campaign_id)},
                result=performance,
                confidence=0.92 if not any(v.get("simulated") for v in by_channel.values()) else 0.5,
                summary=f"Campaign health: {health}, spend {performance['totals']['spend']}",
                actor_id=actor_id,
            )

            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="ai_advertising_campaign",
                entity_id=str(campaign_id),
                action=AuditAction.STATUS_CHANGE.value,
                new_value={"health": health, "alerts": alerts},
            )
            return {
                "campaign": AiAdvertisingAgentV1._campaign_snapshot(campaign),
                "action": action,
            }

    @staticmethod
    async def run_campaign_pipeline(
        actor_id: int,
        tenant_id: uuid.UUID,
        campaign_id: uuid.UUID,
        *,
        total_budget: Decimal | float | int,
        duration_days: int = 30,
    ) -> dict[str, Any]:
        await AiAdvertisingAgentV1._require_access(actor_id, tenant_id)
        ad = await AiAdvertisingAgentV1.generate_ad(actor_id, tenant_id, campaign_id)
        audience = await AiAdvertisingAgentV1.target_audience(actor_id, tenant_id, campaign_id)
        budget = await AiAdvertisingAgentV1.allocate_budget(
            actor_id, tenant_id, campaign_id,
            total_budget=total_budget,
            duration_days=duration_days,
        )
        bids = await AiAdvertisingAgentV1.optimize_bids(actor_id, tenant_id, campaign_id)
        monitor = await AiAdvertisingAgentV1.monitor_campaign(actor_id, tenant_id, campaign_id)
        return {
            "campaign_id": str(campaign_id),
            "ad_generation": ad["action"],
            "audience_targeting": audience["action"],
            "budget_allocation": budget["action"],
            "bid_optimization": bids["action"],
            "campaign_monitoring": monitor["action"],
            "campaign": monitor["campaign"],
        }

    @staticmethod
    async def list_campaigns(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        await AiAdvertisingAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            rows = await AdvertisingAgentCampaignRepository(session).list_by_tenant(
                tenant_id, status=status, limit=limit
            )
            return [AiAdvertisingAgentV1._campaign_snapshot(r) for r in rows]

    @staticmethod
    async def get_dealer_dashboard(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await AiAdvertisingAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            campaigns = await AdvertisingAgentCampaignRepository(session).list_by_tenant(
                tenant_id, limit=100
            )
            active = [c for c in campaigns if c.status == AdvertisingCampaignStatus.ACTIVE.value]
            total_budget = sum((c.budget_total for c in campaigns), Decimal("0"))
            total_spent = sum((c.budget_spent for c in campaigns), Decimal("0"))
            with_creatives = sum(1 for c in campaigns if c.ad_creative)
            with_audience = sum(1 for c in campaigns if c.audience_profile)

            return {
                "tenant_id": str(tenant_id),
                "campaign_count": len(campaigns),
                "active_campaigns": len(active),
                "total_budget": str(AiAdvertisingAgentV1._quantize(total_budget)),
                "total_spent": str(AiAdvertisingAgentV1._quantize(total_spent)),
                "creatives_ready": with_creatives,
                "audience_profiles": with_audience,
                "shared_ai_infrastructure": True,
                "capabilities": [
                    "ad_generation",
                    "audience_targeting",
                    "budget_allocation",
                    "bid_optimization",
                    "campaign_monitoring",
                ],
            }

    @staticmethod
    async def list_actions(
        actor_id: int,
        tenant_id: uuid.UUID,
        campaign_id: uuid.UUID,
        *,
        action_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        await AiAdvertisingAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            await AiAdvertisingAgentV1._get_campaign_or_raise(session, campaign_id, tenant_id)
            rows = await AdvertisingAgentActionRepository(session).list_by_campaign(
                campaign_id, action_type=action_type, limit=limit
            )
            return [AiAdvertisingAgentV1._action_snapshot(r) for r in rows]

    @staticmethod
    async def _optional_ai_ad_copy(
        *,
        campaign_name: str,
        car,
        channels: list[str],
        language: str,
    ) -> dict[str, str] | None:
        try:
            from config import OPENROUTER_API_KEY
            if not OPENROUTER_API_KEY:
                return None
            from openrouter import ask_openrouter

            car_desc = (
                f"{car.year} {car.make} {car.model} VIN {car.vin}"
                if car
                else campaign_name
            )
            prompt = (
                f"Write a short automotive ad copy for channels {', '.join(channels)}. "
                f"Vehicle: {car_desc}. Max 120 words. Include a strong CTA."
            )
            text = await ask_openrouter(
                [{"role": "user", "content": prompt}],
                ai_settings={"language": language, "tone": "professional"},
            )
            return {"body": text.strip()[:800], "language": language}
        except Exception:
            return None
