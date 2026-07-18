# Automotive Cost Engine v1 — full vehicle cost accounting.

from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from config import OWNER_ID
from database.models.automotive_cost import CostType, MarginRuleType, VehicleCostStatus
from database.session import get_session
from repositories.automotive_cost_repository import (
    VehicleCostItemRepository,
    VehicleCostRepository,
    VehicleMarginRuleRepository,
)
from repositories.automotive_inventory_repository import VehicleRepository
from repositories.user_role_repository import UserRoleRepository

COST_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
MONEY = Decimal("0.01")
ROI_PRECISION = Decimal("0.0001")

DEFAULT_TRANSPORT_USA_ODESSA = Decimal("2200")
DEFAULT_CUSTOMS_RATE = Decimal("0.17")
DEFAULT_AUCTION_FEE_RATE = Decimal("0.0714")
DEFAULT_MARGIN_PERCENT = Decimal("0.08")


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
    async def _publish_event(
        event_type: str,
        vehicle_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> None:
        try:
            from events.crm_publisher import publish_crm_event

            await publish_crm_event(
                event_type,
                "vehicle",
                vehicle_id,
                payload,
            )
        except Exception:
            pass

    @staticmethod
    def _cost_snapshot(cost) -> dict[str, Any]:
        return {
            "id": str(cost.id),
            "vehicle_id": str(cost.vehicle_id),
            "currency": cost.currency,
            "status": cost.status,
            "total_cost": str(cost.total_cost),
            "margin_amount": str(cost.margin_amount),
            "target_price": str(cost.target_price),
            "roi_percent": str(cost.roi_percent) if cost.roi_percent is not None else None,
            "created_at": cost.created_at.isoformat(),
            "updated_at": cost.updated_at.isoformat(),
        }

    @staticmethod
    def _item_snapshot(item) -> dict[str, Any]:
        return {
            "id": str(item.id),
            "vehicle_id": str(item.vehicle_id),
            "cost_type": item.cost_type,
            "amount": str(item.amount),
            "currency": item.currency,
            "created_at": item.created_at.isoformat(),
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
    async def calculate_total_cost(
        vehicle_id: uuid.UUID,
        *,
        session=None,
    ) -> Decimal:
        if session is not None:
            return AutomotiveCostEngineV1._quantize(
                await VehicleCostItemRepository(session).sum_by_vehicle(vehicle_id)
            )

        async with get_session() as owned_session:
            return await AutomotiveCostEngineV1.calculate_total_cost(
                vehicle_id,
                session=owned_session,
            )

    @staticmethod
    def _margin_from_rule(
        total_cost: Decimal,
        *,
        rule_type: str,
        margin_percent: Decimal | None = None,
        margin_fixed: Decimal | None = None,
    ) -> Decimal:
        if rule_type == MarginRuleType.FIXED.value:
            if margin_fixed is None:
                raise AutomotiveCostEngineError("margin_fixed required for FIXED rule")
            return AutomotiveCostEngineV1._quantize(margin_fixed)

        percent = margin_percent if margin_percent is not None else DEFAULT_MARGIN_PERCENT
        return AutomotiveCostEngineV1._quantize(total_cost * percent)

    @staticmethod
    async def calculate_margin(
        vehicle_id: uuid.UUID,
        *,
        margin_rule_id: uuid.UUID | None = None,
        margin_amount: Decimal | None = None,
        session=None,
    ) -> Decimal:
        async def _calc(active_session) -> Decimal:
            total_cost = await AutomotiveCostEngineV1.calculate_total_cost(
                vehicle_id,
                session=active_session,
            )
            if margin_amount is not None:
                return AutomotiveCostEngineV1._quantize(margin_amount)

            rule_repo = VehicleMarginRuleRepository(active_session)
            rule = None
            if margin_rule_id is not None:
                rule = await rule_repo.get_by_id(margin_rule_id)
                if rule is None:
                    raise AutomotiveCostEngineError(f"Margin rule not found: {margin_rule_id}")
            else:
                rule = await rule_repo.find_applicable(total_cost)

            if rule is not None:
                return AutomotiveCostEngineV1._margin_from_rule(
                    total_cost,
                    rule_type=rule.rule_type,
                    margin_percent=rule.margin_percent,
                    margin_fixed=rule.margin_fixed,
                )
            return AutomotiveCostEngineV1._margin_from_rule(
                total_cost,
                rule_type=MarginRuleType.PERCENT.value,
            )

        if session is not None:
            return await _calc(session)
        async with get_session() as owned_session:
            return await _calc(owned_session)

    @staticmethod
    async def calculate_target_price(
        vehicle_id: uuid.UUID,
        *,
        margin_rule_id: uuid.UUID | None = None,
        margin_amount: Decimal | None = None,
        session=None,
    ) -> Decimal:
        async def _calc(active_session) -> Decimal:
            total_cost = await AutomotiveCostEngineV1.calculate_total_cost(
                vehicle_id,
                session=active_session,
            )
            margin = await AutomotiveCostEngineV1.calculate_margin(
                vehicle_id,
                margin_rule_id=margin_rule_id,
                margin_amount=margin_amount,
                session=active_session,
            )
            return AutomotiveCostEngineV1._quantize(total_cost + margin)

        if session is not None:
            return await _calc(session)
        async with get_session() as owned_session:
            return await _calc(owned_session)

    @staticmethod
    async def calculate_roi(
        vehicle_id: uuid.UUID,
        *,
        sale_price: Decimal | None = None,
        session=None,
    ) -> Decimal:
        async def _calc(active_session) -> Decimal:
            total_cost = await AutomotiveCostEngineV1.calculate_total_cost(
                vehicle_id,
                session=active_session,
            )
            if total_cost <= 0:
                return Decimal("0")

            if sale_price is None:
                vehicle = await VehicleRepository(active_session).get_by_id(vehicle_id)
                if vehicle is not None and vehicle.sale_price is not None:
                    sale_price_value = vehicle.sale_price
                else:
                    target = await AutomotiveCostEngineV1.calculate_target_price(
                        vehicle_id,
                        session=active_session,
                    )
                    sale_price_value = target
            else:
                sale_price_value = sale_price

            profit = sale_price_value - total_cost
            roi = (profit / total_cost) * Decimal("100")
            return roi.quantize(ROI_PRECISION, rounding=ROUND_HALF_UP)

        if session is not None:
            return await _calc(session)
        async with get_session() as owned_session:
            return await _calc(owned_session)

    @staticmethod
    async def add_cost_item(
        actor_id: int,
        vehicle_id: uuid.UUID,
        *,
        cost_type: str,
        amount: Decimal,
        currency: str = "USD",
    ) -> dict[str, Any]:
        if not await AutomotiveCostEngineV1.user_can_access(actor_id):
            raise AutomotiveCostEngineError("Access denied")
        if cost_type not in {t.value for t in CostType}:
            raise AutomotiveCostEngineError(f"Invalid cost_type: {cost_type}")

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveCostEngineError(f"Vehicle not found: {vehicle_id}")

            await VehicleCostRepository(session).get_or_create(
                vehicle_id,
                currency=currency,
            )
            item = await VehicleCostItemRepository(session).upsert_by_type(
                vehicle_id=vehicle_id,
                cost_type=cost_type,
                amount=AutomotiveCostEngineV1._quantize(amount),
                currency=currency,
            )
            return AutomotiveCostEngineV1._item_snapshot(item)

    @staticmethod
    async def recalculate_vehicle_costs(
        actor_id: int,
        vehicle_id: uuid.UUID,
        *,
        margin_rule_id: uuid.UUID | None = None,
        margin_amount: Decimal | None = None,
        publish_events: bool = True,
    ) -> dict[str, Any]:
        if not await AutomotiveCostEngineV1.user_can_access(actor_id):
            raise AutomotiveCostEngineError("Access denied")

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveCostEngineError(f"Vehicle not found: {vehicle_id}")

            cost_repo = VehicleCostRepository(session)
            cost = await cost_repo.get_or_create(vehicle_id, currency=vehicle.currency)

            old_total = cost.total_cost
            old_margin = cost.margin_amount

            total_cost = await AutomotiveCostEngineV1.calculate_total_cost(
                vehicle_id,
                session=session,
            )
            margin = await AutomotiveCostEngineV1.calculate_margin(
                vehicle_id,
                margin_rule_id=margin_rule_id,
                margin_amount=margin_amount,
                session=session,
            )
            target_price = AutomotiveCostEngineV1._quantize(total_cost + margin)
            roi = await AutomotiveCostEngineV1.calculate_roi(
                vehicle_id,
                sale_price=target_price,
                session=session,
            )

            cost = await cost_repo.update_summary(
                cost.id,
                total_cost=total_cost,
                margin_amount=margin,
                target_price=target_price,
                roi_percent=roi,
            )
            items = await VehicleCostItemRepository(session).list_by_vehicle(vehicle_id)

            if publish_events:
                if total_cost != old_total:
                    await AutomotiveCostEngineV1._publish_event(
                        "vehicle.cost.updated",
                        vehicle_id,
                        {
                            "vehicle_id": str(vehicle_id),
                            "total_cost": str(total_cost),
                            "currency": cost.currency,
                        },
                    )
                if margin != old_margin:
                    await AutomotiveCostEngineV1._publish_event(
                        "vehicle.margin.updated",
                        vehicle_id,
                        {
                            "vehicle_id": str(vehicle_id),
                            "margin_amount": str(margin),
                            "target_price": str(target_price),
                            "roi_percent": str(roi),
                        },
                    )

            return {
                "cost": AutomotiveCostEngineV1._cost_snapshot(cost),
                "items": [AutomotiveCostEngineV1._item_snapshot(i) for i in items],
            }

    @staticmethod
    async def build_default_cost_sheet(
        actor_id: int,
        vehicle_id: uuid.UUID,
        *,
        purchase_amount: Decimal,
        auction_fee: Decimal | None = None,
        transport_amount: Decimal | None = None,
        port_amount: Decimal | None = None,
        customs_amount: Decimal | None = None,
        repair_amount: Decimal | None = None,
        detailing_amount: Decimal | None = None,
        margin_amount: Decimal | None = None,
        currency: str = "USD",
    ) -> dict[str, Any]:
        if not await AutomotiveCostEngineV1.user_can_access(actor_id):
            raise AutomotiveCostEngineError("Access denied")

        purchase = AutomotiveCostEngineV1._quantize(purchase_amount)
        auction = (
            AutomotiveCostEngineV1._quantize(auction_fee)
            if auction_fee is not None
            else AutomotiveCostEngineV1._quantize(purchase * DEFAULT_AUCTION_FEE_RATE)
        )
        transport = (
            AutomotiveCostEngineV1._quantize(transport_amount)
            if transport_amount is not None
            else DEFAULT_TRANSPORT_USA_ODESSA
        )
        port = AutomotiveCostEngineV1._quantize(port_amount or Decimal("0"))
        cif_base = purchase + auction + transport + port
        customs = (
            AutomotiveCostEngineV1._quantize(customs_amount)
            if customs_amount is not None
            else AutomotiveCostEngineV1._quantize(cif_base * DEFAULT_CUSTOMS_RATE)
        )
        repair = AutomotiveCostEngineV1._quantize(repair_amount or Decimal("0"))
        detailing = AutomotiveCostEngineV1._quantize(detailing_amount or Decimal("0"))

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveCostEngineError(f"Vehicle not found: {vehicle_id}")

            await VehicleCostRepository(session).get_or_create(vehicle_id, currency=currency)
            item_repo = VehicleCostItemRepository(session)
            await item_repo.replace_items(
                vehicle_id,
                [
                    {"cost_type": CostType.PURCHASE.value, "amount": purchase, "currency": currency},
                    {"cost_type": CostType.AUCTION_FEE.value, "amount": auction, "currency": currency},
                    {"cost_type": CostType.TRANSPORT.value, "amount": transport, "currency": currency},
                    {"cost_type": CostType.PORT.value, "amount": port, "currency": currency},
                    {"cost_type": CostType.CUSTOMS.value, "amount": customs, "currency": currency},
                    {"cost_type": CostType.REPAIR.value, "amount": repair, "currency": currency},
                    {"cost_type": CostType.DETAILING.value, "amount": detailing, "currency": currency},
                ],
            )

        return await AutomotiveCostEngineV1.recalculate_vehicle_costs(
            actor_id,
            vehicle_id,
            margin_amount=margin_amount,
        )

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

            items = await VehicleCostItemRepository(session).list_by_vehicle(vehicle_id)
            return {
                "cost": AutomotiveCostEngineV1._cost_snapshot(cost),
                "items": [AutomotiveCostEngineV1._item_snapshot(i) for i in items],
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
            rule = await VehicleMarginRuleRepository(session).create(
                name=name,
                rule_type=rule_type,
                **fields,
            )
            return AutomotiveCostEngineV1._margin_rule_snapshot(rule)

    @staticmethod
    async def list_margin_rules(actor_id: int) -> list[dict[str, Any]]:
        if not await AutomotiveCostEngineV1.user_can_access(actor_id):
            raise AutomotiveCostEngineError("Access denied")

        async with get_session() as session:
            rules = await VehicleMarginRuleRepository(session).list_active()
            return [AutomotiveCostEngineV1._margin_rule_snapshot(r) for r in rules]

    @staticmethod
    async def approve_vehicle_costs(
        actor_id: int,
        vehicle_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveCostEngineV1.user_can_access(actor_id):
            raise AutomotiveCostEngineError("Access denied")

        async with get_session() as session:
            cost = await VehicleCostRepository(session).get_by_vehicle(vehicle_id)
            if cost is None:
                raise AutomotiveCostEngineError(f"No cost sheet for vehicle: {vehicle_id}")

            cost = await VehicleCostRepository(session).update_status(
                cost.id,
                VehicleCostStatus.APPROVED.value,
            )
            return AutomotiveCostEngineV1._cost_snapshot(cost)
