# OTC Matching Engine v1 — smart counterparty matching and execution.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.otc_matching import (
    OtcExecutionMode,
    OtcMatchStatus,
    OtcMatchingStrategy,
    OtcOrderStatus,
    OtcOrderType,
    OtcRouteStatus,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.otc_matching_repository import (
    OtcExecutionRouteRepository,
    OtcFillHistoryRepository,
    OtcMatchRepository,
    OtcOrderRepository,
    OtcQuoteRepository,
)
from repositories.partner_engine_repositories import PartnerRepository
from repositories.user_role_repository import UserRoleRepository

OTC_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER", "ACCOUNTANT"})


class OtcMatchingEngineError(Exception):
    pass


class OtcMatchingEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in OTC_ROLES for role in roles)

    @staticmethod
    async def _audit(
        session,
        *,
        user_id: int,
        action: str,
        entity_id: str,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> None:
        await AuditRepository(session).create_log(
            user_id=user_id,
            entity_type="otc",
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )

    @staticmethod
    async def _publish_event(
        event_type: str,
        aggregate_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> None:
        try:
            from events.crm_publisher import publish_crm_event

            await publish_crm_event(event_type, "otc", aggregate_id, payload)
        except Exception:
            pass

    @staticmethod
    async def _partner_risk_score(session, partner_id: uuid.UUID) -> int:
        try:
            from repositories.compliance_repository import RiskProfileRepository

            profile = await RiskProfileRepository(session).get_by_partner(partner_id)
            return profile.risk_score if profile else 0
        except Exception:
            return 50

    @staticmethod
    async def _partner_liquidity_score(
        session,
        asset: str,
        amount: Decimal,
    ) -> Decimal:
        try:
            from services.pg_liquidity_engine import LiquidityEngineV1

            check = await LiquidityEngineV1.check_liquidity(asset, amount)
            if not check["sufficient"]:
                return Decimal("0")
            total = check["total_free"]
            if total <= 0:
                return Decimal("0")
            return min(Decimal("100"), (total / amount) * Decimal("10"))
        except Exception:
            return Decimal("50")

    @staticmethod
    def _requires_approval(execution_mode: str) -> bool:
        return execution_mode in {
            OtcExecutionMode.MANUAL.value,
            OtcExecutionMode.SEMI_AUTO.value,
        }

    @staticmethod
    def _rank_quotes(
        order_type: str,
        quotes: list,
        *,
        strategy: str,
        scores: dict[uuid.UUID, dict[str, Any]],
    ) -> list:
        def sort_key(quote):
            score = scores.get(quote.partner_id, {})
            price = quote.price
            if order_type == OtcOrderType.BUY.value:
                price_key = price
            else:
                price_key = -price

            if strategy == OtcMatchingStrategy.BEST_PRICE.value:
                return (price_key, -quote.available_amount)
            if strategy == OtcMatchingStrategy.BEST_LIQUIDITY.value:
                return (-score.get("liquidity", Decimal("0")), price_key)
            if strategy == OtcMatchingStrategy.LOWEST_RISK.value:
                return (score.get("risk", 50), price_key)
            if strategy == OtcMatchingStrategy.FASTEST_EXECUTION.value:
                received = quote.received_at.timestamp() if quote.received_at else 0
                return (-received, price_key)
            return (price_key,)

        return sorted(quotes, key=sort_key)

    @staticmethod
    async def create_order(
        actor_id: int,
        *,
        order_type: str,
        asset: str,
        quote_asset: str,
        amount: Decimal,
        execution_mode: str = OtcExecutionMode.MANUAL.value,
        matching_strategy: str = OtcMatchingStrategy.BEST_PRICE.value,
        deal_id: uuid.UUID | None = None,
        partner_id: uuid.UUID | None = None,
        price_limit: Decimal | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await OtcMatchingEngineV1.user_can_access(actor_id):
            raise OtcMatchingEngineError("Access denied")

        async with get_session() as session:
            order = await OtcOrderRepository(session).create(
                order_type=order_type,
                asset=asset,
                quote_asset=quote_asset,
                amount=amount,
                execution_mode=execution_mode,
                matching_strategy=matching_strategy,
                deal_id=deal_id,
                partner_id=partner_id,
                created_by=actor_id,
                price_limit=price_limit,
                notes=notes,
            )

        await OtcMatchingEngineV1._publish_event(
            "otc.order.created",
            order.id,
            {
                "order_type": order_type,
                "asset": asset,
                "amount": str(amount),
                "execution_mode": execution_mode,
            },
        )
        return {
            "order_id": str(order.id),
            "status": order.status,
            "remaining_amount": str(order.remaining_amount),
        }

    @staticmethod
    async def submit_quote(
        actor_id: int,
        *,
        order_id: uuid.UUID,
        partner_id: uuid.UUID,
        price: Decimal,
        amount: Decimal,
        ttl_minutes: int = 30,
    ) -> dict[str, Any]:
        if not await OtcMatchingEngineV1.user_can_access(actor_id):
            raise OtcMatchingEngineError("Access denied")

        async with get_session() as session:
            order = await OtcOrderRepository(session).get_by_id(order_id)
            if order is None:
                raise OtcMatchingEngineError(f"Order not found: {order_id}")
            partner = await PartnerRepository(session).get_by_id(partner_id)
            if partner is None:
                raise OtcMatchingEngineError(f"Partner not found: {partner_id}")

            quote = await OtcQuoteRepository(session).create(
                order_id=order_id,
                partner_id=partner_id,
                price=price,
                amount=amount,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes),
            )

        await OtcMatchingEngineV1._publish_event(
            "otc.quote.received",
            order_id,
            {
                "quote_id": str(quote.id),
                "partner_id": str(partner_id),
                "price": str(price),
                "amount": str(amount),
            },
        )
        return {
            "quote_id": str(quote.id),
            "status": quote.status,
            "expires_at": quote.expires_at.isoformat() if quote.expires_at else None,
        }

    @staticmethod
    async def find_matches(
        actor_id: int,
        order_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await OtcMatchingEngineV1.user_can_access(actor_id):
            raise OtcMatchingEngineError("Access denied")

        async with get_session() as session:
            order = await OtcOrderRepository(session).get_by_id(order_id)
            if order is None:
                raise OtcMatchingEngineError(f"Order not found: {order_id}")
            if order.status in {
                OtcOrderStatus.FILLED.value,
                OtcOrderStatus.CANCELLED.value,
            }:
                raise OtcMatchingEngineError(f"Order not matchable: {order.status}")

            quotes = await OtcQuoteRepository(session).list_active_for_order(order_id)
            if not quotes:
                return {"order_id": str(order_id), "matches": [], "candidates": []}

            if order.price_limit is not None:
                if order.order_type == OtcOrderType.BUY.value:
                    quotes = [q for q in quotes if q.price <= order.price_limit]
                else:
                    quotes = [q for q in quotes if q.price >= order.price_limit]

            scores: dict[uuid.UUID, dict[str, Any]] = {}
            for quote in quotes:
                scores[quote.partner_id] = {
                    "risk": await OtcMatchingEngineV1._partner_risk_score(
                        session, quote.partner_id
                    ),
                    "liquidity": await OtcMatchingEngineV1._partner_liquidity_score(
                        session, order.asset, quote.available_amount
                    ),
                }

            ranked = OtcMatchingEngineV1._rank_quotes(
                order.order_type,
                quotes,
                strategy=order.matching_strategy,
                scores=scores,
            )

            remaining = order.remaining_amount
            candidates: list[dict[str, Any]] = []
            for quote in ranked:
                if remaining <= 0:
                    break
                fill_amount = min(remaining, quote.available_amount)
                candidates.append(
                    {
                        "quote_id": str(quote.id),
                        "partner_id": str(quote.partner_id),
                        "price": str(quote.price),
                        "amount": str(fill_amount),
                        "risk_score": scores[quote.partner_id]["risk"],
                        "liquidity_score": str(scores[quote.partner_id]["liquidity"]),
                    }
                )
                remaining -= fill_amount

        return {
            "order_id": str(order_id),
            "strategy": order.matching_strategy,
            "candidates": candidates,
        }

    @staticmethod
    async def calculate_execution_route(
        actor_id: int,
        order_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await OtcMatchingEngineV1.user_can_access(actor_id):
            raise OtcMatchingEngineError("Access denied")

        match_result = await OtcMatchingEngineV1.find_matches(actor_id, order_id)
        candidates = match_result.get("candidates", [])

        async with get_session() as session:
            order = await OtcOrderRepository(session).get_by_id(order_id)
            if order is None:
                raise OtcMatchingEngineError(f"Order not found: {order_id}")

            route_repo = OtcExecutionRouteRepository(session)
            existing = await route_repo.list_by_order(order_id)
            for route in existing:
                if route.status == OtcRouteStatus.PLANNED.value:
                    await route_repo.update_status(route.id, OtcRouteStatus.CANCELLED.value)

            steps: list[dict[str, Any]] = []
            for index, candidate in enumerate(candidates, start=1):
                partner_id = uuid.UUID(candidate["partner_id"])
                amount = Decimal(candidate["amount"])
                price = Decimal(candidate["price"])
                route = await route_repo.create(
                    order_id=order_id,
                    partner_id=partner_id,
                    step_order=index,
                    amount=amount,
                    price=price,
                    liquidity_score=Decimal(candidate["liquidity_score"]),
                    risk_score=candidate["risk_score"],
                    metadata_json={"quote_id": candidate["quote_id"]},
                )
                steps.append(
                    {
                        "route_id": str(route.id),
                        "step_order": index,
                        "partner_id": candidate["partner_id"],
                        "amount": candidate["amount"],
                        "price": candidate["price"],
                        "status": route.status,
                    }
                )

        return {
            "order_id": str(order_id),
            "execution_mode": order.execution_mode,
            "requires_approval": OtcMatchingEngineV1._requires_approval(
                order.execution_mode
            ),
            "steps": steps,
        }

    @staticmethod
    async def split_order(
        actor_id: int,
        order_id: uuid.UUID,
    ) -> dict[str, Any]:
        return await OtcMatchingEngineV1.calculate_execution_route(actor_id, order_id)

    @staticmethod
    async def execute_match(
        actor_id: int,
        order_id: uuid.UUID,
        *,
        auto_approve: bool = False,
    ) -> dict[str, Any]:
        if not await OtcMatchingEngineV1.user_can_access(actor_id):
            raise OtcMatchingEngineError("Access denied")

        async with get_session() as session:
            existing_routes = await OtcExecutionRouteRepository(session).list_by_order(
                order_id
            )
            has_planned = any(
                r.status == OtcRouteStatus.PLANNED.value for r in existing_routes
            )

        if not has_planned:
            await OtcMatchingEngineV1.calculate_execution_route(actor_id, order_id)

        executed: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        async with get_session() as session:
            order = await OtcOrderRepository(session).get_by_id(order_id)
            if order is None:
                raise OtcMatchingEngineError(f"Order not found: {order_id}")

            routes = await OtcExecutionRouteRepository(session).list_by_order(order_id)
            planned = [r for r in routes if r.status == OtcRouteStatus.PLANNED.value]

            requires_approval = OtcMatchingEngineV1._requires_approval(
                order.execution_mode
            )
            if (
                requires_approval
                and not auto_approve
                and actor_id != OWNER_ID
                and order.execution_mode == OtcExecutionMode.MANUAL.value
            ):
                raise OtcMatchingEngineError("Manual approval required for execution")

            match_repo = OtcMatchRepository(session)
            quote_repo = OtcQuoteRepository(session)
            fill_repo = OtcFillHistoryRepository(session)
            order_repo = OtcOrderRepository(session)
            route_repo = OtcExecutionRouteRepository(session)

            for route in planned:
                try:
                    order = await order_repo.get_by_id(order_id)
                    if order is None or order.remaining_amount <= 0:
                        break

                    quote_id_str = (route.metadata_json or {}).get("quote_id")
                    if not quote_id_str:
                        raise OtcMatchingEngineError("Route missing quote reference")

                    quote_id = uuid.UUID(quote_id_str)
                    quote = await quote_repo.get_by_id(quote_id)
                    if quote is None:
                        raise OtcMatchingEngineError(f"Quote not found: {quote_id}")

                    fill_amount = min(
                        route.amount, order.remaining_amount, quote.available_amount
                    )
                    if fill_amount <= 0:
                        continue

                    match = await match_repo.create(
                        order_id=order_id,
                        quote_id=quote_id,
                        partner_id=route.partner_id,
                        matched_amount=fill_amount,
                        matched_price=route.price,
                        requires_approval=requires_approval and not auto_approve,
                    )

                    if requires_approval or auto_approve or actor_id == OWNER_ID:
                        await match_repo.approve(match.id, approved_by=actor_id)

                    await route_repo.update_status(
                        route.id, OtcRouteStatus.EXECUTING.value
                    )
                    await match_repo.update_status(
                        match.id, OtcMatchStatus.EXECUTING.value
                    )

                    await quote_repo.consume_amount(quote_id, fill_amount)
                    await order_repo.apply_fill(order_id, fill_amount)

                    fill = await fill_repo.record(
                        order_id=order_id,
                        match_id=match.id,
                        route_id=route.id,
                        partner_id=route.partner_id,
                        fill_amount=fill_amount,
                        fill_price=route.price,
                    )

                    await route_repo.update_status(
                        route.id, OtcRouteStatus.COMPLETED.value
                    )
                    await match_repo.update_status(
                        match.id, OtcMatchStatus.COMPLETED.value
                    )

                    await OtcMatchingEngineV1._audit(
                        session,
                        user_id=actor_id,
                        action=AuditAction.MATCH_CREATED.value,
                        entity_id=str(match.id),
                        new_value={
                            "order_id": str(order_id),
                            "amount": str(fill_amount),
                            "price": str(route.price),
                        },
                    )
                    await OtcMatchingEngineV1._audit(
                        session,
                        user_id=actor_id,
                        action=AuditAction.MATCH_EXECUTED.value,
                        entity_id=str(match.id),
                        new_value={"fill_id": str(fill.id)},
                    )

                    executed.append(
                        {
                            "match_id": str(match.id),
                            "route_id": str(route.id),
                            "partner_id": str(route.partner_id),
                            "fill_amount": str(fill_amount),
                            "fill_price": str(route.price),
                        }
                    )

                except Exception as exc:
                    await route_repo.update_status(route.id, OtcRouteStatus.FAILED.value)
                    failed.append({"route_id": str(route.id), "error": str(exc)})

            order = await order_repo.get_by_id(order_id)

        for item in executed:
            await OtcMatchingEngineV1._publish_event(
                "otc.match.created",
                uuid.UUID(item["match_id"]),
                {
                    "order_id": str(order_id),
                    "partner_id": item["partner_id"],
                    "amount": item["fill_amount"],
                },
            )
        for item in failed:
            await OtcMatchingEngineV1._publish_event(
                "otc.execution.failed",
                order_id,
                item,
            )

        if order and order.status == OtcOrderStatus.FILLED.value:
            await OtcMatchingEngineV1._publish_event(
                "otc.order.filled",
                order_id,
                {
                    "filled_amount": str(order.filled_amount),
                    "executed_legs": len(executed),
                },
            )

        return {
            "order_id": str(order_id),
            "status": order.status if order else None,
            "filled_amount": str(order.filled_amount) if order else "0",
            "executed": executed,
            "failed": failed,
        }

    @staticmethod
    async def cancel_order(
        actor_id: int,
        order_id: uuid.UUID,
        *,
        reason: str | None = None,
    ) -> dict[str, Any]:
        if not await OtcMatchingEngineV1.user_can_access(actor_id):
            raise OtcMatchingEngineError("Access denied")

        async with get_session() as session:
            order = await OtcOrderRepository(session).update_status(
                order_id, OtcOrderStatus.CANCELLED.value
            )
            if order is None:
                raise OtcMatchingEngineError(f"Order not found: {order_id}")

            routes = await OtcExecutionRouteRepository(session).list_by_order(order_id)
            for route in routes:
                if route.status in {
                    OtcRouteStatus.PLANNED.value,
                    OtcRouteStatus.APPROVED.value,
                }:
                    await OtcExecutionRouteRepository(session).update_status(
                        route.id, OtcRouteStatus.CANCELLED.value
                    )

            matches = await OtcMatchRepository(session).list_by_order(order_id)
            for match in matches:
                if match.status in {
                    OtcMatchStatus.PENDING.value,
                    OtcMatchStatus.APPROVED.value,
                }:
                    await OtcMatchRepository(session).update_status(
                        match.id, OtcMatchStatus.CANCELLED.value
                    )

            await OtcMatchingEngineV1._audit(
                session,
                user_id=actor_id,
                action=AuditAction.MATCH_CANCELLED.value,
                entity_id=str(order_id),
                new_value={"reason": reason},
            )

        return {"order_id": str(order_id), "status": OtcOrderStatus.CANCELLED.value}

    @staticmethod
    async def get_order(
        actor_id: int,
        order_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await OtcMatchingEngineV1.user_can_access(actor_id):
            raise OtcMatchingEngineError("Access denied")

        async with get_session() as session:
            order = await OtcOrderRepository(session).get_by_id(order_id)
            if order is None:
                raise OtcMatchingEngineError(f"Order not found: {order_id}")

            routes = await OtcExecutionRouteRepository(session).list_by_order(order_id)
            matches = await OtcMatchRepository(session).list_by_order(order_id)
            fills = await OtcFillHistoryRepository(session).list_by_order(order_id)
            quotes = await OtcQuoteRepository(session).list_active_for_order(order_id)

            return {
                "order": {
                    "id": str(order.id),
                    "order_type": order.order_type,
                    "asset": order.asset,
                    "quote_asset": order.quote_asset,
                    "amount": str(order.amount),
                    "filled_amount": str(order.filled_amount),
                    "remaining_amount": str(order.remaining_amount),
                    "status": order.status,
                    "execution_mode": order.execution_mode,
                    "matching_strategy": order.matching_strategy,
                },
                "active_quotes": len(quotes),
                "routes": [
                    {
                        "id": str(r.id),
                        "step_order": r.step_order,
                        "partner_id": str(r.partner_id),
                        "amount": str(r.amount),
                        "price": str(r.price),
                        "status": r.status,
                    }
                    for r in routes
                ],
                "matches": [
                    {
                        "id": str(m.id),
                        "partner_id": str(m.partner_id),
                        "matched_amount": str(m.matched_amount),
                        "status": m.status,
                    }
                    for m in matches
                ],
                "fills": [
                    {
                        "id": str(f.id),
                        "fill_amount": str(f.fill_amount),
                        "fill_price": str(f.fill_price),
                        "filled_at": f.filled_at.isoformat(),
                    }
                    for f in fills
                ],
            }
