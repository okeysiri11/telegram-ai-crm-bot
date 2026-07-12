# Automotive Parts Warehouse Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_warehouse import (
    Part,
    PartReservation,
    PartReservationStatus,
    ReorderRule,
    StockMovement,
    StockMovementType,
    StockReferenceType,
    Supplier,
)


class SupplierRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        name: str,
        contact_name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        country: str | None = None,
        is_active: bool = True,
        notes: str | None = None,
        **extra: Any,
    ) -> Supplier:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        supplier = Supplier(
            name=name,
            contact_name=contact_name,
            phone=phone,
            email=email,
            country=country,
            is_active=is_active,
            notes=notes,
        )
        self._session.add(supplier)
        await self._session.flush()
        return supplier

    async def get_by_id(self, supplier_id: uuid.UUID) -> Supplier | None:
        result = await self._session.execute(
            select(Supplier).where(Supplier.id == supplier_id)
        )
        return result.scalar_one_or_none()

    async def list_active(self, *, limit: int = 100) -> list[Supplier]:
        result = await self._session.execute(
            select(Supplier)
            .where(Supplier.is_active.is_(True))
            .order_by(Supplier.name.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


class PartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        part_number: str,
        name: str,
        supplier_id: uuid.UUID | None = None,
        quantity_on_hand: int = 0,
        min_stock_level: int = 0,
        reorder_quantity: int = 0,
        unit_cost: Decimal | None = None,
        currency: str = "USD",
        location: str | None = None,
        description: str | None = None,
        **extra: Any,
    ) -> Part:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if quantity_on_hand < 0:
            raise ValueError("quantity_on_hand must be >= 0")

        part = Part(
            part_number=part_number,
            name=name,
            supplier_id=supplier_id,
            quantity_on_hand=quantity_on_hand,
            min_stock_level=min_stock_level,
            reorder_quantity=reorder_quantity,
            unit_cost=unit_cost,
            currency=currency,
            location=location,
            description=description,
        )
        self._session.add(part)
        await self._session.flush()
        return part

    async def get_by_id(self, part_id: uuid.UUID) -> Part | None:
        result = await self._session.execute(
            select(Part).where(Part.id == part_id)
        )
        return result.scalar_one_or_none()

    async def get_by_part_number(self, part_number: str) -> Part | None:
        result = await self._session.execute(
            select(Part).where(Part.part_number == part_number)
        )
        return result.scalar_one_or_none()

    async def list_low_stock(self) -> list[Part]:
        result = await self._session.execute(
            select(Part)
            .where(
                Part.is_active.is_(True),
                Part.quantity_on_hand <= Part.min_stock_level,
            )
            .order_by(Part.quantity_on_hand.asc())
        )
        return list(result.scalars().all())

    async def list_all(self, *, limit: int = 100) -> list[Part]:
        result = await self._session.execute(
            select(Part)
            .where(Part.is_active.is_(True))
            .order_by(Part.part_number.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def adjust_stock(
        self,
        part_id: uuid.UUID,
        *,
        on_hand_delta: int = 0,
        reserved_delta: int = 0,
    ) -> Part | None:
        part = await self.get_by_id(part_id)
        if part is None:
            return None

        new_on_hand = part.quantity_on_hand + on_hand_delta
        new_reserved = part.quantity_reserved + reserved_delta
        if new_on_hand < 0 or new_reserved < 0:
            raise ValueError("Insufficient stock")
        if new_on_hand < new_reserved:
            raise ValueError("Reserved quantity exceeds on-hand stock")

        part.quantity_on_hand = new_on_hand
        part.quantity_reserved = new_reserved
        part.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return part


class StockMovementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        part_id: uuid.UUID,
        movement_type: str,
        quantity: int,
        reference_type: str | None = None,
        reference_id: uuid.UUID | None = None,
        service_order_id: uuid.UUID | None = None,
        created_by: int | None = None,
        notes: str | None = None,
    ) -> StockMovement:
        if movement_type not in {t.value for t in StockMovementType}:
            raise ValueError(f"Invalid movement_type: {movement_type}")
        if quantity <= 0:
            raise ValueError("quantity must be > 0")
        if reference_type is not None and reference_type not in {
            t.value for t in StockReferenceType
        }:
            raise ValueError(f"Invalid reference_type: {reference_type}")

        movement = StockMovement(
            part_id=part_id,
            movement_type=movement_type,
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            service_order_id=service_order_id,
            created_by=created_by,
            notes=notes,
        )
        self._session.add(movement)
        await self._session.flush()
        return movement

    async def list_by_part(self, part_id: uuid.UUID) -> list[StockMovement]:
        result = await self._session.execute(
            select(StockMovement)
            .where(StockMovement.part_id == part_id)
            .order_by(StockMovement.created_at.desc())
        )
        return list(result.scalars().all())


class PartReservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        part_id: uuid.UUID,
        service_order_id: uuid.UUID,
        quantity: int,
        reserved_until: datetime | None = None,
        notes: str | None = None,
        **extra: Any,
    ) -> PartReservation:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if quantity <= 0:
            raise ValueError("quantity must be > 0")

        reservation = PartReservation(
            part_id=part_id,
            service_order_id=service_order_id,
            quantity=quantity,
            reserved_until=reserved_until,
            notes=notes,
        )
        self._session.add(reservation)
        await self._session.flush()
        return reservation

    async def get_by_id(self, reservation_id: uuid.UUID) -> PartReservation | None:
        result = await self._session.execute(
            select(PartReservation).where(PartReservation.id == reservation_id)
        )
        return result.scalar_one_or_none()

    async def list_by_service_order(
        self,
        service_order_id: uuid.UUID,
    ) -> list[PartReservation]:
        result = await self._session.execute(
            select(PartReservation)
            .where(PartReservation.service_order_id == service_order_id)
            .order_by(PartReservation.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_active_by_part(self, part_id: uuid.UUID) -> list[PartReservation]:
        result = await self._session.execute(
            select(PartReservation)
            .where(
                PartReservation.part_id == part_id,
                PartReservation.status == PartReservationStatus.ACTIVE.value,
            )
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        reservation_id: uuid.UUID,
        status: str,
    ) -> PartReservation | None:
        reservation = await self.get_by_id(reservation_id)
        if reservation is None:
            return None
        if status not in {s.value for s in PartReservationStatus}:
            raise ValueError(f"Invalid status: {status}")
        reservation.status = status
        reservation.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return reservation


class ReorderRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        part_id: uuid.UUID,
        min_quantity: int,
        reorder_quantity: int,
        supplier_id: uuid.UUID | None = None,
        is_active: bool = True,
        priority: int = 0,
        notes: str | None = None,
        **extra: Any,
    ) -> ReorderRule:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if min_quantity < 0:
            raise ValueError("min_quantity must be >= 0")
        if reorder_quantity <= 0:
            raise ValueError("reorder_quantity must be > 0")

        rule = ReorderRule(
            part_id=part_id,
            supplier_id=supplier_id,
            min_quantity=min_quantity,
            reorder_quantity=reorder_quantity,
            is_active=is_active,
            priority=priority,
            notes=notes,
        )
        self._session.add(rule)
        await self._session.flush()
        return rule

    async def get_by_part(self, part_id: uuid.UUID) -> ReorderRule | None:
        result = await self._session.execute(
            select(ReorderRule).where(ReorderRule.part_id == part_id)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[ReorderRule]:
        result = await self._session.execute(
            select(ReorderRule)
            .where(ReorderRule.is_active.is_(True))
            .order_by(ReorderRule.priority.desc())
        )
        return list(result.scalars().all())

    async def list_triggered(self) -> list[tuple[ReorderRule, Part]]:
        result = await self._session.execute(
            select(ReorderRule, Part)
            .join(Part, ReorderRule.part_id == Part.id)
            .where(
                ReorderRule.is_active.is_(True),
                Part.is_active.is_(True),
                Part.quantity_on_hand <= ReorderRule.min_quantity,
            )
            .order_by(ReorderRule.priority.desc(), Part.quantity_on_hand.asc())
        )
        return list(result.all())
