# Pricing Engine — dynamic rates, partner/manager/VIP pricing.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from database.models.pricing import (
    Markup,
    MarkupAppliesTo,
    MarkupType,
    PricingRule,
    PricingRuleType,
    PricingSource,
    Spread,
    SpreadType,
)
from database.session import get_session
from repositories.pricing_repository import PricingRepository


class PricingEngineError(Exception):
    pass


class PricingEngine:
    @staticmethod
    def _apply_spread(
        base_rate: Decimal,
        spread: Spread | None,
        *,
        side: str = "ask",
    ) -> Decimal:
        if spread is None:
            return base_rate

        spread_value = spread.ask_spread if side == "ask" else spread.bid_spread
        if spread.spread_type == SpreadType.PERCENTAGE.value:
            multiplier = Decimal("1") + (spread_value / Decimal("100"))
            return base_rate * multiplier
        return base_rate + spread_value

    @staticmethod
    def _apply_markup(rate: Decimal, markups: list[Markup]) -> Decimal:
        result = rate
        for markup in markups:
            if markup.markup_type == MarkupType.PERCENTAGE.value:
                result = result * (Decimal("1") + markup.value / Decimal("100"))
            else:
                result = result + markup.value
        return result

    @staticmethod
    async def create_source(
        *,
        code: str,
        name: str,
        asset_in: str,
        asset_out: str,
        base_rate: Decimal,
        source_type: str = "INTERNAL",
    ) -> PricingSource:
        async with get_session() as session:
            repo = PricingRepository(session)
            existing = await repo.get_source_by_code(code)
            if existing is not None:
                return await repo.update_source_rate(existing.id, base_rate) or existing
            return await repo.create_source(
                code=code,
                name=name,
                source_type=source_type,
                asset_in=asset_in,
                asset_out=asset_out,
                base_rate=base_rate,
            )

    @staticmethod
    async def update_dynamic_rate(
        source_id: uuid.UUID,
        base_rate: Decimal,
    ) -> PricingSource:
        async with get_session() as session:
            repo = PricingRepository(session)
            source = await repo.update_source_rate(source_id, base_rate)
            if source is None:
                raise PricingEngineError(f"Source not found: {source_id}")
            return source

    @staticmethod
    async def create_rule(
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
    ) -> PricingRule:
        async with get_session() as session:
            return await PricingRepository(session).create_rule(
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
            )

    @staticmethod
    async def create_spread(
        *,
        asset_in: str,
        asset_out: str,
        bid_spread: Decimal,
        ask_spread: Decimal,
        spread_type: str = SpreadType.PERCENTAGE.value,
        rule_id: uuid.UUID | None = None,
        source_id: uuid.UUID | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
    ) -> Spread:
        async with get_session() as session:
            return await PricingRepository(session).create_spread(
                asset_in=asset_in,
                asset_out=asset_out,
                spread_type=spread_type,
                bid_spread=bid_spread,
                ask_spread=ask_spread,
                rule_id=rule_id,
                source_id=source_id,
                min_amount=min_amount,
                max_amount=max_amount,
            )

    @staticmethod
    async def create_markup(
        *,
        applies_to: str,
        markup_type: str,
        value: Decimal,
        rule_id: uuid.UUID | None = None,
        target_id: int | None = None,
        asset_in: str | None = None,
        asset_out: str | None = None,
        priority: int = 100,
    ) -> Markup:
        async with get_session() as session:
            return await PricingRepository(session).create_markup(
                applies_to=applies_to,
                markup_type=markup_type,
                value=value,
                rule_id=rule_id,
                target_id=target_id,
                asset_in=asset_in,
                asset_out=asset_out,
                priority=priority,
            )

    @staticmethod
    async def _calculate_rate(
        *,
        asset_in: str,
        asset_out: str,
        amount: Decimal,
        rule_type: str,
        partner_id: int | None = None,
        manager_id: int | None = None,
        vip_user_id: int | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            repo = PricingRepository(session)
            rule = await repo.find_rule(
                rule_type=rule_type,
                asset_in=asset_in,
                asset_out=asset_out,
                partner_id=partner_id,
                manager_id=manager_id,
                vip_user_id=vip_user_id,
            )

            source: PricingSource | None = None
            if rule is not None and rule.source_id is not None:
                source = await repo.get_source(rule.source_id)
            if source is None:
                source = await repo.get_active_source_for_pair(asset_in, asset_out)
            if source is None:
                raise PricingEngineError(
                    f"No pricing source for {asset_in}/{asset_out}"
                )

            spread = None
            if rule is not None:
                spread = await repo.get_spread_for_rule(rule.id, amount=amount)
            if spread is None:
                spread = await repo.get_default_spread(asset_in, asset_out, amount=amount)

            base_rate = source.base_rate
            rate_after_spread = PricingEngine._apply_spread(base_rate, spread, side="ask")

            markups: list[Markup] = []
            if rule is not None:
                markups.extend(await repo.list_markups_for_rule(rule.id))
            if partner_id is not None:
                markups.extend(
                    await repo.list_markups_for_target(
                        MarkupAppliesTo.PARTNER.value,
                        partner_id,
                        asset_in=asset_in,
                        asset_out=asset_out,
                    )
                )
            if manager_id is not None:
                markups.extend(
                    await repo.list_markups_for_target(
                        MarkupAppliesTo.MANAGER.value,
                        manager_id,
                        asset_in=asset_in,
                        asset_out=asset_out,
                    )
                )
            if vip_user_id is not None:
                markups.extend(
                    await repo.list_markups_for_target(
                        MarkupAppliesTo.VIP.value,
                        vip_user_id,
                        asset_in=asset_in,
                        asset_out=asset_out,
                    )
                )
            markups.extend(
                await repo.list_markups_for_target(
                    MarkupAppliesTo.GLOBAL.value,
                    asset_in=asset_in,
                    asset_out=asset_out,
                )
            )

            final_rate = PricingEngine._apply_markup(rate_after_spread, markups)
            output_amount = amount * final_rate

            return {
                "asset_in": asset_in,
                "asset_out": asset_out,
                "amount_in": amount,
                "amount_out": output_amount,
                "base_rate": base_rate,
                "rate_after_spread": rate_after_spread,
                "final_rate": final_rate,
                "rule_type": rule_type,
                "rule_id": str(rule.id) if rule else None,
                "source_id": str(source.id),
                "spread_id": str(spread.id) if spread else None,
                "markup_count": len(markups),
            }

    @staticmethod
    async def get_dynamic_rate(
        asset_in: str,
        asset_out: str,
        amount: Decimal,
    ) -> dict[str, Any]:
        return await PricingEngine._calculate_rate(
            asset_in=asset_in,
            asset_out=asset_out,
            amount=amount,
            rule_type=PricingRuleType.DYNAMIC.value,
        )

    @staticmethod
    async def get_partner_pricing(
        partner_id: int,
        asset_in: str,
        asset_out: str,
        amount: Decimal,
    ) -> dict[str, Any]:
        return await PricingEngine._calculate_rate(
            asset_in=asset_in,
            asset_out=asset_out,
            amount=amount,
            rule_type=PricingRuleType.PARTNER.value,
            partner_id=partner_id,
        )

    @staticmethod
    async def get_manager_pricing(
        manager_id: int,
        asset_in: str,
        asset_out: str,
        amount: Decimal,
    ) -> dict[str, Any]:
        return await PricingEngine._calculate_rate(
            asset_in=asset_in,
            asset_out=asset_out,
            amount=amount,
            rule_type=PricingRuleType.MANAGER.value,
            manager_id=manager_id,
        )

    @staticmethod
    async def get_vip_pricing(
        user_id: int,
        asset_in: str,
        asset_out: str,
        amount: Decimal,
    ) -> dict[str, Any]:
        return await PricingEngine._calculate_rate(
            asset_in=asset_in,
            asset_out=asset_out,
            amount=amount,
            rule_type=PricingRuleType.VIP.value,
            vip_user_id=user_id,
        )

    @staticmethod
    async def get_best_rate(
        *,
        asset_in: str,
        asset_out: str,
        amount: Decimal,
        partner_id: int | None = None,
        manager_id: int | None = None,
        vip_user_id: int | None = None,
    ) -> dict[str, Any]:
        candidates: list[dict[str, Any]] = []

        if vip_user_id is not None:
            try:
                candidates.append(
                    await PricingEngine.get_vip_pricing(
                        vip_user_id, asset_in, asset_out, amount
                    )
                )
            except PricingEngineError:
                pass

        if partner_id is not None:
            try:
                candidates.append(
                    await PricingEngine.get_partner_pricing(
                        partner_id, asset_in, asset_out, amount
                    )
                )
            except PricingEngineError:
                pass

        if manager_id is not None:
            try:
                candidates.append(
                    await PricingEngine.get_manager_pricing(
                        manager_id, asset_in, asset_out, amount
                    )
                )
            except PricingEngineError:
                pass

        try:
            candidates.append(
                await PricingEngine.get_dynamic_rate(asset_in, asset_out, amount)
            )
        except PricingEngineError:
            pass

        if not candidates:
            raise PricingEngineError(
                f"No pricing available for {asset_in}/{asset_out}"
            )

        return max(candidates, key=lambda item: item["final_rate"])
