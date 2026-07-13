# Lead Marketplace Engine v1 — distribution, auction, exclusive mode, pricing, quality scoring.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.lead_automation_engine import AutomationLead, AutomationLeadStatus
from database.models.lead_marketplace_engine import (
    MARKETPLACE_DISTRIBUTION_MODES,
    MarketplaceDistributionMode,
    MarketplaceListingStatus,
    MarketplaceOfferStatus,
    MarketplaceOfferType,
)
from database.models.partner_tenant_engine import TenantResourceType
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.lead_automation_repository import LeadAutomationRepository
from repositories.lead_marketplace_repository import (
    LeadMarketplaceListingRepository,
    LeadMarketplaceOfferRepository,
    LeadMarketplacePricingRuleRepository,
)
from repositories.partner_tenant_repository import PartnerTenantRepository
from repositories.user_role_repository import UserRoleRepository
from services.pg_lead_automation_engine import LeadAutomationEngineV1
from services.pg_partner_tenant_engine import PartnerTenantEngineV1

MONEY = Decimal("0.01")
MARKETPLACE_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
DEFAULT_AUCTION_HOURS = 24
DEFAULT_DISTRIBUTION_HOURS = 12


class LeadMarketplaceEngineError(Exception):
    pass


class LeadMarketplaceEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in MARKETPLACE_ROLES for role in roles)

    @staticmethod
    def _quantize(amount: Decimal) -> Decimal:
        return amount.quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    async def _require_access(actor_id: int, tenant_id: uuid.UUID):
        if not await LeadMarketplaceEngineV1.user_can_access(actor_id):
            raise LeadMarketplaceEngineError("Lead marketplace access denied")
        return await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

    @staticmethod
    def _listing_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "company_id": str(row.company_id),
            "automation_lead_id": str(row.automation_lead_id),
            "distribution_mode": row.distribution_mode,
            "status": row.status,
            "base_price": str(row.base_price),
            "reserve_price": str(row.reserve_price) if row.reserve_price is not None else None,
            "final_price": str(row.final_price) if row.final_price is not None else None,
            "currency": row.currency,
            "quality_score": row.quality_score,
            "quality_factors": row.quality_factors,
            "pricing_breakdown": row.pricing_breakdown,
            "buyer_tenant_id": str(row.buyer_tenant_id) if row.buyer_tenant_id else None,
            "exclusive_buyer_tenant_id": (
                str(row.exclusive_buyer_tenant_id) if row.exclusive_buyer_tenant_id else None
            ),
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
            "notes": row.notes,
            "metadata": row.metadata_ or {},
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _offer_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "listing_id": str(row.listing_id),
            "buyer_tenant_id": str(row.buyer_tenant_id),
            "actor_id": row.actor_id,
            "offer_type": row.offer_type,
            "amount": str(row.amount),
            "status": row.status,
            "metadata": row.metadata_ or {},
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _pricing_rule_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "company_id": str(row.company_id),
            "code": row.code,
            "name": row.name,
            "min_quality_score": row.min_quality_score,
            "max_quality_score": row.max_quality_score,
            "base_price": str(row.base_price),
            "price_per_score_point": str(row.price_per_score_point),
            "auction_premium_percent": str(row.auction_premium_percent),
            "exclusive_multiplier": str(row.exclusive_multiplier),
            "default_distribution_mode": row.default_distribution_mode,
            "currency": row.currency,
            "is_active": row.is_active,
            "metadata": row.metadata_ or {},
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def score_lead_quality(
        lead,
        *,
        marketplace_boost: int = 0,
    ) -> tuple[int, dict[str, int]]:
        base_score, factors = LeadAutomationEngineV1.calculate_score(
            source=lead.source,
            phone=lead.phone,
            email=lead.email,
            car_id=lead.car_id,
            budget=lead.budget,
            customer_name=lead.customer_name,
            source_metadata=lead.source_metadata,
        )
        if lead.score and lead.score > base_score:
            factors["automation_score"] = lead.score - base_score
            base_score = lead.score

        if lead.budget is not None and Decimal(str(lead.budget)) >= Decimal("10000"):
            factors["high_budget"] = 10
        elif lead.budget is not None and Decimal(str(lead.budget)) >= Decimal("5000"):
            factors["medium_budget"] = 5

        if lead.status == AutomationLeadStatus.QUALIFIED.value:
            factors["qualified_status"] = 10
        elif lead.status == AutomationLeadStatus.ASSIGNED.value:
            factors["assigned_status"] = 5

        if marketplace_boost:
            factors["marketplace_boost"] = marketplace_boost

        total = min(100, sum(factors.values()))
        return total, factors

    @staticmethod
    def calculate_lead_price(
        *,
        quality_score: int,
        base_price: Decimal,
        price_per_score_point: Decimal = Decimal("0"),
        distribution_mode: str = MarketplaceDistributionMode.DISTRIBUTION.value,
        auction_premium_percent: Decimal = Decimal("0"),
        exclusive_multiplier: Decimal = Decimal("1.5"),
    ) -> tuple[Decimal, dict[str, str]]:
        score_component = LeadMarketplaceEngineV1._quantize(
            Decimal(str(quality_score)) * price_per_score_point
        )
        subtotal = LeadMarketplaceEngineV1._quantize(base_price + score_component)
        breakdown: dict[str, str] = {
            "base_price": str(base_price),
            "score_component": str(score_component),
            "subtotal": str(subtotal),
        }

        if distribution_mode == MarketplaceDistributionMode.AUCTION.value:
            premium = LeadMarketplaceEngineV1._quantize(
                subtotal * auction_premium_percent / Decimal("100")
            )
            total = LeadMarketplaceEngineV1._quantize(subtotal + premium)
            breakdown["auction_premium_percent"] = str(auction_premium_percent)
            breakdown["auction_premium"] = str(premium)
            breakdown["total"] = str(total)
            return total, breakdown

        if distribution_mode == MarketplaceDistributionMode.EXCLUSIVE.value:
            total = LeadMarketplaceEngineV1._quantize(subtotal * exclusive_multiplier)
            breakdown["exclusive_multiplier"] = str(exclusive_multiplier)
            breakdown["total"] = str(total)
            return total, breakdown

        breakdown["total"] = str(subtotal)
        return subtotal, breakdown

    @staticmethod
    async def create_pricing_rule(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        code: str,
        name: str,
        base_price: Decimal | float | int,
        price_per_score_point: Decimal | float | int = 0,
        min_quality_score: int = 0,
        max_quality_score: int = 100,
        auction_premium_percent: Decimal | float | int = 0,
        exclusive_multiplier: Decimal | float | int = Decimal("1.5"),
        default_distribution_mode: str = MarketplaceDistributionMode.DISTRIBUTION.value,
        currency: str = "USD",
    ) -> dict[str, Any]:
        ctx = await LeadMarketplaceEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            existing = await LeadMarketplacePricingRuleRepository(session).get_by_code(
                tenant_id, code
            )
            if existing is not None:
                raise LeadMarketplaceEngineError(f"Pricing rule already exists: {code}")

            row = await LeadMarketplacePricingRuleRepository(session).create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                code=code,
                name=name,
                base_price=Decimal(str(base_price)),
                price_per_score_point=Decimal(str(price_per_score_point)),
                min_quality_score=min_quality_score,
                max_quality_score=max_quality_score,
                auction_premium_percent=Decimal(str(auction_premium_percent)),
                exclusive_multiplier=Decimal(str(exclusive_multiplier)),
                default_distribution_mode=default_distribution_mode,
                currency=currency,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="lead_marketplace_pricing_rule",
                entity_id=str(row.id),
                action=AuditAction.CREATE.value,
                new_value={"code": row.code, "base_price": str(row.base_price)},
            )
            await session.refresh(row)
            return LeadMarketplaceEngineV1._pricing_rule_snapshot(row)

    @staticmethod
    async def list_pricing_rules(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        active_only: bool = True,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        await LeadMarketplaceEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            rows = await LeadMarketplacePricingRuleRepository(session).list_by_tenant(
                tenant_id, active_only=active_only, limit=limit
            )
            return [LeadMarketplaceEngineV1._pricing_rule_snapshot(r) for r in rows]

    @staticmethod
    async def create_listing(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        automation_lead_id: uuid.UUID,
        distribution_mode: str | None = None,
        pricing_rule_code: str | None = None,
        reserve_price: Decimal | float | int | None = None,
        exclusive_buyer_tenant_id: uuid.UUID | None = None,
        expires_in_hours: int | None = None,
        publish: bool = True,
        notes: str | None = None,
    ) -> dict[str, Any]:
        ctx = await LeadMarketplaceEngineV1._require_access(actor_id, tenant_id)
        if distribution_mode is not None and distribution_mode not in MARKETPLACE_DISTRIBUTION_MODES:
            raise LeadMarketplaceEngineError(f"Invalid distribution_mode: {distribution_mode}")

        async with get_session() as session:
            lead = await LeadAutomationRepository(session).get_by_id(automation_lead_id)
            if lead is None:
                raise LeadMarketplaceEngineError(f"Lead not found: {automation_lead_id}")
            if lead.is_duplicate:
                raise LeadMarketplaceEngineError("Duplicate leads cannot be listed")

            pricing_repo = LeadMarketplacePricingRuleRepository(session)
            rule = None
            if pricing_rule_code:
                rule = await pricing_repo.get_by_code(tenant_id, pricing_rule_code)
                if rule is None:
                    raise LeadMarketplaceEngineError(f"Pricing rule not found: {pricing_rule_code}")

            quality_score, quality_factors = LeadMarketplaceEngineV1.score_lead_quality(lead)
            if rule is None:
                rule = await pricing_repo.find_for_score(tenant_id, quality_score)

            mode = distribution_mode or (
                rule.default_distribution_mode if rule else MarketplaceDistributionMode.DISTRIBUTION.value
            )
            if mode == MarketplaceDistributionMode.EXCLUSIVE.value and exclusive_buyer_tenant_id is None:
                raise LeadMarketplaceEngineError("exclusive_buyer_tenant_id required for EXCLUSIVE mode")

            base_price = Decimal(str(rule.base_price)) if rule else Decimal("50")
            price_per_point = Decimal(str(rule.price_per_score_point)) if rule else Decimal("0.50")
            auction_premium = Decimal(str(rule.auction_premium_percent)) if rule else Decimal("10")
            exclusive_mult = Decimal(str(rule.exclusive_multiplier)) if rule else Decimal("1.5")
            currency = rule.currency if rule else "USD"

            total_price, pricing_breakdown = LeadMarketplaceEngineV1.calculate_lead_price(
                quality_score=quality_score,
                base_price=base_price,
                price_per_score_point=price_per_point,
                distribution_mode=mode,
                auction_premium_percent=auction_premium,
                exclusive_multiplier=exclusive_mult,
            )

            hours = expires_in_hours
            if hours is None:
                hours = DEFAULT_AUCTION_HOURS if mode == MarketplaceDistributionMode.AUCTION.value else DEFAULT_DISTRIBUTION_HOURS
            expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)

            status = MarketplaceListingStatus.OPEN.value if publish else MarketplaceListingStatus.DRAFT.value
            listing = await LeadMarketplaceListingRepository(session).create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                automation_lead_id=automation_lead_id,
                distribution_mode=mode,
                status=status,
                base_price=total_price,
                reserve_price=Decimal(str(reserve_price)) if reserve_price is not None else None,
                currency=currency,
                quality_score=quality_score,
                quality_factors=quality_factors,
                pricing_breakdown=pricing_breakdown,
                exclusive_buyer_tenant_id=exclusive_buyer_tenant_id,
                expires_at=expires_at,
                notes=notes,
            )

            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="lead_marketplace_listing",
                entity_id=str(listing.id),
                action=AuditAction.CREATE.value,
                new_value={
                    "automation_lead_id": str(automation_lead_id),
                    "distribution_mode": mode,
                    "base_price": str(total_price),
                    "quality_score": quality_score,
                },
            )
            await session.refresh(listing)
            return LeadMarketplaceEngineV1._listing_snapshot(listing)

    @staticmethod
    async def list_listings(
        actor_id: int,
        tenant_id: uuid.UUID | None = None,
        *,
        status: str | None = None,
        distribution_mode: str | None = None,
        marketplace_only: bool = False,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not await LeadMarketplaceEngineV1.user_can_access(actor_id):
            raise LeadMarketplaceEngineError("Lead marketplace access denied")

        async with get_session() as session:
            repo = LeadMarketplaceListingRepository(session)
            if marketplace_only or tenant_id is None:
                rows = await repo.list_open(
                    distribution_mode=distribution_mode,
                    limit=limit,
                )
            else:
                await LeadMarketplaceEngineV1._require_access(actor_id, tenant_id)
                rows = await repo.list_by_tenant(
                    tenant_id,
                    status=status,
                    distribution_mode=distribution_mode,
                    limit=limit,
                )
            return [LeadMarketplaceEngineV1._listing_snapshot(r) for r in rows]

    @staticmethod
    async def distribute_lead(
        actor_id: int,
        tenant_id: uuid.UUID,
        listing_id: uuid.UUID,
        *,
        buyer_tenant_ids: list[uuid.UUID],
    ) -> dict[str, Any]:
        ctx = await LeadMarketplaceEngineV1._require_access(actor_id, tenant_id)
        if not buyer_tenant_ids:
            raise LeadMarketplaceEngineError("buyer_tenant_ids required")

        async with get_session() as session:
            listing = await LeadMarketplaceListingRepository(session).get_by_id(listing_id)
            if listing is None or listing.tenant_id != tenant_id:
                raise LeadMarketplaceEngineError(f"Listing not found: {listing_id}")
            if listing.distribution_mode != MarketplaceDistributionMode.DISTRIBUTION.value:
                raise LeadMarketplaceEngineError("Listing is not in DISTRIBUTION mode")
            if listing.status != MarketplaceListingStatus.OPEN.value:
                raise LeadMarketplaceEngineError(f"Listing is not open: {listing.status}")

            offer_repo = LeadMarketplaceOfferRepository(session)
            offers: list[dict[str, Any]] = []
            for buyer_id in buyer_tenant_ids:
                buyer = await PartnerTenantRepository(session).get_by_id(buyer_id)
                if buyer is None:
                    raise LeadMarketplaceEngineError(f"Buyer tenant not found: {buyer_id}")
                row = await offer_repo.create(
                    listing_id=listing_id,
                    buyer_tenant_id=buyer_id,
                    actor_id=actor_id,
                    offer_type=MarketplaceOfferType.DISTRIBUTION_ACCEPT.value,
                    amount=listing.base_price,
                    status=MarketplaceOfferStatus.PENDING.value,
                    metadata={"distributed_by": str(tenant_id)},
                )
                offers.append(LeadMarketplaceEngineV1._offer_snapshot(row))

            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="lead_marketplace_listing",
                entity_id=str(listing_id),
                action=AuditAction.ASSIGN.value,
                new_value={"buyer_tenant_ids": [str(b) for b in buyer_tenant_ids], "offer_count": len(offers)},
            )
            return {"listing_id": str(listing_id), "offers": offers}

    @staticmethod
    async def accept_distribution(
        actor_id: int,
        buyer_tenant_id: uuid.UUID,
        listing_id: uuid.UUID,
    ) -> dict[str, Any]:
        ctx = await LeadMarketplaceEngineV1._require_access(actor_id, buyer_tenant_id)
        async with get_session() as session:
            listing = await LeadMarketplaceListingRepository(session).get_by_id(listing_id)
            if listing is None:
                raise LeadMarketplaceEngineError(f"Listing not found: {listing_id}")
            if listing.distribution_mode != MarketplaceDistributionMode.DISTRIBUTION.value:
                raise LeadMarketplaceEngineError("Listing is not in DISTRIBUTION mode")
            if listing.status != MarketplaceListingStatus.OPEN.value:
                raise LeadMarketplaceEngineError(f"Listing is not open: {listing.status}")

            offer_repo = LeadMarketplaceOfferRepository(session)
            offers = await offer_repo.list_by_listing(
                listing_id,
                offer_type=MarketplaceOfferType.DISTRIBUTION_ACCEPT.value,
                status=MarketplaceOfferStatus.PENDING.value,
            )
            my_offer = next((o for o in offers if o.buyer_tenant_id == buyer_tenant_id), None)
            if my_offer is None:
                raise LeadMarketplaceEngineError("No pending distribution offer for this tenant")

            my_offer.status = MarketplaceOfferStatus.ACCEPTED.value
            for other in offers:
                if other.id != my_offer.id:
                    other.status = MarketplaceOfferStatus.DECLINED.value

            listing = await LeadMarketplaceListingRepository(session).update_status(
                listing_id,
                status=MarketplaceListingStatus.ASSIGNED.value,
                buyer_tenant_id=buyer_tenant_id,
                final_price=my_offer.amount,
            )

            await PartnerTenantEngineV1.bind_resource(
                actor_id,
                buyer_tenant_id,
                resource_type=TenantResourceType.LEAD.value,
                resource_id=str(listing.automation_lead_id),
                notes=f"marketplace listing {listing_id}",
            )

            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=buyer_tenant_id,
                entity_type="lead_marketplace_listing",
                entity_id=str(listing_id),
                action=AuditAction.STATUS_CHANGE.value,
                new_value={"status": MarketplaceListingStatus.ASSIGNED.value, "final_price": str(my_offer.amount)},
            )
            await session.refresh(listing)
            return LeadMarketplaceEngineV1._listing_snapshot(listing)

    @staticmethod
    async def place_bid(
        actor_id: int,
        buyer_tenant_id: uuid.UUID,
        listing_id: uuid.UUID,
        *,
        amount: Decimal | float | int,
    ) -> dict[str, Any]:
        ctx = await LeadMarketplaceEngineV1._require_access(actor_id, buyer_tenant_id)
        bid_amount = LeadMarketplaceEngineV1._quantize(Decimal(str(amount)))

        async with get_session() as session:
            listing = await LeadMarketplaceListingRepository(session).get_by_id(listing_id)
            if listing is None:
                raise LeadMarketplaceEngineError(f"Listing not found: {listing_id}")
            if listing.distribution_mode != MarketplaceDistributionMode.AUCTION.value:
                raise LeadMarketplaceEngineError("Listing is not in AUCTION mode")
            if listing.status != MarketplaceListingStatus.OPEN.value:
                raise LeadMarketplaceEngineError(f"Listing is not open: {listing.status}")
            if listing.expires_at and listing.expires_at <= datetime.now(timezone.utc):
                raise LeadMarketplaceEngineError("Auction has expired")

            offer_repo = LeadMarketplaceOfferRepository(session)
            highest = await offer_repo.get_highest_bid(listing_id)
            min_bid = listing.base_price
            if highest is not None and highest.amount >= min_bid:
                min_bid = LeadMarketplaceEngineV1._quantize(highest.amount + Decimal("1"))
            if bid_amount < min_bid:
                raise LeadMarketplaceEngineError(f"Bid must be at least {min_bid}")

            row = await offer_repo.create(
                listing_id=listing_id,
                buyer_tenant_id=buyer_tenant_id,
                actor_id=actor_id,
                offer_type=MarketplaceOfferType.BID.value,
                amount=bid_amount,
                status=MarketplaceOfferStatus.WINNING.value,
            )
            await offer_repo.mark_outbid(listing_id, except_offer_id=row.id)

            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=buyer_tenant_id,
                entity_type="lead_marketplace_offer",
                entity_id=str(row.id),
                action=AuditAction.CREATE.value,
                new_value={"listing_id": str(listing_id), "amount": str(bid_amount)},
            )
            await session.refresh(row)
            return LeadMarketplaceEngineV1._offer_snapshot(row)

    @staticmethod
    async def close_auction(
        actor_id: int,
        tenant_id: uuid.UUID,
        listing_id: uuid.UUID,
    ) -> dict[str, Any]:
        ctx = await LeadMarketplaceEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            listing = await LeadMarketplaceListingRepository(session).get_by_id(listing_id)
            if listing is None or listing.tenant_id != tenant_id:
                raise LeadMarketplaceEngineError(f"Listing not found: {listing_id}")
            if listing.distribution_mode != MarketplaceDistributionMode.AUCTION.value:
                raise LeadMarketplaceEngineError("Listing is not in AUCTION mode")
            if listing.status != MarketplaceListingStatus.OPEN.value:
                raise LeadMarketplaceEngineError(f"Listing is not open: {listing.status}")

            offer_repo = LeadMarketplaceOfferRepository(session)
            winning = await offer_repo.get_highest_bid(listing_id)
            if winning is None:
                listing = await LeadMarketplaceListingRepository(session).update_status(
                    listing_id,
                    status=MarketplaceListingStatus.CLOSED.value,
                )
                await session.refresh(listing)
                return LeadMarketplaceEngineV1._listing_snapshot(listing)

            if listing.reserve_price is not None and winning.amount < listing.reserve_price:
                winning.status = MarketplaceOfferStatus.REJECTED.value
                listing = await LeadMarketplaceListingRepository(session).update_status(
                    listing_id,
                    status=MarketplaceListingStatus.CLOSED.value,
                )
            else:
                winning.status = MarketplaceOfferStatus.ACCEPTED.value
                listing = await LeadMarketplaceListingRepository(session).update_status(
                    listing_id,
                    status=MarketplaceListingStatus.ASSIGNED.value,
                    buyer_tenant_id=winning.buyer_tenant_id,
                    final_price=winning.amount,
                )
                await PartnerTenantEngineV1.bind_resource(
                    actor_id,
                    winning.buyer_tenant_id,
                    resource_type=TenantResourceType.LEAD.value,
                    resource_id=str(listing.automation_lead_id),
                    notes=f"auction listing {listing_id}",
                )

            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="lead_marketplace_listing",
                entity_id=str(listing_id),
                action=AuditAction.STATUS_CHANGE.value,
                new_value={
                    "status": listing.status,
                    "winner": str(winning.buyer_tenant_id) if winning.status == MarketplaceOfferStatus.ACCEPTED.value else None,
                    "final_price": str(listing.final_price) if listing.final_price else None,
                },
            )
            await session.refresh(listing)
            return LeadMarketplaceEngineV1._listing_snapshot(listing)

    @staticmethod
    async def purchase_exclusive(
        actor_id: int,
        buyer_tenant_id: uuid.UUID,
        listing_id: uuid.UUID,
    ) -> dict[str, Any]:
        ctx = await LeadMarketplaceEngineV1._require_access(actor_id, buyer_tenant_id)
        async with get_session() as session:
            listing = await LeadMarketplaceListingRepository(session).get_by_id(listing_id)
            if listing is None:
                raise LeadMarketplaceEngineError(f"Listing not found: {listing_id}")
            if listing.distribution_mode != MarketplaceDistributionMode.EXCLUSIVE.value:
                raise LeadMarketplaceEngineError("Listing is not in EXCLUSIVE mode")
            if listing.status != MarketplaceListingStatus.OPEN.value:
                raise LeadMarketplaceEngineError(f"Listing is not open: {listing.status}")
            if (
                listing.exclusive_buyer_tenant_id is not None
                and listing.exclusive_buyer_tenant_id != buyer_tenant_id
            ):
                raise LeadMarketplaceEngineError("This exclusive lead is reserved for another tenant")

            offer = await LeadMarketplaceOfferRepository(session).create(
                listing_id=listing_id,
                buyer_tenant_id=buyer_tenant_id,
                actor_id=actor_id,
                offer_type=MarketplaceOfferType.EXCLUSIVE_PURCHASE.value,
                amount=listing.base_price,
                status=MarketplaceOfferStatus.ACCEPTED.value,
            )

            listing = await LeadMarketplaceListingRepository(session).update_status(
                listing_id,
                status=MarketplaceListingStatus.ASSIGNED.value,
                buyer_tenant_id=buyer_tenant_id,
                final_price=listing.base_price,
            )

            await PartnerTenantEngineV1.bind_resource(
                actor_id,
                buyer_tenant_id,
                resource_type=TenantResourceType.LEAD.value,
                resource_id=str(listing.automation_lead_id),
                notes=f"exclusive listing {listing_id}",
            )

            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=buyer_tenant_id,
                entity_type="lead_marketplace_listing",
                entity_id=str(listing_id),
                action=AuditAction.STATUS_CHANGE.value,
                new_value={"status": MarketplaceListingStatus.ASSIGNED.value, "offer_id": str(offer.id)},
            )
            await session.refresh(listing)
            return LeadMarketplaceEngineV1._listing_snapshot(listing)

    @staticmethod
    async def list_offers(
        actor_id: int,
        tenant_id: uuid.UUID,
        listing_id: uuid.UUID,
        *,
        offer_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        await LeadMarketplaceEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            listing = await LeadMarketplaceListingRepository(session).get_by_id(listing_id)
            if listing is None:
                raise LeadMarketplaceEngineError(f"Listing not found: {listing_id}")

            rows = await LeadMarketplaceOfferRepository(session).list_by_listing(
                listing_id, offer_type=offer_type, limit=limit
            )
            return [LeadMarketplaceEngineV1._offer_snapshot(r) for r in rows]

    @staticmethod
    async def get_lead_pricing(
        actor_id: int,
        tenant_id: uuid.UUID,
        automation_lead_id: uuid.UUID,
        *,
        distribution_mode: str = MarketplaceDistributionMode.DISTRIBUTION.value,
        pricing_rule_code: str | None = None,
    ) -> dict[str, Any]:
        await LeadMarketplaceEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            lead = await LeadAutomationRepository(session).get_by_id(automation_lead_id)
            if lead is None:
                raise LeadMarketplaceEngineError(f"Lead not found: {automation_lead_id}")

            pricing_repo = LeadMarketplacePricingRuleRepository(session)
            rule = None
            if pricing_rule_code:
                rule = await pricing_repo.get_by_code(tenant_id, pricing_rule_code)

            quality_score, quality_factors = LeadMarketplaceEngineV1.score_lead_quality(lead)
            if rule is None:
                rule = await pricing_repo.find_for_score(tenant_id, quality_score)

            base_price = Decimal(str(rule.base_price)) if rule else Decimal("50")
            price_per_point = Decimal(str(rule.price_per_score_point)) if rule else Decimal("0.50")
            auction_premium = Decimal(str(rule.auction_premium_percent)) if rule else Decimal("10")
            exclusive_mult = Decimal(str(rule.exclusive_multiplier)) if rule else Decimal("1.5")

            total_price, pricing_breakdown = LeadMarketplaceEngineV1.calculate_lead_price(
                quality_score=quality_score,
                base_price=base_price,
                price_per_score_point=price_per_point,
                distribution_mode=distribution_mode,
                auction_premium_percent=auction_premium,
                exclusive_multiplier=exclusive_mult,
            )

            return {
                "automation_lead_id": str(automation_lead_id),
                "quality_score": quality_score,
                "quality_factors": quality_factors,
                "distribution_mode": distribution_mode,
                "price": str(total_price),
                "pricing_breakdown": pricing_breakdown,
                "pricing_rule_code": rule.code if rule else None,
                "currency": rule.currency if rule else "USD",
            }

    @staticmethod
    async def list_distribution_modes() -> list[dict[str, str]]:
        return [
            {"code": m.value, "label": m.value.replace("_", " ").title()}
            for m in MarketplaceDistributionMode
        ]
