# Lead Marketplace v1 — unified lead marketplace with distribution, auction, exclusive, scoring, pricing.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from database.models.lead_marketplace_engine import (
    MarketplaceDistributionMode,
    MarketplaceListingStatus,
)
from database.session import get_session
from repositories.lead_automation_repository import LeadAutomationRepository
from services.pg_lead_marketplace_engine import (
    LeadMarketplaceEngineError,
    LeadMarketplaceEngineV1,
)
from services.pg_partner_tenant_engine import PartnerTenantEngineV1

MARKETPLACE_FEATURES = frozenset({
    "lead_distribution",
    "exclusive_leads",
    "lead_auction",
    "lead_scoring",
    "lead_pricing",
})


class LeadMarketplaceError(Exception):
    pass


class LeadMarketplaceV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        return await LeadMarketplaceEngineV1.user_can_access(user_id)

    @staticmethod
    async def _require_access(actor_id: int, tenant_id: uuid.UUID):
        if not await LeadMarketplaceV1.user_can_access(actor_id):
            raise LeadMarketplaceError("Lead marketplace access denied")
        return await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

    @staticmethod
    def list_features() -> list[dict[str, str]]:
        labels = {
            "lead_distribution": "Lead Distribution",
            "exclusive_leads": "Exclusive Leads",
            "lead_auction": "Lead Auction",
            "lead_scoring": "Lead Scoring",
            "lead_pricing": "Lead Pricing",
        }
        return [{"code": code, "label": labels[code]} for code in sorted(MARKETPLACE_FEATURES)]

    @staticmethod
    async def get_marketplace(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        ctx = await LeadMarketplaceV1._require_access(actor_id, tenant_id)

        distribution = await LeadMarketplaceV1.get_lead_distribution_module(actor_id, tenant_id)
        exclusive = await LeadMarketplaceV1.get_exclusive_leads_module(actor_id, tenant_id)
        auction = await LeadMarketplaceV1.get_lead_auction_module(actor_id, tenant_id)
        scoring = await LeadMarketplaceV1.get_lead_scoring_module(actor_id, tenant_id)
        pricing = await LeadMarketplaceV1.get_lead_pricing_module(actor_id, tenant_id)

        return {
            "tenant_id": str(tenant_id),
            "company_id": str(ctx.company_id),
            "features": list(MARKETPLACE_FEATURES),
            "distribution_modes": await LeadMarketplaceEngineV1.list_distribution_modes(),
            "summary": {
                "open_distribution_listings": len(distribution.get("open_listings", [])),
                "open_exclusive_listings": len(exclusive.get("open_listings", [])),
                "open_auction_listings": len(auction.get("open_listings", [])),
                "pricing_rules": len(pricing.get("pricing_rules", [])),
                "scored_leads_sample": len(scoring.get("leads", [])),
            },
            "feature_data": {
                "lead_distribution": distribution,
                "exclusive_leads": exclusive,
                "lead_auction": auction,
                "lead_scoring": scoring,
                "lead_pricing": pricing,
            },
        }

    @staticmethod
    async def get_feature(
        actor_id: int,
        tenant_id: uuid.UUID,
        feature: str,
    ) -> dict[str, Any]:
        if feature not in MARKETPLACE_FEATURES:
            raise LeadMarketplaceError(f"Unknown feature: {feature}")

        getters = {
            "lead_distribution": LeadMarketplaceV1.get_lead_distribution_module,
            "exclusive_leads": LeadMarketplaceV1.get_exclusive_leads_module,
            "lead_auction": LeadMarketplaceV1.get_lead_auction_module,
            "lead_scoring": LeadMarketplaceV1.get_lead_scoring_module,
            "lead_pricing": LeadMarketplaceV1.get_lead_pricing_module,
        }
        return await getters[feature](actor_id, tenant_id)

    @staticmethod
    async def get_lead_distribution_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await LeadMarketplaceV1._require_access(actor_id, tenant_id)
        listings = await LeadMarketplaceEngineV1.list_listings(
            actor_id,
            tenant_id,
            distribution_mode=MarketplaceDistributionMode.DISTRIBUTION.value,
            limit=50,
        )
        open_listings = [l for l in listings if l.get("status") == MarketplaceListingStatus.OPEN.value]
        marketplace = await LeadMarketplaceEngineV1.list_listings(
            actor_id,
            None,
            marketplace_only=True,
            distribution_mode=MarketplaceDistributionMode.DISTRIBUTION.value,
            limit=20,
        )
        return {
            "feature": "lead_distribution",
            "open_listings": open_listings,
            "marketplace_feed": marketplace,
            "description": "Broadcast leads to buyer tenants; first accept wins.",
        }

    @staticmethod
    async def get_exclusive_leads_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await LeadMarketplaceV1._require_access(actor_id, tenant_id)
        listings = await LeadMarketplaceEngineV1.list_listings(
            actor_id,
            tenant_id,
            distribution_mode=MarketplaceDistributionMode.EXCLUSIVE.value,
            limit=50,
        )
        open_listings = [l for l in listings if l.get("status") == MarketplaceListingStatus.OPEN.value]
        marketplace = await LeadMarketplaceEngineV1.list_listings(
            actor_id,
            None,
            marketplace_only=True,
            distribution_mode=MarketplaceDistributionMode.EXCLUSIVE.value,
            limit=20,
        )
        return {
            "feature": "exclusive_leads",
            "open_listings": open_listings,
            "marketplace_feed": marketplace,
            "description": "Single-buyer exclusive purchase at premium pricing.",
        }

    @staticmethod
    async def get_lead_auction_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await LeadMarketplaceV1._require_access(actor_id, tenant_id)
        listings = await LeadMarketplaceEngineV1.list_listings(
            actor_id,
            tenant_id,
            distribution_mode=MarketplaceDistributionMode.AUCTION.value,
            limit=50,
        )
        open_listings = [l for l in listings if l.get("status") == MarketplaceListingStatus.OPEN.value]

        auctions_with_bids: list[dict[str, Any]] = []
        for listing in open_listings[:10]:
            listing_id = uuid.UUID(listing["id"])
            offers = await LeadMarketplaceEngineV1.list_offers(
                actor_id, tenant_id, listing_id, offer_type="BID"
            )
            auctions_with_bids.append({
                **listing,
                "bid_count": len(offers),
                "top_bid": offers[0]["amount"] if offers else None,
            })

        return {
            "feature": "lead_auction",
            "open_listings": open_listings,
            "active_auctions": auctions_with_bids,
            "description": "Competitive bidding with optional reserve price.",
        }

    @staticmethod
    async def get_lead_scoring_module(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        limit: int = 20,
    ) -> dict[str, Any]:
        await LeadMarketplaceV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            leads = await LeadAutomationRepository(session).list_leads(limit=limit)

        scored: list[dict[str, Any]] = []
        for lead in leads:
            if lead.is_duplicate:
                continue
            score, factors = LeadMarketplaceEngineV1.score_lead_quality(lead)
            scored.append({
                "automation_lead_id": str(lead.id),
                "customer_name": lead.customer_name,
                "source": lead.source,
                "status": lead.status,
                "automation_score": lead.score,
                "marketplace_score": score,
                "quality_factors": factors,
            })

        scored.sort(key=lambda item: item["marketplace_score"], reverse=True)
        avg_score = (
            round(sum(item["marketplace_score"] for item in scored) / len(scored), 1)
            if scored
            else 0
        )

        return {
            "feature": "lead_scoring",
            "leads": scored[:limit],
            "average_score": avg_score,
            "description": "Quality scoring from lead automation plus marketplace boosters.",
        }

    @staticmethod
    async def get_lead_pricing_module(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await LeadMarketplaceV1._require_access(actor_id, tenant_id)
        rules = await LeadMarketplaceEngineV1.list_pricing_rules(actor_id, tenant_id)
        modes = await LeadMarketplaceEngineV1.list_distribution_modes()

        samples: list[dict[str, Any]] = []
        async with get_session() as session:
            leads = await LeadAutomationRepository(session).list_leads(limit=5)
            for lead in leads:
                if lead.is_duplicate:
                    continue
                for mode in (
                    MarketplaceDistributionMode.DISTRIBUTION.value,
                    MarketplaceDistributionMode.AUCTION.value,
                    MarketplaceDistributionMode.EXCLUSIVE.value,
                ):
                    pricing = await LeadMarketplaceEngineV1.get_lead_pricing(
                        actor_id,
                        tenant_id,
                        lead.id,
                        distribution_mode=mode,
                    )
                    samples.append({
                        "automation_lead_id": str(lead.id),
                        "customer_name": lead.customer_name,
                        "mode": mode,
                        "price": pricing["price"],
                        "quality_score": pricing["quality_score"],
                    })
                break

        return {
            "feature": "lead_pricing",
            "pricing_rules": rules,
            "distribution_modes": modes,
            "sample_quotes": samples,
            "description": "Rule-based pricing by quality score and distribution mode.",
        }

    @staticmethod
    async def score_lead(
        actor_id: int,
        tenant_id: uuid.UUID,
        automation_lead_id: uuid.UUID,
    ) -> dict[str, Any]:
        await LeadMarketplaceV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            lead = await LeadAutomationRepository(session).get_by_id(automation_lead_id)
            if lead is None:
                raise LeadMarketplaceError(f"Lead not found: {automation_lead_id}")

        score, factors = LeadMarketplaceEngineV1.score_lead_quality(lead)
        return {
            "automation_lead_id": str(automation_lead_id),
            "marketplace_score": score,
            "quality_factors": factors,
            "automation_score": lead.score,
        }

    @staticmethod
    async def quote_lead_price(
        actor_id: int,
        tenant_id: uuid.UUID,
        automation_lead_id: uuid.UUID,
        *,
        distribution_mode: str = MarketplaceDistributionMode.DISTRIBUTION.value,
        pricing_rule_code: str | None = None,
    ) -> dict[str, Any]:
        try:
            return await LeadMarketplaceEngineV1.get_lead_pricing(
                actor_id,
                tenant_id,
                automation_lead_id,
                distribution_mode=distribution_mode,
                pricing_rule_code=pricing_rule_code,
            )
        except LeadMarketplaceEngineError as exc:
            raise LeadMarketplaceError(str(exc)) from exc

    @staticmethod
    async def publish_lead(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        automation_lead_id: uuid.UUID,
        distribution_mode: str,
        pricing_rule_code: str | None = None,
        exclusive_buyer_tenant_id: uuid.UUID | None = None,
        reserve_price: Decimal | float | int | None = None,
        publish: bool = True,
    ) -> dict[str, Any]:
        try:
            listing = await LeadMarketplaceEngineV1.create_listing(
                actor_id,
                tenant_id,
                automation_lead_id=automation_lead_id,
                distribution_mode=distribution_mode,
                pricing_rule_code=pricing_rule_code,
                exclusive_buyer_tenant_id=exclusive_buyer_tenant_id,
                reserve_price=reserve_price,
                publish=publish,
            )
            score = await LeadMarketplaceV1.score_lead(actor_id, tenant_id, automation_lead_id)
            return {"listing": listing, "scoring": score}
        except LeadMarketplaceEngineError as exc:
            raise LeadMarketplaceError(str(exc)) from exc

    @staticmethod
    async def distribute_lead(
        actor_id: int,
        tenant_id: uuid.UUID,
        listing_id: uuid.UUID,
        *,
        buyer_tenant_ids: list[uuid.UUID],
    ) -> dict[str, Any]:
        try:
            return await LeadMarketplaceEngineV1.distribute_lead(
                actor_id, tenant_id, listing_id, buyer_tenant_ids=buyer_tenant_ids
            )
        except LeadMarketplaceEngineError as exc:
            raise LeadMarketplaceError(str(exc)) from exc

    @staticmethod
    async def accept_distribution(
        actor_id: int,
        buyer_tenant_id: uuid.UUID,
        listing_id: uuid.UUID,
    ) -> dict[str, Any]:
        try:
            return await LeadMarketplaceEngineV1.accept_distribution(
                actor_id, buyer_tenant_id, listing_id
            )
        except LeadMarketplaceEngineError as exc:
            raise LeadMarketplaceError(str(exc)) from exc

    @staticmethod
    async def place_bid(
        actor_id: int,
        buyer_tenant_id: uuid.UUID,
        listing_id: uuid.UUID,
        *,
        amount: Decimal | float | int,
    ) -> dict[str, Any]:
        try:
            return await LeadMarketplaceEngineV1.place_bid(
                actor_id, buyer_tenant_id, listing_id, amount=amount
            )
        except LeadMarketplaceEngineError as exc:
            raise LeadMarketplaceError(str(exc)) from exc

    @staticmethod
    async def purchase_exclusive(
        actor_id: int,
        buyer_tenant_id: uuid.UUID,
        listing_id: uuid.UUID,
    ) -> dict[str, Any]:
        try:
            return await LeadMarketplaceEngineV1.purchase_exclusive(
                actor_id, buyer_tenant_id, listing_id
            )
        except LeadMarketplaceEngineError as exc:
            raise LeadMarketplaceError(str(exc)) from exc

    @staticmethod
    async def close_auction(
        actor_id: int,
        tenant_id: uuid.UUID,
        listing_id: uuid.UUID,
    ) -> dict[str, Any]:
        try:
            return await LeadMarketplaceEngineV1.close_auction(actor_id, tenant_id, listing_id)
        except LeadMarketplaceEngineError as exc:
            raise LeadMarketplaceError(str(exc)) from exc

    @staticmethod
    async def create_pricing_rule(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        code: str,
        name: str,
        base_price: Decimal | float | int,
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            return await LeadMarketplaceEngineV1.create_pricing_rule(
                actor_id, tenant_id, code=code, name=name, base_price=base_price, **kwargs
            )
        except LeadMarketplaceEngineError as exc:
            raise LeadMarketplaceError(str(exc)) from exc
