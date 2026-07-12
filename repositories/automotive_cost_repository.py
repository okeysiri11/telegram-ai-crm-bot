# Automotive Cost Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_cost import (
    CostItem,
    CostItemType,
    MarginRule,
    MarginRuleType,
    VehicleCost,
    VehicleCostStatus,
)


class VehicleCostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        vehicle_id: uuid.UUID,
        purchase_amount: Decimal,
        currency: str = "USD",
        status: str = VehicleCostStatus.DRAFT.value,
        subtotal_amount: Decimal = Decimal("0"),
        margin_amount: Decimal = Decimal("0"),
        total_amount: Decimal = Decimal("0"),
        notes: str | None = None,
        **extra: Any,
    ) -> VehicleCost:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        cost = VehicleCost(
            vehicle_id=vehicle_id,
            purchase_amount=purchase_amount,
            currency=currency,
            status=status,
            subtotal_amount=subtotal_amount,
            margin_amount=margin_amount,
            total_amount=total_amount,
            notes=notes,
        )
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

    async def update_totals(
        self,
        cost_id: uuid.UUID,
        *,
        subtotal_amount: Decimal,
        margin_amount: Decimal,
        total_amount: Decimal,
        status: str = VehicleCostStatus.CALCULATED.value,
    ) -> VehicleCost | None:
        cost = await self.get_by_id(cost_id)
        if cost is None:
            return None
        cost.subtotal_amount = subtotal_amount
        cost.margin_amount = margin_amount
        cost.total_amount = total_amount
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


class CostItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        vehicle_cost_id: uuid.UUID,
        item_type: str,
        amount: Decimal,
        label: str | None = None,
        currency: str = "USD",
        is_calculated: bool = False,
        calculation_method: str | None = None,
        notes: str | None = None,
        **extra: Any,
    ) -> CostItem:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if item_type not in {t.value for t in CostItemType}:
            raise ValueError(f"Invalid item_type: {item_type}")

        item = CostItem(
            vehicle_cost_id=vehicle_cost_id,
            item_type=item_type,
            amount=amount,
            label=label,
            currency=currency,
            is_calculated=is_calculated,
            calculation_method=calculation_method,
            notes=notes,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def list_by_vehicle_cost(self, vehicle_cost_id: uuid.UUID) -> list[CostItem]:
        result = await self._session.execute(
            select(CostItem)
            .where(CostItem.vehicle_cost_id == vehicle_cost_id)
            .order_by(CostItem.created_at.asc())
        )
        return list(result.scalars().all())

    async def replace_items(
        self,
        vehicle_cost_id: uuid.UUID,
        items: list[dict[str, Any]],
    ) -> list[CostItem]:
        await self._session.execute(
            delete(CostItem).where(CostItem.vehicle_cost_id == vehicle_cost_id)
        )
        created: list[CostItem] = []
        for item_data in items:
            created.append(await self.create(vehicle_cost_id=vehicle_cost_id, **item_data))
        return created


class MarginRuleRepository:
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
    ) -> MarginRule:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if rule_type not in {t.value for t in MarginRuleType}:
            raise ValueError(f"Invalid rule_type: {rule_type}")

        rule = MarginRule(
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

    async def get_by_id(self, rule_id: uuid.UUID) -> MarginRule | None:
        result = await self._session.execute(
            select(MarginRule).where(MarginRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def find_applicable(
        self,
        base_amount: Decimal,
    ) -> MarginRule | None:
        result = await self._session.execute(
            select(MarginRule)
            .where(MarginRule.is_active.is_(True))
            .order_by(MarginRule.priority.desc(), MarginRule.created_at.desc())
        )
        for rule in result.scalars().all():
            if rule.min_base_amount is not None and base_amount < rule.min_base_amount:
                continue
            if rule.max_base_amount is not None and base_amount > rule.max_base_amount:
                continue
            return rule
        return None

    async def list_active(self) -> list[MarginRule]:
        result = await self._session.execute(
            select(MarginRule)
            .where(MarginRule.is_active.is_(True))
            .order_by(MarginRule.priority.desc())
        )
        return list(result.scalars().all())
