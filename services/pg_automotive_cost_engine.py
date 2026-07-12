# Automotive Cost Engine v1 — cost calculation, margin rules, vehicle pricing.

from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from config import OWNER_ID
from database.models.automotive_cost import (
    CostItemType,
    LogisticsRoute,
    MarginRuleType,
    VehicleCostStatus,
)
from database.session import get_session
from repositories.automotive_cost_repository import (
    CostItemRepository,
    MarginRuleRepository,
    VehicleCostRepository,
)
from repositories.automotive_inventory_repository import VehicleRepository
from repositories.user_role_repository import UserRoleRepository

COST_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})

LOGISTICS_RATES: dict[str, Decimal] = {
    LogisticsRoute.USA_ODESSA.value: Decimal("2200"),
    LogisticsRoute.USA_KYIV.value: Decimal("2500"),
    LogisticsRoute.EU_ODESSA.value: Decimal("1200"),
    LogisticsRoute.LOCAL.value: Decimal("500"),
}

DEFAULT_CUSTOMS_RATE = Decimal("0.17")
DEFAULT_AUCTION_FEE_RATE = Decimal("0.0714")
MONEY = Decimal("0.01")


class AutomotiveCostEngineError(Exception):
    pass


class AutomotiveCostEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in COST_ROLES for role in roles)

    @staticmethod
    def _quantize(amount: Decimal) -> Decimal:
        return amount.quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_logistics(
        route: str = LogisticsRoute.USA_ODESSA.value,
        *,
        override_amount: Decimal | None = None,
    ) -> Decimal:
        if override_amount is not None:
            return AutomotiveCostEngineV1._quantize(override_amount)
        rate = LOGISTICS_RATES.get(route)
        if rate is None:
            raise AutomotiveCostEngineError(f"Unknown logistics route: {route}")
        return rate

    @staticmethod
    def calculate_customs(
        cif_base: Decimal,
        *,
        rate_percent: Decimal | None = None,
        override_amount: Decimal | None = None,
    ) -> Decimal:
        if override_amount is not None:
            return AutomotiveCostEngineV1._quantize(override_amount)
        rate = rate_percent if rate_percent is not None else DEFAULT_CUSTOMS_RATE
        return AutomotiveCostEngineV1._quantize(cif_base * rate)

    @staticmethod
    def calculate_repair(
        *,
        estimate: Decimal | None = None,
        override_amount: Decimal | None = None,
    ) -> Decimal:
        amount = override_amount if override_amount is not None else estimate
        if amount is None:
            return Decimal("0")
        return AutomotiveCostEngineV1._quantize(amount)

    @staticmethod
    def calculate_margin(
        subtotal: Decimal,
        *,
        rule_type: str = MarginRuleType.PERCENT.value,
        margin_percent: Decimal | None = None,
        margin_fixed: Decimal | None = None,
    ) -> Decimal:
        if rule_type == MarginRuleType.FIXED.value:
            if margin_fixed is None:
                raise AutomotiveCostEngineError("margin_fixed required for FIXED rule")
            return AutomotiveCostEngineV1._quantize(margin_fixed)

        percent = margin_percent if margin_percent is not None else Decimal("0.08")
        return AutomotiveCostEngineV1._quantize(subtotal * percent)

    @staticmethod
    def _vehicle_cost_snapshot(cost) -> dict[str, Any]:
        return {
            "id": str(cost.id),
            "vehicle_id": str(cost.vehicle_id),
            "currency": cost.currency,
            "status": cost.status,
            "purchase_amount": str(cost.purchase_amount),
            "subtotal_amount": str(cost.subtotal_amount),
            "margin_amount": str(cost.margin_amount),
            "total_amount": str(cost.total_amount),
            "notes": cost.notes,
            "created_at": cost.created_at.isoformat(),
            "updated_at": cost.updated_at.isoformat(),
        }

    @staticmethod
    def _cost_item_snapshot(item) -> dict[str, Any]:
        return {
            "id": str(item.id),
            "item_type": item.item_type,
            "label": item.label,
            "amount": str(item.amount),
            "currency": item.currency,
            "is_calculated": item.is_calculated,
            "calculation_method": item.calculation_method,
        }

    @staticmethod
    def _margin_rule_snapshot(rule) -> dict[str, Any]:
        return {
            "id": str(rule.id),
            "name": rule.name,
            "rule_type": rule.rule_type,
            "margin_percent": str(rule.margin_percent) if rule.margin_percent else None,
            "margin_fixed": str(rule.margin_fixed) if rule.margin_fixed else None,
            "min_base_amount": str(rule.min_base_amount) if rule.min_base_amount else None,
            "max_base_amount": str(rule.max_base_amount) if rule.max_base_amount else None,
            "is_active": rule.is_active,
            "priority": rule.priority,
        }

    @staticmethod
    async def create_margin_rule(
        actor_id: int,
        *,
        name: str,
        rule_type: str,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveCostEngineV1.user_can_access(actor_id):
            raise AutomotiveCostEngineError("Access denied")

        async with get_session() as session:
            rule = await MarginRuleRepository(session).create(
                name=name,
                rule_type=rule_type,
                **fields,
            )
            return AutomotiveCostEngineV1._margin_rule_snapshot(rule)

    @staticmethod
    async def calculate_vehicle_costs(
        actor_id: int,
        vehicle_id: uuid.UUID,
        *,
        purchase_amount: Decimal,
        currency: str = "USD",
        auction_fee: Decimal | None = None,
        logistics_route: str = LogisticsRoute.USA_ODESSA.value,
        logistics_amount: Decimal | None = None,
        repair_amount: Decimal | None = None,
        customs_rate: Decimal | None = None,
        customs_amount: Decimal | None = None,
        margin_rule_id: uuid.UUID | None = None,
        margin_amount: Decimal | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveCostEngineV1.user_can_access(actor_id):
            raise AutomotiveCostEngineError("Access denied")

        purchase = AutomotiveCostEngineV1._quantize(purchase_amount)
        auction = (
            AutomotiveCostEngineV1._quantize(auction_fee)
            if auction_fee is not None
            else AutomotiveCostEngineV1._quantize(purchase * DEFAULT_AUCTION_FEE_RATE)
        )
        logistics = AutomotiveCostEngineV1.calculate_logistics(
            logistics_route,
            override_amount=logistics_amount,
        )
        cif_base = purchase + auction + logistics
        customs = AutomotiveCostEngineV1.calculate_customs(
            cif_base,
            rate_percent=customs_rate,
            override_amount=customs_amount,
        )
        repair = AutomotiveCostEngineV1.calculate_repair(
            estimate=repair_amount,
        )
        subtotal = purchase + auction + logistics + customs + repair

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveCostEngineError(f"Vehicle not found: {vehicle_id}")

            margin_repo = MarginRuleRepository(session)
            if margin_amount is not None:
                margin = AutomotiveCostEngineV1._quantize(margin_amount)
                margin_method = "MANUAL"
            elif margin_rule_id is not None:
                rule = await margin_repo.get_by_id(margin_rule_id)
                if rule is None:
                    raise AutomotiveCostEngineError(f"Margin rule not found: {margin_rule_id}")
                margin = AutomotiveCostEngineV1.calculate_margin(
                    subtotal,
                    rule_type=rule.rule_type,
                    margin_percent=rule.margin_percent,
                    margin_fixed=rule.margin_fixed,
                )
                margin_method = f"RULE:{rule.name}"
            else:
                rule = await margin_repo.find_applicable(subtotal)
                if rule is not None:
                    margin = AutomotiveCostEngineV1.calculate_margin(
                        subtotal,
                        rule_type=rule.rule_type,
                        margin_percent=rule.margin_percent,
                        margin_fixed=rule.margin_fixed,
                    )
                    margin_method = f"RULE:{rule.name}"
                else:
                    margin = AutomotiveCostEngineV1.calculate_margin(subtotal)
                    margin_method = "DEFAULT_PERCENT"

            total = subtotal + margin

            cost_repo = VehicleCostRepository(session)
            existing = await cost_repo.get_by_vehicle(vehicle_id)
            if existing is None:
                cost = await cost_repo.create(
                    vehicle_id=vehicle_id,
                    purchase_amount=purchase,
                    currency=currency,
                )
            else:
                cost = existing
                cost.purchase_amount = purchase
                cost.currency = currency

            item_repo = CostItemRepository(session)
            items_data = [
                {
                    "item_type": CostItemType.PURCHASE.value,
                    "label": "Закупка",
                    "amount": purchase,
                    "currency": currency,
                    "is_calculated": False,
                },
                {
                    "item_type": CostItemType.AUCTION_FEE.value,
                    "label": "Аукционный сбор",
                    "amount": auction,
                    "currency": currency,
                    "is_calculated": auction_fee is None,
                    "calculation_method": "PERCENT_OF_PURCHASE" if auction_fee is None else None,
                },
                {
                    "item_type": CostItemType.LOGISTICS.value,
                    "label": f"Доставка {logistics_route}",
                    "amount": logistics,
                    "currency": currency,
                    "is_calculated": logistics_amount is None,
                    "calculation_method": logistics_route,
                },
                {
                    "item_type": CostItemType.CUSTOMS.value,
                    "label": "Таможня",
                    "amount": customs,
                    "currency": currency,
                    "is_calculated": customs_amount is None,
                    "calculation_method": "PERCENT_OF_CIF",
                },
                {
                    "item_type": CostItemType.REPAIR.value,
                    "label": "Ремонт",
                    "amount": repair,
                    "currency": currency,
                    "is_calculated": False,
                },
                {
                    "item_type": CostItemType.MARGIN.value,
                    "label": "Маржа",
                    "amount": margin,
                    "currency": currency,
                    "is_calculated": margin_amount is None,
                    "calculation_method": margin_method,
                },
            ]
            items = await item_repo.replace_items(cost.id, items_data)

            cost = await cost_repo.update_totals(
                cost.id,
                subtotal_amount=subtotal,
                margin_amount=margin,
                total_amount=total,
            )

            return {
                "cost": AutomotiveCostEngineV1._vehicle_cost_snapshot(cost),
                "items": [
                    AutomotiveCostEngineV1._cost_item_snapshot(i) for i in items
                ],
            }

    @staticmethod
    async def get_vehicle_costs(
        actor_id: int,
        vehicle_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveCostEngineV1.user_can_access(actor_id):
            raise AutomotiveCostEngineError("Access denied")

        async with get_session() as session:
            cost = await VehicleCostRepository(session).get_by_vehicle(vehicle_id)
            if cost is None:
                raise AutomotiveCostEngineError(f"No cost sheet for vehicle: {vehicle_id}")

            items = await CostItemRepository(session).list_by_vehicle_cost(cost.id)

            return {
                "cost": AutomotiveCostEngineV1._vehicle_cost_snapshot(cost),
                "items": [
                    AutomotiveCostEngineV1._cost_item_snapshot(i) for i in items
                ],
            }

    @staticmethod
    async def approve_vehicle_costs(
        actor_id: int,
        vehicle_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveCostEngineV1.user_can_access(actor_id):
            raise AutomotiveCostEngineError("Access denied")

        async with get_session() as session:
            cost_repo = VehicleCostRepository(session)
            cost = await cost_repo.get_by_vehicle(vehicle_id)
            if cost is None:
                raise AutomotiveCostEngineError(f"No cost sheet for vehicle: {vehicle_id}")

            cost = await cost_repo.update_status(cost.id, VehicleCostStatus.APPROVED.value)
            return AutomotiveCostEngineV1._vehicle_cost_snapshot(cost)

    @staticmethod
    async def list_margin_rules(actor_id: int) -> list[dict[str, Any]]:
        if not await AutomotiveCostEngineV1.user_can_access(actor_id):
            raise AutomotiveCostEngineError("Access denied")

        async with get_session() as session:
            rules = await MarginRuleRepository(session).list_active()
            return [AutomotiveCostEngineV1._margin_rule_snapshot(r) for r in rules]
