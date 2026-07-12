# Pricing Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.pricing_v1 import (
    ManagerPricing,
    PartnerPricing,
    PriceSource,
    PriceSourceName,
    SpreadRule,
    SpreadRuleType,
)


class PriceSourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        source_name: str,
        asset: str,
        bid_price: Decimal,
        ask_price: Decimal,
        **extra: Any,
    ) -> PriceSource:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if source_name not in {s.value for s in PriceSourceName}:
            raise ValueError(f"Invalid source_name: {source_name}")
        if bid_price <= 0 or ask_price <= 0:
            raise ValueError("bid_price and ask_price must be positive")

        source = PriceSource(
            source_name=source_name,
            asset=asset,
            bid_price=bid_price,
            ask_price=ask_price,
            updated_at=datetime.now(timezone.utc),
        )
        self._session.add(source)
        await self._session.flush()
        return source

    async def get_by_id(self, source_id: uuid.UUID) -> PriceSource | None:
        result = await self._session.execute(
            select(PriceSource).where(PriceSource.id == source_id)
        )
        return result.scalar_one_or_none()

    async def get_best_for_asset(self, asset: str) -> PriceSource | None:
        result = await self._session.execute(
            select(PriceSource)
            .where(PriceSource.asset == asset)
            .order_by(PriceSource.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        source_name: str,
        asset: str,
        bid_price: Decimal,
        ask_price: Decimal,
    ) -> PriceSource:
        result = await self._session.execute(
            select(PriceSource).where(
                PriceSource.source_name == source_name,
                PriceSource.asset == asset,
            )
        )
        source = result.scalar_one_or_none()
        if source is None:
            return await self.create(
                source_name=source_name,
                asset=asset,
                bid_price=bid_price,
                ask_price=ask_price,
            )

        source.bid_price = bid_price
        source.ask_price = ask_price
        source.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return source


class SpreadRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        asset: str,
        spread_type: str,
        value: Decimal,
        priority: int = 100,
        **extra: Any,
    ) -> SpreadRule:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if spread_type not in {t.value for t in SpreadRuleType}:
            raise ValueError(f"Invalid spread_type: {spread_type}")
        if value < 0:
            raise ValueError("value must be non-negative")

        rule = SpreadRule(
            asset=asset,
            spread_type=spread_type,
            value=value,
            priority=priority,
        )
        self._session.add(rule)
        await self._session.flush()
        return rule

    async def get_by_id(self, rule_id: uuid.UUID) -> SpreadRule | None:
        result = await self._session.execute(
            select(SpreadRule).where(SpreadRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def get_best_for_asset(self, asset: str) -> SpreadRule | None:
        result = await self._session.execute(
            select(SpreadRule)
            .where(SpreadRule.asset == asset)
            .order_by(SpreadRule.priority.asc(), SpreadRule.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_asset(self, asset: str) -> list[SpreadRule]:
        result = await self._session.execute(
            select(SpreadRule)
            .where(SpreadRule.asset == asset)
            .order_by(SpreadRule.priority.asc())
        )
        return list(result.scalars().all())

    async def update_value(self, rule_id: uuid.UUID, value: Decimal) -> SpreadRule | None:
        rule = await self.get_by_id(rule_id)
        if rule is None:
            return None
        if value < 0:
            raise ValueError("value must be non-negative")
        rule.value = value
        await self._session.flush()
        return rule


class PartnerPricingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        partner_id: uuid.UUID,
        asset: str,
        custom_spread: Decimal,
    ) -> PartnerPricing:
        if custom_spread < 0:
            raise ValueError("custom_spread must be non-negative")

        result = await self._session.execute(
            select(PartnerPricing).where(
                PartnerPricing.partner_id == partner_id,
                PartnerPricing.asset == asset,
            )
        )
        pricing = result.scalar_one_or_none()
        if pricing is None:
            pricing = PartnerPricing(
                partner_id=partner_id,
                asset=asset,
                custom_spread=custom_spread,
            )
            self._session.add(pricing)
        else:
            pricing.custom_spread = custom_spread
        await self._session.flush()
        return pricing

    async def get_for_partner(
        self,
        partner_id: uuid.UUID,
        asset: str,
    ) -> PartnerPricing | None:
        result = await self._session.execute(
            select(PartnerPricing).where(
                PartnerPricing.partner_id == partner_id,
                PartnerPricing.asset == asset,
            )
        )
        return result.scalar_one_or_none()


class ManagerPricingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        manager_id: uuid.UUID,
        asset: str,
        custom_margin: Decimal,
    ) -> ManagerPricing:
        if custom_margin < 0:
            raise ValueError("custom_margin must be non-negative")

        result = await self._session.execute(
            select(ManagerPricing).where(
                ManagerPricing.manager_id == manager_id,
                ManagerPricing.asset == asset,
            )
        )
        pricing = result.scalar_one_or_none()
        if pricing is None:
            pricing = ManagerPricing(
                manager_id=manager_id,
                asset=asset,
                custom_margin=custom_margin,
            )
            self._session.add(pricing)
        else:
            pricing.custom_margin = custom_margin
        await self._session.flush()
        return pricing

    async def get_for_manager(
        self,
        manager_id: uuid.UUID,
        asset: str,
    ) -> ManagerPricing | None:
        result = await self._session.execute(
            select(ManagerPricing).where(
                ManagerPricing.manager_id == manager_id,
                ManagerPricing.asset == asset,
            )
        )
        return result.scalar_one_or_none()
