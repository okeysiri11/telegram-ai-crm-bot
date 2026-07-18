# Liquidity Engine v1 — monitoring, allocation, and alerts.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from config import LIQUIDITY_LOW_THRESHOLD, LIQUIDITY_POOL_LIMIT_RATIO, OWNER_ID
from database.models.liquidity import (
    LiquidityAlert,
    LiquidityAlertType,
    LiquidityPool,
    LiquidityReservation,
    LiquidityReservationStatus,
)
from database.session import get_session
from repositories.deal_repository import DealRepository
from repositories.liquidity_repository import (
    LiquidityAlertRepository,
    LiquidityPoolRepository,
    LiquidityReservationRepository,
)
from repositories.user_role_repository import UserRoleRepository

LIQUIDITY_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
LOW_LIQUIDITY_THRESHOLD = Decimal(LIQUIDITY_LOW_THRESHOLD)
POOL_LIMIT_RATIO = Decimal(LIQUIDITY_POOL_LIMIT_RATIO)


class LiquidityEngineError(Exception):
    pass


class InsufficientLiquidityError(LiquidityEngineError):
    pass


class LiquidityEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in LIQUIDITY_ROLES for role in roles)

    @staticmethod
    async def _publish_event(
        event_type: str,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> None:
        try:
            from events.crm_publisher import publish_crm_event

            await publish_crm_event(
                event_type,
                aggregate_type,
                aggregate_id,
                payload,
            )
        except Exception:
            pass

    @staticmethod
    async def _create_alert(
        session,
        *,
        alert_type: str,
        message: str,
        pool_id: uuid.UUID | None = None,
        asset: str | None = None,
        deal_id: uuid.UUID | None = None,
    ) -> LiquidityAlert:
        return await LiquidityAlertRepository(session).create(
            alert_type=alert_type,
            message=message,
            pool_id=pool_id,
            asset=asset,
            deal_id=deal_id,
        )

    @staticmethod
    async def _treasury_reserve(
        pool: LiquidityPool,
        amount: Decimal,
        deal_id: uuid.UUID,
    ) -> None:
        try:
            from repositories.treasury_repository import TreasuryRepository

            async with get_session() as session:
                treasury_repo = TreasuryRepository(session)
                accounts = await treasury_repo.list_accounts(asset=pool.asset)
                for account in accounts:
                    if account.code.endswith(pool.location) or account.code.startswith(
                        pool.location
                    ):
                        from services.treasury_engine import TreasuryEngine

                        await TreasuryEngine.reserve_funds(
                            account_id=account.id,
                            amount=amount,
                            deal_id=deal_id,
                            reference=f"liquidity:{deal_id}",
                        )
                        break
        except Exception:
            pass

    @staticmethod
    async def create_pool(
        actor_id: int,
        *,
        asset: str,
        location: str,
        available_amount: Decimal = Decimal("0"),
    ) -> LiquidityPool:
        if not await LiquidityEngineV1.user_can_access(actor_id):
            raise LiquidityEngineError("Access denied")

        async with get_session() as session:
            repo = LiquidityPoolRepository(session)
            existing = await repo.get_by_asset_location(asset, location)
            if existing is not None:
                return await repo.deposit(existing.id, available_amount) or existing
            return await repo.create(
                asset=asset,
                location=location,
                available_amount=available_amount,
            )

    @staticmethod
    async def check_liquidity(
        asset: str,
        amount: Decimal,
        *,
        location: str | None = None,
        deal_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            pool_repo = LiquidityPoolRepository(session)
            pools = (
                [await pool_repo.get_by_asset_location(asset, location)]
                if location
                else await pool_repo.list_by_asset(asset)
            )
            pools = [p for p in pools if p is not None]

            if not pools:
                await LiquidityEngineV1._create_alert(
                    session,
                    alert_type=LiquidityAlertType.LOW_LIQUIDITY.value,
                    message=f"No liquidity pool for {asset}",
                    asset=asset,
                    deal_id=deal_id,
                )
                await LiquidityEngineV1._publish_event(
                    "liquidity.shortage",
                    "liquidity",
                    deal_id or uuid.uuid4(),
                    {"asset": asset, "amount": str(amount), "reason": "no_pool"},
                )
                return {
                    "asset": asset,
                    "amount": amount,
                    "sufficient": False,
                    "total_free": Decimal("0"),
                    "pools": [],
                }

            total_free = sum(p.free_amount for p in pools)
            sufficient = total_free >= amount

            for pool in pools:
                if pool.free_amount < 0:
                    await LiquidityEngineV1._create_alert(
                        session,
                        alert_type=LiquidityAlertType.NEGATIVE_BALANCE.value,
                        message=f"Negative balance in pool {pool.location}/{pool.asset}",
                        pool_id=pool.id,
                        asset=asset,
                        deal_id=deal_id,
                    )
                elif pool.free_amount < LOW_LIQUIDITY_THRESHOLD:
                    await LiquidityEngineV1._create_alert(
                        session,
                        alert_type=LiquidityAlertType.LOW_LIQUIDITY.value,
                        message=(
                            f"Low liquidity in {pool.location}/{pool.asset}: "
                            f"{pool.free_amount} < {LOW_LIQUIDITY_THRESHOLD}"
                        ),
                        pool_id=pool.id,
                        asset=asset,
                        deal_id=deal_id,
                    )

            if not sufficient:
                await LiquidityEngineV1._publish_event(
                    "liquidity.shortage",
                    "liquidity",
                    deal_id or uuid.uuid4(),
                    {
                        "asset": asset,
                        "amount": str(amount),
                        "total_free": str(total_free),
                    },
                )

            return {
                "asset": asset,
                "amount": amount,
                "sufficient": sufficient,
                "total_free": total_free,
                "pools": [
                    {
                        "id": str(p.id),
                        "location": p.location,
                        "available": p.available_amount,
                        "reserved": p.reserved_amount,
                        "free": p.free_amount,
                    }
                    for p in pools
                ],
            }

    @staticmethod
    async def reserve_liquidity(
        actor_id: int,
        deal_id: uuid.UUID,
        *,
        asset: str | None = None,
        amount: Decimal | None = None,
        location: str | None = None,
    ) -> LiquidityReservation:
        if not await LiquidityEngineV1.user_can_access(actor_id):
            raise LiquidityEngineError("Access denied")

        async with get_session() as session:
            deal = await DealRepository(session).get_by_id(deal_id)
            if deal is None:
                raise LiquidityEngineError(f"Deal not found: {deal_id}")

            resolved_asset = asset or deal.asset_out_type or deal.asset_in_type
            if not resolved_asset:
                raise LiquidityEngineError("Asset could not be determined")

            resolved_amount = amount
            if resolved_amount is None:
                resolved_amount = deal.asset_out_amount or deal.asset_in_amount
            if resolved_amount is None or resolved_amount <= 0:
                raise LiquidityEngineError("Amount could not be determined")

            try:
                from services.pg_pricing_engine import PricingEngineV1

                quote = await PricingEngineV1.calculate_client_price(
                    asset=resolved_asset,
                    deal_id=deal_id,
                )
                if quote.get("client_price"):
                    resolved_amount = max(resolved_amount, quote["client_price"])
            except Exception:
                pass

            check = await LiquidityEngineV1.check_liquidity(
                resolved_asset,
                resolved_amount,
                location=location,
                deal_id=deal_id,
            )
            if not check["sufficient"]:
                raise InsufficientLiquidityError(
                    f"Insufficient liquidity for {resolved_asset}: "
                    f"need {resolved_amount}, free {check['total_free']}"
                )

            pool_repo = LiquidityPoolRepository(session)
            pool = await pool_repo.find_best_pool(
                resolved_asset,
                resolved_amount,
                location=location,
            )
            if pool is None:
                raise InsufficientLiquidityError(f"No pool for {resolved_asset}")

            locked = await pool_repo.get_for_update(pool.id)
            if locked is None:
                raise LiquidityEngineError(f"Pool not found: {pool.id}")

            if locked.free_amount < resolved_amount:
                await LiquidityEngineV1._create_alert(
                    session,
                    alert_type=LiquidityAlertType.POOL_LIMIT_EXCEEDED.value,
                    message=(
                        f"Pool {locked.location}/{locked.asset} limit exceeded: "
                        f"requested {resolved_amount}, free {locked.free_amount}"
                    ),
                    pool_id=locked.id,
                    asset=resolved_asset,
                    deal_id=deal_id,
                )
                await LiquidityEngineV1._publish_event(
                    "liquidity.shortage",
                    "liquidity",
                    deal_id,
                    {
                        "asset": resolved_asset,
                        "amount": str(resolved_amount),
                        "pool_id": str(locked.id),
                    },
                )
                raise InsufficientLiquidityError("Pool limit exceeded")

            locked.reserved_amount += resolved_amount
            locked.updated_at = datetime.now(timezone.utc)

            reservation = await LiquidityReservationRepository(session).create(
                deal_id=deal_id,
                pool_id=locked.id,
                asset=resolved_asset,
                amount=resolved_amount,
            )
            await session.flush()

        await LiquidityEngineV1._treasury_reserve(locked, resolved_amount, deal_id)

        await LiquidityEngineV1._publish_event(
            "liquidity.reserved",
            "liquidity",
            reservation.id,
            {
                "deal_id": str(deal_id),
                "pool_id": str(locked.id),
                "asset": resolved_asset,
                "amount": str(resolved_amount),
                "location": locked.location,
            },
        )
        return reservation

    @staticmethod
    async def release_liquidity(
        actor_id: int,
        reservation_id: uuid.UUID,
    ) -> LiquidityReservation:
        if not await LiquidityEngineV1.user_can_access(actor_id):
            raise LiquidityEngineError("Access denied")

        async with get_session() as session:
            res_repo = LiquidityReservationRepository(session)
            reservation = await res_repo.get_by_id(reservation_id)
            if reservation is None:
                raise LiquidityEngineError(f"Reservation not found: {reservation_id}")
            if reservation.status != LiquidityReservationStatus.ACTIVE.value:
                raise LiquidityEngineError(
                    f"Reservation is not active: {reservation.status}"
                )

            pool = await LiquidityPoolRepository(session).get_for_update(
                reservation.pool_id
            )
            if pool is None:
                raise LiquidityEngineError(f"Pool not found: {reservation.pool_id}")

            pool.reserved_amount = max(
                Decimal("0"),
                pool.reserved_amount - reservation.amount,
            )
            reservation.status = LiquidityReservationStatus.RELEASED.value
            await session.flush()

        await LiquidityEngineV1._publish_event(
            "liquidity.released",
            "liquidity",
            reservation_id,
            {
                "deal_id": str(reservation.deal_id),
                "asset": reservation.asset,
                "amount": str(reservation.amount),
            },
        )
        return reservation

    @staticmethod
    async def consume_liquidity(
        actor_id: int,
        reservation_id: uuid.UUID,
    ) -> LiquidityReservation:
        if not await LiquidityEngineV1.user_can_access(actor_id):
            raise LiquidityEngineError("Access denied")

        async with get_session() as session:
            res_repo = LiquidityReservationRepository(session)
            reservation = await res_repo.get_by_id(reservation_id)
            if reservation is None:
                raise LiquidityEngineError(f"Reservation not found: {reservation_id}")
            if reservation.status != LiquidityReservationStatus.ACTIVE.value:
                raise LiquidityEngineError(
                    f"Reservation is not active: {reservation.status}"
                )

            pool = await LiquidityPoolRepository(session).get_for_update(
                reservation.pool_id
            )
            if pool is None:
                raise LiquidityEngineError(f"Pool not found: {reservation.pool_id}")

            pool.reserved_amount = max(
                Decimal("0"),
                pool.reserved_amount - reservation.amount,
            )
            pool.available_amount = max(
                Decimal("0"),
                pool.available_amount - reservation.amount,
            )
            reservation.status = LiquidityReservationStatus.CONSUMED.value
            await session.flush()

        await LiquidityEngineV1._publish_event(
            "liquidity.consumed",
            "liquidity",
            reservation_id,
            {
                "deal_id": str(reservation.deal_id),
                "asset": reservation.asset,
                "amount": str(reservation.amount),
            },
        )
        return reservation

    @staticmethod
    async def get_status() -> dict[str, Any]:
        async with get_session() as session:
            pools = await LiquidityPoolRepository(session).list_all()
            alerts = await LiquidityAlertRepository(session).list_unresolved()
            return {
                "pools_count": len(pools),
                "pools": [
                    {
                        "id": str(p.id),
                        "asset": p.asset,
                        "location": p.location,
                        "available": str(p.available_amount),
                        "reserved": str(p.reserved_amount),
                        "free": str(p.free_amount),
                    }
                    for p in pools
                ],
                "unresolved_alerts": len(alerts),
                "alerts": [
                    {
                        "id": str(a.id),
                        "type": a.alert_type,
                        "message": a.message,
                        "asset": a.asset,
                    }
                    for a in alerts
                ],
            }
