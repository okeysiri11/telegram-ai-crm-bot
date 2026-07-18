# Pricing Engine v1 — universal pricing and quotation subsystem.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from config import OWNER_ID, PRICING_COMPANY_MARGIN
from database.models.audit_log import AuditAction
from database.models.pricing_v1 import (
    ManagerPricing,
    PartnerPricing,
    PriceSource,
    SpreadRule,
    SpreadRuleType,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.deal_repository import DealRepository
from repositories.partner_engine_repositories import PartnerRepository
from repositories.pricing_v1_repository import (
    ManagerPricingRepository,
    PartnerPricingRepository,
    PriceSourceRepository,
    SpreadRuleRepository,
)
from repositories.user_role_repository import UserRoleRepository

PRICING_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
DEFAULT_COMPANY_MARGIN = Decimal(PRICING_COMPANY_MARGIN)


class PricingEngineV1Error(Exception):
    pass


class PermissionDeniedError(PricingEngineV1Error):
    pass


class PricingEngineV1:
    @staticmethod
    def manager_uuid(manager_id: int | uuid.UUID) -> uuid.UUID:
        if isinstance(manager_id, uuid.UUID):
            return manager_id
        return uuid.uuid5(uuid.NAMESPACE_OID, f"manager:{manager_id}")

    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in PRICING_ROLES for role in roles)

    @staticmethod
    async def _audit(
        session,
        *,
        user_id: int,
        action: str,
        entity_type: str,
        entity_id: str,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> None:
        await AuditRepository(session).create_log(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )

    @staticmethod
    async def _publish_event(
        event_type: str,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> None:
        try:
            from services import crm_event_bus as bus

            await bus.publish_event(
                event_type,
                aggregate_type,
                aggregate_id,
                payload,
            )
        except Exception:
            pass

    @staticmethod
    def _apply_spread_amount(
        base: Decimal,
        spread_rule: SpreadRule | None,
    ) -> Decimal:
        if spread_rule is None:
            return Decimal("0")
        if spread_rule.spread_type == SpreadRuleType.PERCENTAGE.value:
            return base * (spread_rule.value / Decimal("100"))
        return spread_rule.value

    @staticmethod
    async def update_price(
        actor_id: int,
        *,
        source_name: str,
        asset: str,
        bid_price: Decimal,
        ask_price: Decimal,
    ) -> PriceSource:
        if not await PricingEngineV1.user_can_access(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            repo = PriceSourceRepository(session)
            existing = await repo.get_best_for_asset(asset)
            old_value = None
            if existing is not None and existing.source_name == source_name:
                old_value = {
                    "bid_price": str(existing.bid_price),
                    "ask_price": str(existing.ask_price),
                }

            source = await repo.upsert(
                source_name=source_name,
                asset=asset,
                bid_price=bid_price,
                ask_price=ask_price,
            )

            await PricingEngineV1._audit(
                session,
                user_id=actor_id,
                action=AuditAction.PRICE_CHANGED.value,
                entity_type="price_source",
                entity_id=str(source.id),
                old_value=old_value,
                new_value={
                    "source_name": source_name,
                    "asset": asset,
                    "bid_price": str(bid_price),
                    "ask_price": str(ask_price),
                },
            )

        await PricingEngineV1._publish_event(
            "price.updated",
            "price",
            source.id,
            {
                "source_name": source_name,
                "asset": asset,
                "bid_price": str(bid_price),
                "ask_price": str(ask_price),
            },
        )
        return source

    @staticmethod
    async def create_spread_rule(
        actor_id: int,
        *,
        asset: str,
        spread_type: str,
        value: Decimal,
        priority: int = 100,
    ) -> SpreadRule:
        if not await PricingEngineV1.user_can_access(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            rule = await SpreadRuleRepository(session).create(
                asset=asset,
                spread_type=spread_type,
                value=value,
                priority=priority,
            )
            await PricingEngineV1._audit(
                session,
                user_id=actor_id,
                action=AuditAction.SPREAD_CHANGED.value,
                entity_type="spread_rule",
                entity_id=str(rule.id),
                new_value={
                    "asset": asset,
                    "spread_type": spread_type,
                    "value": str(value),
                    "priority": priority,
                },
            )

        await PricingEngineV1._publish_event(
            "spread.changed",
            "price",
            rule.id,
            {"asset": asset, "spread_type": spread_type, "value": str(value)},
        )
        return rule

    @staticmethod
    async def update_spread_rule(
        actor_id: int,
        rule_id: uuid.UUID,
        value: Decimal,
    ) -> SpreadRule:
        if not await PricingEngineV1.user_can_access(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            repo = SpreadRuleRepository(session)
            existing = await repo.get_by_id(rule_id)
            if existing is None:
                raise PricingEngineV1Error(f"Spread rule not found: {rule_id}")

            old_value = {"value": str(existing.value)}
            rule = await repo.update_value(rule_id, value)
            if rule is None:
                raise PricingEngineV1Error(f"Spread rule not found: {rule_id}")

            await PricingEngineV1._audit(
                session,
                user_id=actor_id,
                action=AuditAction.SPREAD_CHANGED.value,
                entity_type="spread_rule",
                entity_id=str(rule_id),
                old_value=old_value,
                new_value={"value": str(value)},
            )

        await PricingEngineV1._publish_event(
            "spread.changed",
            "price",
            rule_id,
            {"asset": rule.asset, "value": str(value)},
        )
        return rule

    @staticmethod
    async def set_partner_pricing(
        actor_id: int,
        partner_id: uuid.UUID,
        *,
        asset: str,
        custom_spread: Decimal,
    ) -> PartnerPricing:
        if not await PricingEngineV1.user_can_access(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            partner = await PartnerRepository(session).get_by_id(partner_id)
            if partner is None:
                raise PricingEngineV1Error(f"Partner not found: {partner_id}")

            repo = PartnerPricingRepository(session)
            existing = await repo.get_for_partner(partner_id, asset)
            old_value = (
                {"custom_spread": str(existing.custom_spread)} if existing else None
            )

            pricing = await repo.upsert(
                partner_id=partner_id,
                asset=asset,
                custom_spread=custom_spread,
            )

            await PricingEngineV1._audit(
                session,
                user_id=actor_id,
                action=AuditAction.SPREAD_CHANGED.value,
                entity_type="partner_pricing",
                entity_id=str(partner_id),
                old_value=old_value,
                new_value={"asset": asset, "custom_spread": str(custom_spread)},
            )

        await PricingEngineV1._publish_event(
            "partner.price.updated",
            "partner",
            partner_id,
            {"asset": asset, "custom_spread": str(custom_spread)},
        )
        return pricing

    @staticmethod
    async def set_manager_pricing(
        actor_id: int,
        manager_id: int | uuid.UUID,
        *,
        asset: str,
        custom_margin: Decimal,
    ) -> ManagerPricing:
        if not await PricingEngineV1.user_can_access(actor_id):
            raise PermissionDeniedError("Access denied")

        manager_uuid = PricingEngineV1.manager_uuid(manager_id)

        async with get_session() as session:
            repo = ManagerPricingRepository(session)
            existing = await repo.get_for_manager(manager_uuid, asset)
            old_value = (
                {"custom_margin": str(existing.custom_margin)} if existing else None
            )

            pricing = await repo.upsert(
                manager_id=manager_uuid,
                asset=asset,
                custom_margin=custom_margin,
            )

            await PricingEngineV1._audit(
                session,
                user_id=actor_id,
                action=AuditAction.MANAGER_MARGIN_CHANGED.value,
                entity_type="manager_pricing",
                entity_id=str(manager_uuid),
                old_value=old_value,
                new_value={"asset": asset, "custom_margin": str(custom_margin)},
            )

        return pricing

    @staticmethod
    async def calculate_client_price(
        *,
        asset: str,
        partner_id: uuid.UUID | None = None,
        manager_id: int | uuid.UUID | None = None,
        deal_id: uuid.UUID | None = None,
        side: str = "ask",
        company_margin: Decimal | None = None,
    ) -> dict[str, Any]:
        """Calculate client price: market + spread + partner_fee + manager_fee + company_margin."""
        async with get_session() as session:
            deal_repo = DealRepository(session)
            price_repo = PriceSourceRepository(session)
            spread_repo = SpreadRuleRepository(session)
            partner_repo = PartnerPricingRepository(session)
            manager_repo = ManagerPricingRepository(session)

            resolved_partner_id = partner_id
            resolved_manager_id = manager_id
            resolved_asset = asset

            if deal_id is not None:
                deal = await deal_repo.get_by_id(deal_id)
                if deal is None:
                    raise PricingEngineV1Error(f"Deal not found: {deal_id}")
                if deal.manager_id is not None:
                    resolved_manager_id = deal.manager_id
                resolved_asset = deal.asset_out_type or deal.asset_in_type or asset

            source = await price_repo.get_best_for_asset(resolved_asset)
            if source is None:
                raise PricingEngineV1Error(f"No price source for asset: {resolved_asset}")

            market_price = source.ask_price if side == "ask" else source.bid_price
            spread_rule = await spread_repo.get_best_for_asset(resolved_asset)
            spread_amount = PricingEngineV1._apply_spread_amount(market_price, spread_rule)

            partner_fee = Decimal("0")
            if resolved_partner_id is not None:
                partner_pricing = await partner_repo.get_for_partner(
                    resolved_partner_id,
                    resolved_asset,
                )
                if partner_pricing is not None:
                    partner_fee = partner_pricing.custom_spread

            manager_fee = Decimal("0")
            if resolved_manager_id is not None:
                manager_uuid = PricingEngineV1.manager_uuid(resolved_manager_id)
                manager_pricing = await manager_repo.get_for_manager(
                    manager_uuid,
                    resolved_asset,
                )
                if manager_pricing is not None:
                    manager_fee = manager_pricing.custom_margin

            margin_amount = (
                company_margin if company_margin is not None else DEFAULT_COMPANY_MARGIN
            )

            client_price = (
                market_price + spread_amount + partner_fee + manager_fee + margin_amount
            )

            return {
                "asset": resolved_asset,
                "side": side,
                "market_price": market_price,
                "spread": spread_amount,
                "partner_fee": partner_fee,
                "manager_fee": manager_fee,
                "company_margin": margin_amount,
                "client_price": client_price,
                "price_source_id": str(source.id),
                "price_source_name": source.source_name,
                "spread_rule_id": str(spread_rule.id) if spread_rule else None,
                "partner_id": str(resolved_partner_id) if resolved_partner_id else None,
                "manager_id": str(PricingEngineV1.manager_uuid(resolved_manager_id))
                if resolved_manager_id is not None
                else None,
                "deal_id": str(deal_id) if deal_id else None,
            }
