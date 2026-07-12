# OTC Matching Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.otc_matching import (
    OtcExecutionRoute,
    OtcFillHistory,
    OtcMatch,
    OtcMatchStatus,
    OtcOrder,
    OtcOrderStatus,
    OtcOrderType,
    OtcExecutionMode,
    OtcMatchingStrategy,
    OtcQuote,
    OtcQuoteStatus,
    OtcRouteStatus,
)


class OtcOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        order_type: str,
        asset: str,
        quote_asset: str,
        amount: Decimal,
        execution_mode: str = OtcExecutionMode.MANUAL.value,
        matching_strategy: str = OtcMatchingStrategy.BEST_PRICE.value,
        deal_id: uuid.UUID | None = None,
        partner_id: uuid.UUID | None = None,
        created_by: int | None = None,
        price_limit: Decimal | None = None,
        notes: str | None = None,
        **extra: Any,
    ) -> OtcOrder:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if order_type not in {t.value for t in OtcOrderType}:
            raise ValueError(f"Invalid order_type: {order_type}")
        if amount <= 0:
            raise ValueError("amount must be positive")

        order = OtcOrder(
            deal_id=deal_id,
            partner_id=partner_id,
            created_by=created_by,
            order_type=order_type,
            asset=asset,
            quote_asset=quote_asset,
            amount=amount,
            filled_amount=Decimal("0"),
            remaining_amount=amount,
            price_limit=price_limit,
            execution_mode=execution_mode,
            matching_strategy=matching_strategy,
            notes=notes,
        )
        self._session.add(order)
        await self._session.flush()
        return order

    async def get_by_id(self, order_id: uuid.UUID) -> OtcOrder | None:
        result = await self._session.execute(
            select(OtcOrder).where(OtcOrder.id == order_id)
        )
        return result.scalar_one_or_none()

    async def apply_fill(
        self,
        order_id: uuid.UUID,
        fill_amount: Decimal,
    ) -> OtcOrder | None:
        order = await self.get_by_id(order_id)
        if order is None:
            return None
        order.filled_amount += fill_amount
        order.remaining_amount = max(Decimal("0"), order.amount - order.filled_amount)
        if order.remaining_amount == 0:
            order.status = OtcOrderStatus.FILLED.value
        elif order.filled_amount > 0:
            order.status = OtcOrderStatus.PARTIALLY_FILLED.value
        await self._session.flush()
        return order

    async def update_status(self, order_id: uuid.UUID, status: str) -> OtcOrder | None:
        order = await self.get_by_id(order_id)
        if order is None:
            return None
        order.status = status
        await self._session.flush()
        return order


class OtcQuoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        order_id: uuid.UUID,
        partner_id: uuid.UUID,
        price: Decimal,
        amount: Decimal,
        expires_at: datetime | None = None,
        **extra: Any,
    ) -> OtcQuote:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if price <= 0 or amount <= 0:
            raise ValueError("price and amount must be positive")

        quote = OtcQuote(
            order_id=order_id,
            partner_id=partner_id,
            price=price,
            amount=amount,
            available_amount=amount,
            expires_at=expires_at,
        )
        self._session.add(quote)
        await self._session.flush()
        return quote

    async def get_by_id(self, quote_id: uuid.UUID) -> OtcQuote | None:
        result = await self._session.execute(
            select(OtcQuote).where(OtcQuote.id == quote_id)
        )
        return result.scalar_one_or_none()

    async def list_active_for_order(self, order_id: uuid.UUID) -> list[OtcQuote]:
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            select(OtcQuote)
            .where(
                OtcQuote.order_id == order_id,
                OtcQuote.status == OtcQuoteStatus.ACTIVE.value,
                OtcQuote.available_amount > 0,
            )
            .order_by(OtcQuote.received_at.asc())
        )
        quotes = list(result.scalars().all())
        active: list[OtcQuote] = []
        for quote in quotes:
            if quote.expires_at is not None and quote.expires_at < now:
                quote.status = OtcQuoteStatus.EXPIRED.value
                continue
            active.append(quote)
        if len(active) != len(quotes):
            await self._session.flush()
        return active

    async def consume_amount(
        self,
        quote_id: uuid.UUID,
        amount: Decimal,
    ) -> OtcQuote | None:
        quote = await self.get_by_id(quote_id)
        if quote is None:
            return None
        quote.available_amount = max(Decimal("0"), quote.available_amount - amount)
        if quote.available_amount == 0:
            quote.status = OtcQuoteStatus.FILLED.value
        await self._session.flush()
        return quote


class OtcMatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        order_id: uuid.UUID,
        quote_id: uuid.UUID,
        partner_id: uuid.UUID,
        matched_amount: Decimal,
        matched_price: Decimal,
        requires_approval: bool = True,
        **extra: Any,
    ) -> OtcMatch:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        match = OtcMatch(
            order_id=order_id,
            quote_id=quote_id,
            partner_id=partner_id,
            matched_amount=matched_amount,
            matched_price=matched_price,
            requires_approval=requires_approval,
        )
        self._session.add(match)
        await self._session.flush()
        return match

    async def get_by_id(self, match_id: uuid.UUID) -> OtcMatch | None:
        result = await self._session.execute(
            select(OtcMatch).where(OtcMatch.id == match_id)
        )
        return result.scalar_one_or_none()

    async def list_by_order(self, order_id: uuid.UUID) -> list[OtcMatch]:
        result = await self._session.execute(
            select(OtcMatch)
            .where(OtcMatch.order_id == order_id)
            .order_by(OtcMatch.created_at.asc())
        )
        return list(result.scalars().all())

    async def update_status(self, match_id: uuid.UUID, status: str) -> OtcMatch | None:
        match = await self.get_by_id(match_id)
        if match is None:
            return None
        match.status = status
        await self._session.flush()
        return match

    async def approve(
        self,
        match_id: uuid.UUID,
        *,
        approved_by: int,
    ) -> OtcMatch | None:
        match = await self.get_by_id(match_id)
        if match is None:
            return None
        match.status = OtcMatchStatus.APPROVED.value
        match.approved_by = approved_by
        match.approved_at = datetime.now(timezone.utc)
        await self._session.flush()
        return match


class OtcExecutionRouteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        order_id: uuid.UUID,
        partner_id: uuid.UUID,
        step_order: int,
        amount: Decimal,
        price: Decimal,
        match_id: uuid.UUID | None = None,
        liquidity_score: Decimal | None = None,
        risk_score: int | None = None,
        metadata_json: dict | None = None,
        **extra: Any,
    ) -> OtcExecutionRoute:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        route = OtcExecutionRoute(
            order_id=order_id,
            match_id=match_id,
            partner_id=partner_id,
            step_order=step_order,
            amount=amount,
            price=price,
            liquidity_score=liquidity_score,
            risk_score=risk_score,
            metadata_json=metadata_json,
        )
        self._session.add(route)
        await self._session.flush()
        return route

    async def list_by_order(self, order_id: uuid.UUID) -> list[OtcExecutionRoute]:
        result = await self._session.execute(
            select(OtcExecutionRoute)
            .where(OtcExecutionRoute.order_id == order_id)
            .order_by(OtcExecutionRoute.step_order.asc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        route_id: uuid.UUID,
        status: str,
    ) -> OtcExecutionRoute | None:
        result = await self._session.execute(
            select(OtcExecutionRoute).where(OtcExecutionRoute.id == route_id)
        )
        route = result.scalar_one_or_none()
        if route is None:
            return None
        route.status = status
        await self._session.flush()
        return route


class OtcFillHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        order_id: uuid.UUID,
        partner_id: uuid.UUID,
        fill_amount: Decimal,
        fill_price: Decimal,
        match_id: uuid.UUID | None = None,
        route_id: uuid.UUID | None = None,
        **extra: Any,
    ) -> OtcFillHistory:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        fill = OtcFillHistory(
            order_id=order_id,
            match_id=match_id,
            route_id=route_id,
            partner_id=partner_id,
            fill_amount=fill_amount,
            fill_price=fill_price,
        )
        self._session.add(fill)
        await self._session.flush()
        return fill

    async def list_by_order(self, order_id: uuid.UUID) -> list[OtcFillHistory]:
        result = await self._session.execute(
            select(OtcFillHistory)
            .where(OtcFillHistory.order_id == order_id)
            .order_by(OtcFillHistory.filled_at.asc())
        )
        return list(result.scalars().all())
