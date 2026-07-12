# Automotive Cost Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_cost import (
    CostType,
    MarginRuleType,
    VehicleCost,
    VehicleCostItem,
    VehicleCostStatus,
    VehicleMarginRule,
)


class VehicleCostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(
        self,
        vehicle_id: uuid.UUID,
        *,
        currency: str = "USD",
    ) -> VehicleCost:
        cost = await self.get_by_vehicle(vehicle_id)
        if cost is not None:
            return cost
        cost = VehicleCost(vehicle_id=vehicle_id, currency=currency)
        self._session.add(cost)
        await self._session.flush()
        return cost

    async def get_by_id(self, cost_id: uuid.UUID) -> VehicleCost | None:
        result = await self._session.execute(
            select(VehicleCost).where(VehicleCost.id == cost_id)
        )
        return result.scalar_one_or_none()

    async def get_by_vehicle(self, vehicle_id: uuid.UUID) -> VehicleCost | None:
        result = await self._session.execute(
            select(VehicleCost).where(VehicleCost.vehicle_id == vehicle_id)
        )
        return result.scalar_one_or_none()

    async def update_summary(
        self,
        cost_id: uuid.UUID,
        *,
        total_cost: Decimal,
        margin_amount: Decimal,
        target_price: Decimal,
        roi_percent: Decimal | None,
        status: str = VehicleCostStatus.CALCULATED.value,
    ) -> VehicleCost | None:
        cost = await self.get_by_id(cost_id)
        if cost is None:
            return None
        cost.total_cost = total_cost
        cost.margin_amount = margin_amount
        cost.target_price = target_price
        cost.roi_percent = roi_percent
        cost.status = status
        cost.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return cost

    async def update_status(
        self,
        cost_id: uuid.UUID,
        status: str,
    ) -> VehicleCost | None:
        cost = await self.get_by_id(cost_id)
        if cost is None:
            return None
        if status not in {s.value for s in VehicleCostStatus}:
            raise ValueError(f"Invalid status: {status}")
        cost.status = status
        cost.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return cost


class VehicleCostItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        *,
        vehicle_id: uuid.UUID,
        cost_type: str,
        amount: Decimal,
        currency: str = "USD",
        **extra: Any,
    ) -> VehicleCostItem:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if cost_type not in {t.value for t in CostType}:
            raise ValueError(f"Invalid cost_type: {cost_type}")

        item = VehicleCostItem(
            vehicle_id=vehicle_id,
            cost_type=cost_type,
            amount=amount,
            currency=currency,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def upsert_by_type(
        self,
        *,
        vehicle_id: uuid.UUID,
        cost_type: str,
        amount: Decimal,
        currency: str = "USD",
    ) -> VehicleCostItem:
        result = await self._session.execute(
            select(VehicleCostItem).where(
                VehicleCostItem.vehicle_id == vehicle_id,
                VehicleCostItem.cost_type == cost_type,
            )
        )
        item = result.scalar_one_or_none()
        if item is None:
            return await self.add(
                vehicle_id=vehicle_id,
                cost_type=cost_type,
                amount=amount,
                currency=currency,
            )
        item.amount = amount
        item.currency = currency
        await self._session.flush()
        return item

    async def list_by_vehicle(self, vehicle_id: uuid.UUID) -> list[VehicleCostItem]:
        result = await self._session.execute(
            select(VehicleCostItem)
            .where(VehicleCostItem.vehicle_id == vehicle_id)
            .order_by(VehicleCostItem.created_at.asc())
        )
        return list(result.scalars().all())

    async def sum_by_vehicle(self, vehicle_id: uuid.UUID) -> Decimal:
        items = await self.list_by_vehicle(vehicle_id)
        return sum((item.amount for item in items), Decimal("0"))

    async def replace_items(
        self,
        vehicle_id: uuid.UUID,
        items: list[dict[str, Any]],
    ) -> list[VehicleCostItem]:
        await self._session.execute(
            delete(VehicleCostItem).where(VehicleCostItem.vehicle_id == vehicle_id)
        )
        created: list[VehicleCostItem] = []
        for item_data in items:
            created.append(await self.add(vehicle_id=vehicle_id, **item_data))
        return created


class VehicleMarginRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        name: str,
        rule_type: str,
        margin_percent: Decimal | None = None,
        margin_fixed: Decimal | None = None,
        min_base_amount: Decimal | None = None,
        max_base_amount: Decimal | None = None,
        currency: str = "USD",
        is_active: bool = True,
        priority: int = 0,
        notes: str | None = None,
        **extra: Any,
    ) -> VehicleMarginRule:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if rule_type not in {t.value for t in MarginRuleType}:
            raise ValueError(f"Invalid rule_type: {rule_type}")

        rule = VehicleMarginRule(
            name=name,
            rule_type=rule_type,
            margin_percent=margin_percent,
            margin_fixed=margin_fixed,
            min_base_amount=min_base_amount,
            max_base_amount=max_base_amount,
            currency=currency,
            is_active=is_active,
            priority=priority,
            notes=notes,
        )
        self._session.add(rule)
        await self._session.flush()
        return rule

    async def get_by_id(self, rule_id: uuid.UUID) -> VehicleMarginRule | None:
        result = await self._session.execute(
            select(VehicleMarginRule).where(VehicleMarginRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def find_applicable(
        self,
        base_amount: Decimal,
    ) -> VehicleMarginRule | None:
        result = await self._session.execute(
            select(VehicleMarginRule)
            .where(VehicleMarginRule.is_active.is_(True))
            .order_by(VehicleMarginRule.priority.desc(), VehicleMarginRule.created_at.desc())
        )
        for rule in result.scalars().all():
            if rule.min_base_amount is not None and base_amount < rule.min_base_amount:
                continue
            if rule.max_base_amount is not None and base_amount > rule.max_base_amount:
                continue
            return rule
        return None

    async def list_active(self) -> list[VehicleMarginRule]:
        result = await self._session.execute(
            select(VehicleMarginRule)
            .where(VehicleMarginRule.is_active.is_(True))
            .order_by(VehicleMarginRule.priority.desc())
        )
        return list(result.scalars().all())
