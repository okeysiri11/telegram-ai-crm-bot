# Lead Marketplace Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.lead_marketplace_engine import (
    MARKETPLACE_DISTRIBUTION_MODES,
    MARKETPLACE_LISTING_STATUSES,
    MARKETPLACE_OFFER_STATUSES,
    MARKETPLACE_OFFER_TYPES,
    LeadMarketplaceListing,
    LeadMarketplaceOffer,
    LeadMarketplacePricingRule,
    MarketplaceListingStatus,
    MarketplaceOfferStatus,
)


class LeadMarketplaceListingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        automation_lead_id: uuid.UUID,
        distribution_mode: str,
        base_price: Decimal,
        quality_score: int,
        quality_factors: dict,
        pricing_breakdown: dict,
        currency: str = "USD",
        reserve_price: Decimal | None = None,
        exclusive_buyer_tenant_id: uuid.UUID | None = None,
        expires_at: datetime | None = None,
        status: str = MarketplaceListingStatus.DRAFT.value,
        notes: str | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> LeadMarketplaceListing:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if distribution_mode not in MARKETPLACE_DISTRIBUTION_MODES:
            raise ValueError(f"Invalid distribution_mode: {distribution_mode}")
        if status not in MARKETPLACE_LISTING_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        row = LeadMarketplaceListing(
            tenant_id=tenant_id,
            company_id=company_id,
            automation_lead_id=automation_lead_id,
            distribution_mode=distribution_mode,
            status=status,
            base_price=base_price,
            reserve_price=reserve_price,
            currency=currency,
            quality_score=quality_score,
            quality_factors=quality_factors,
            pricing_breakdown=pricing_breakdown,
            exclusive_buyer_tenant_id=exclusive_buyer_tenant_id,
            expires_at=expires_at,
            notes=notes,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, listing_id: uuid.UUID) -> LeadMarketplaceListing | None:
        result = await self._session.execute(
            select(LeadMarketplaceListing).where(LeadMarketplaceListing.id == listing_id)
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        status: str | None = None,
        distribution_mode: str | None = None,
        limit: int = 100,
    ) -> list[LeadMarketplaceListing]:
        stmt = (
            select(LeadMarketplaceListing)
            .where(LeadMarketplaceListing.tenant_id == tenant_id)
            .order_by(LeadMarketplaceListing.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            stmt = stmt.where(LeadMarketplaceListing.status == status)
        if distribution_mode is not None:
            stmt = stmt.where(LeadMarketplaceListing.distribution_mode == distribution_mode)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_open(
        self,
        *,
        distribution_mode: str | None = None,
        min_quality_score: int | None = None,
        limit: int = 100,
    ) -> list[LeadMarketplaceListing]:
        stmt = (
            select(LeadMarketplaceListing)
            .where(LeadMarketplaceListing.status == MarketplaceListingStatus.OPEN.value)
            .order_by(LeadMarketplaceListing.quality_score.desc(), LeadMarketplaceListing.created_at.desc())
            .limit(limit)
        )
        if distribution_mode is not None:
            stmt = stmt.where(LeadMarketplaceListing.distribution_mode == distribution_mode)
        if min_quality_score is not None:
            stmt = stmt.where(LeadMarketplaceListing.quality_score >= min_quality_score)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        listing_id: uuid.UUID,
        *,
        status: str,
        buyer_tenant_id: uuid.UUID | None = None,
        final_price: Decimal | None = None,
    ) -> LeadMarketplaceListing | None:
        row = await self.get_by_id(listing_id)
        if row is None:
            return None
        row.status = status
        if buyer_tenant_id is not None:
            row.buyer_tenant_id = buyer_tenant_id
        if final_price is not None:
            row.final_price = final_price
        await self._session.flush()
        return row


class LeadMarketplaceOfferRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        listing_id: uuid.UUID,
        buyer_tenant_id: uuid.UUID,
        actor_id: int,
        offer_type: str,
        amount: Decimal,
        status: str = MarketplaceOfferStatus.PENDING.value,
        metadata: dict | None = None,
        **extra: Any,
    ) -> LeadMarketplaceOffer:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if offer_type not in MARKETPLACE_OFFER_TYPES:
            raise ValueError(f"Invalid offer_type: {offer_type}")
        if status not in MARKETPLACE_OFFER_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        row = LeadMarketplaceOffer(
            listing_id=listing_id,
            buyer_tenant_id=buyer_tenant_id,
            actor_id=actor_id,
            offer_type=offer_type,
            amount=amount,
            status=status,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, offer_id: uuid.UUID) -> LeadMarketplaceOffer | None:
        result = await self._session.execute(
            select(LeadMarketplaceOffer).where(LeadMarketplaceOffer.id == offer_id)
        )
        return result.scalar_one_or_none()

    async def list_by_listing(
        self,
        listing_id: uuid.UUID,
        *,
        offer_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[LeadMarketplaceOffer]:
        stmt = (
            select(LeadMarketplaceOffer)
            .where(LeadMarketplaceOffer.listing_id == listing_id)
            .order_by(LeadMarketplaceOffer.amount.desc(), LeadMarketplaceOffer.created_at.desc())
            .limit(limit)
        )
        if offer_type is not None:
            stmt = stmt.where(LeadMarketplaceOffer.offer_type == offer_type)
        if status is not None:
            stmt = stmt.where(LeadMarketplaceOffer.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_highest_bid(self, listing_id: uuid.UUID) -> LeadMarketplaceOffer | None:
        result = await self._session.execute(
            select(LeadMarketplaceOffer)
            .where(
                LeadMarketplaceOffer.listing_id == listing_id,
                LeadMarketplaceOffer.offer_type == "BID",
                LeadMarketplaceOffer.status.in_([
                    MarketplaceOfferStatus.PENDING.value,
                    MarketplaceOfferStatus.WINNING.value,
                ]),
            )
            .order_by(LeadMarketplaceOffer.amount.desc(), LeadMarketplaceOffer.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def mark_outbid(self, listing_id: uuid.UUID, *, except_offer_id: uuid.UUID) -> None:
        await self._session.execute(
            update(LeadMarketplaceOffer)
            .where(
                LeadMarketplaceOffer.listing_id == listing_id,
                LeadMarketplaceOffer.offer_type == "BID",
                LeadMarketplaceOffer.id != except_offer_id,
                LeadMarketplaceOffer.status.in_([
                    MarketplaceOfferStatus.PENDING.value,
                    MarketplaceOfferStatus.WINNING.value,
                ]),
            )
            .values(status=MarketplaceOfferStatus.OUTBID.value)
        )

    async def count_by_listing(self, listing_id: uuid.UUID, *, offer_type: str | None = None) -> int:
        stmt = (
            select(func.count())
            .select_from(LeadMarketplaceOffer)
            .where(LeadMarketplaceOffer.listing_id == listing_id)
        )
        if offer_type is not None:
            stmt = stmt.where(LeadMarketplaceOffer.offer_type == offer_type)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())


class LeadMarketplacePricingRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        code: str,
        name: str,
        base_price: Decimal,
        price_per_score_point: Decimal = Decimal("0"),
        min_quality_score: int = 0,
        max_quality_score: int = 100,
        auction_premium_percent: Decimal = Decimal("0"),
        exclusive_multiplier: Decimal = Decimal("1.5"),
        default_distribution_mode: str = "DISTRIBUTION",
        currency: str = "USD",
        is_active: bool = True,
        metadata: dict | None = None,
        **extra: Any,
    ) -> LeadMarketplacePricingRule:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if default_distribution_mode not in MARKETPLACE_DISTRIBUTION_MODES:
            raise ValueError(f"Invalid default_distribution_mode: {default_distribution_mode}")

        row = LeadMarketplacePricingRule(
            tenant_id=tenant_id,
            company_id=company_id,
            code=code.strip().upper(),
            name=name.strip(),
            base_price=base_price,
            price_per_score_point=price_per_score_point,
            min_quality_score=min_quality_score,
            max_quality_score=max_quality_score,
            auction_premium_percent=auction_premium_percent,
            exclusive_multiplier=exclusive_multiplier,
            default_distribution_mode=default_distribution_mode,
            currency=currency,
            is_active=is_active,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_code(
        self,
        tenant_id: uuid.UUID,
        code: str,
    ) -> LeadMarketplacePricingRule | None:
        result = await self._session.execute(
            select(LeadMarketplacePricingRule).where(
                LeadMarketplacePricingRule.tenant_id == tenant_id,
                LeadMarketplacePricingRule.code == code.strip().upper(),
            )
        )
        return result.scalar_one_or_none()

    async def find_for_score(
        self,
        tenant_id: uuid.UUID,
        quality_score: int,
    ) -> LeadMarketplacePricingRule | None:
        result = await self._session.execute(
            select(LeadMarketplacePricingRule)
            .where(
                LeadMarketplacePricingRule.tenant_id == tenant_id,
                LeadMarketplacePricingRule.is_active.is_(True),
                LeadMarketplacePricingRule.min_quality_score <= quality_score,
                LeadMarketplacePricingRule.max_quality_score >= quality_score,
            )
            .order_by(LeadMarketplacePricingRule.base_price.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        active_only: bool = True,
        limit: int = 100,
    ) -> list[LeadMarketplacePricingRule]:
        stmt = (
            select(LeadMarketplacePricingRule)
            .where(LeadMarketplacePricingRule.tenant_id == tenant_id)
            .order_by(LeadMarketplacePricingRule.code.asc())
            .limit(limit)
        )
        if active_only:
            stmt = stmt.where(LeadMarketplacePricingRule.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
