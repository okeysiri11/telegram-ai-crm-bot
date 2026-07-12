# Pricing Engine repository — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.pricing import (
    Markup,
    MarkupAppliesTo,
    MarkupType,
    PricingRule,
    PricingRuleType,
    PricingSource,
    PricingSourceType,
    Spread,
    SpreadType,
)


class PricingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_source(
        self,
        *,
        code: str,
        name: str,
        source_type: str,
        asset_in: str,
        asset_out: str,
        base_rate: Decimal,
        is_active: bool = True,
        metadata: dict[str, Any] | None = None,
        **extra: Any,
    ) -> PricingSource:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if source_type not in {t.value for t in PricingSourceType}:
            raise ValueError(f"Invalid source_type: {source_type}")
        if base_rate <= 0:
            raise ValueError("base_rate must be positive")

        source = PricingSource(
            code=code,
            name=name,
            source_type=source_type,
            asset_in=asset_in,
            asset_out=asset_out,
            base_rate=base_rate,
            is_active=is_active,
            last_fetched_at=datetime.now(timezone.utc),
            metadata_=metadata,
        )
        self._session.add(source)
        await self._session.flush()
        return source

    async def get_source(self, source_id: uuid.UUID) -> PricingSource | None:
        result = await self._session.execute(
            select(PricingSource).where(PricingSource.id == source_id)
        )
        return result.scalar_one_or_none()

    async def get_source_by_code(self, code: str) -> PricingSource | None:
        result = await self._session.execute(
            select(PricingSource).where(PricingSource.code == code)
        )
        return result.scalar_one_or_none()

    async def update_source_rate(
        self,
        source_id: uuid.UUID,
        base_rate: Decimal,
    ) -> PricingSource | None:
        source = await self.get_source(source_id)
        if source is None:
            return None
        if base_rate <= 0:
            raise ValueError("base_rate must be positive")

        source.base_rate = base_rate
        source.last_fetched_at = datetime.now(timezone.utc)
        await self._session.flush()
        return source

    async def get_active_source_for_pair(
        self,
        asset_in: str,
        asset_out: str,
    ) -> PricingSource | None:
        result = await self._session.execute(
            select(PricingSource)
            .where(
                PricingSource.asset_in == asset_in,
                PricingSource.asset_out == asset_out,
                PricingSource.is_active.is_(True),
            )
            .order_by(PricingSource.last_fetched_at.desc().nullslast())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_rule(
        self,
        *,
        code: str,
        name: str,
        rule_type: str,
        asset_in: str,
        asset_out: str,
        source_id: uuid.UUID | None = None,
        partner_id: int | None = None,
        manager_id: int | None = None,
        vip_user_id: int | None = None,
        priority: int = 100,
        conditions: dict[str, Any] | None = None,
        description: str | None = None,
        **extra: Any,
    ) -> PricingRule:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if rule_type not in {t.value for t in PricingRuleType}:
            raise ValueError(f"Invalid rule_type: {rule_type}")

        rule = PricingRule(
            code=code,
            name=name,
            rule_type=rule_type,
            asset_in=asset_in,
            asset_out=asset_out,
            source_id=source_id,
            partner_id=partner_id,
            manager_id=manager_id,
            vip_user_id=vip_user_id,
            priority=priority,
            conditions=conditions,
            description=description,
        )
        self._session.add(rule)
        await self._session.flush()
        return rule

    async def get_rule(self, rule_id: uuid.UUID) -> PricingRule | None:
        result = await self._session.execute(
            select(PricingRule).where(PricingRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def find_rule(
        self,
        *,
        rule_type: str,
        asset_in: str,
        asset_out: str,
        partner_id: int | None = None,
        manager_id: int | None = None,
        vip_user_id: int | None = None,
    ) -> PricingRule | None:
        stmt = (
            select(PricingRule)
            .where(
                PricingRule.rule_type == rule_type,
                PricingRule.asset_in == asset_in,
                PricingRule.asset_out == asset_out,
                PricingRule.is_active.is_(True),
            )
            .order_by(PricingRule.priority.asc())
        )
        if partner_id is not None:
            stmt = stmt.where(PricingRule.partner_id == partner_id)
        if manager_id is not None:
            stmt = stmt.where(PricingRule.manager_id == manager_id)
        if vip_user_id is not None:
            stmt = stmt.where(PricingRule.vip_user_id == vip_user_id)

        result = await self._session.execute(stmt.limit(1))
        return result.scalar_one_or_none()

    async def create_spread(
        self,
        *,
        asset_in: str,
        asset_out: str,
        spread_type: str,
        bid_spread: Decimal,
        ask_spread: Decimal,
        rule_id: uuid.UUID | None = None,
        source_id: uuid.UUID | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        **extra: Any,
    ) -> Spread:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if spread_type not in {t.value for t in SpreadType}:
            raise ValueError(f"Invalid spread_type: {spread_type}")

        spread = Spread(
            rule_id=rule_id,
            source_id=source_id,
            asset_in=asset_in,
            asset_out=asset_out,
            spread_type=spread_type,
            bid_spread=bid_spread,
            ask_spread=ask_spread,
            min_amount=min_amount,
            max_amount=max_amount,
        )
        self._session.add(spread)
        await self._session.flush()
        return spread

    async def get_spread_for_rule(
        self,
        rule_id: uuid.UUID,
        *,
        amount: Decimal | None = None,
    ) -> Spread | None:
        stmt = (
            select(Spread)
            .where(
                Spread.rule_id == rule_id,
                Spread.is_active.is_(True),
            )
            .order_by(Spread.created_at.desc())
        )
        result = await self._session.execute(stmt)
        spreads = list(result.scalars().all())
        if amount is None:
            return spreads[0] if spreads else None

        for spread in spreads:
            if spread.min_amount is not None and amount < spread.min_amount:
                continue
            if spread.max_amount is not None and amount > spread.max_amount:
                continue
            return spread
        return spreads[0] if spreads else None

    async def get_default_spread(
        self,
        asset_in: str,
        asset_out: str,
        *,
        amount: Decimal | None = None,
    ) -> Spread | None:
        stmt = (
            select(Spread)
            .where(
                Spread.asset_in == asset_in,
                Spread.asset_out == asset_out,
                Spread.rule_id.is_(None),
                Spread.is_active.is_(True),
            )
            .order_by(Spread.created_at.desc())
        )
        result = await self._session.execute(stmt)
        spreads = list(result.scalars().all())
        if amount is None:
            return spreads[0] if spreads else None

        for spread in spreads:
            if spread.min_amount is not None and amount < spread.min_amount:
                continue
            if spread.max_amount is not None and amount > spread.max_amount:
                continue
            return spread
        return spreads[0] if spreads else None

    async def create_markup(
        self,
        *,
        applies_to: str,
        markup_type: str,
        value: Decimal,
        rule_id: uuid.UUID | None = None,
        target_id: int | None = None,
        asset_in: str | None = None,
        asset_out: str | None = None,
        priority: int = 100,
        description: str | None = None,
        **extra: Any,
    ) -> Markup:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if applies_to not in {a.value for a in MarkupAppliesTo}:
            raise ValueError(f"Invalid applies_to: {applies_to}")
        if markup_type not in {t.value for t in MarkupType}:
            raise ValueError(f"Invalid markup_type: {markup_type}")

        markup = Markup(
            rule_id=rule_id,
            applies_to=applies_to,
            target_id=target_id,
            markup_type=markup_type,
            value=value,
            asset_in=asset_in,
            asset_out=asset_out,
            priority=priority,
            description=description,
        )
        self._session.add(markup)
        await self._session.flush()
        return markup

    async def list_markups_for_rule(self, rule_id: uuid.UUID) -> list[Markup]:
        result = await self._session.execute(
            select(Markup)
            .where(
                Markup.rule_id == rule_id,
                Markup.is_active.is_(True),
            )
            .order_by(Markup.priority.asc())
        )
        return list(result.scalars().all())

    async def list_markups_for_target(
        self,
        applies_to: str,
        target_id: int | None = None,
        *,
        asset_in: str | None = None,
        asset_out: str | None = None,
    ) -> list[Markup]:
        stmt = (
            select(Markup)
            .where(
                Markup.applies_to == applies_to,
                Markup.is_active.is_(True),
            )
            .order_by(Markup.priority.asc())
        )
        if target_id is not None:
            stmt = stmt.where(Markup.target_id == target_id)
        if asset_in is not None:
            stmt = stmt.where(
                (Markup.asset_in.is_(None)) | (Markup.asset_in == asset_in)
            )
        if asset_out is not None:
            stmt = stmt.where(
                (Markup.asset_out.is_(None)) | (Markup.asset_out == asset_out)
            )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())
