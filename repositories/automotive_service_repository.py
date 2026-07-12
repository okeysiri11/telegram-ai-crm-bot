# Automotive Service Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_service import (
    OperationType,
    ServiceOperation,
    ServiceOperationStatus,
    ServiceOrder,
    ServiceOrderStatus,
    ServicePart,
    ServiceHistory,
    WarrantyRecord,
    WarrantyStatus,
    WarrantyType,
)


class ServiceOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        order_number: str,
        vehicle_id: uuid.UUID,
        customer_name: str | None = None,
        customer_phone: str | None = None,
        assigned_to: int | None = None,
        status: str = ServiceOrderStatus.CREATED.value,
        currency: str = "USD",
        diagnosis_notes: str | None = None,
        notes: str | None = None,
        **extra: Any,
    ) -> ServiceOrder:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in {s.value for s in ServiceOrderStatus}:
            raise ValueError(f"Invalid status: {status}")

        order = ServiceOrder(
            order_number=order_number,
            vehicle_id=vehicle_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            assigned_to=assigned_to,
            status=status,
            currency=currency,
            diagnosis_notes=diagnosis_notes,
            notes=notes,
        )
        self._session.add(order)
        await self._session.flush()
        return order

    async def get_by_id(self, order_id: uuid.UUID) -> ServiceOrder | None:
        result = await self._session.execute(
            select(ServiceOrder).where(ServiceOrder.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_order_number(self, order_number: str) -> ServiceOrder | None:
        result = await self._session.execute(
            select(ServiceOrder).where(ServiceOrder.order_number == order_number)
        )
        return result.scalar_one_or_none()

    async def list_by_status(self, status: str, *, limit: int = 100) -> list[ServiceOrder]:
        result = await self._session.execute(
            select(ServiceOrder)
            .where(ServiceOrder.status == status)
            .order_by(ServiceOrder.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_vehicle(self, vehicle_id: uuid.UUID) -> list[ServiceOrder]:
        result = await self._session.execute(
            select(ServiceOrder)
            .where(ServiceOrder.vehicle_id == vehicle_id)
            .order_by(ServiceOrder.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        order_id: uuid.UUID,
        status: str,
    ) -> ServiceOrder | None:
        order = await self.get_by_id(order_id)
        if order is None:
            return None
        if status not in {s.value for s in ServiceOrderStatus}:
            raise ValueError(f"Invalid status: {status}")
        order.status = status
        order.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return order

    async def update_costs(
        self,
        order_id: uuid.UUID,
        *,
        labor_total: Decimal,
        parts_total: Decimal,
        total_cost: Decimal,
    ) -> ServiceOrder | None:
        order = await self.get_by_id(order_id)
        if order is None:
            return None
        order.labor_total = labor_total
        order.parts_total = parts_total
        order.total_cost = total_cost
        order.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return order

    async def update_fields(
        self,
        order_id: uuid.UUID,
        **fields: Any,
    ) -> ServiceOrder | None:
        order = await self.get_by_id(order_id)
        if order is None:
            return None
        allowed = {
            "customer_name", "customer_phone", "assigned_to",
            "diagnosis_notes", "notes", "currency",
        }
        for key, value in fields.items():
            if key not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(order, key, value)
        order.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return order


class ServiceOperationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        service_order_id: uuid.UUID,
        operation_type: str,
        description: str,
        labor_rate: Decimal,
        labor_hours: Decimal = Decimal("0"),
        labor_cost: Decimal | None = None,
        currency: str = "USD",
        technician_id: int | None = None,
        status: str = ServiceOperationStatus.PENDING.value,
        notes: str | None = None,
        **extra: Any,
    ) -> ServiceOperation:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if operation_type not in {t.value for t in OperationType}:
            raise ValueError(f"Invalid operation_type: {operation_type}")
        if status not in {s.value for s in ServiceOperationStatus}:
            raise ValueError(f"Invalid status: {status}")

        cost = (
            labor_cost
            if labor_cost is not None
            else (labor_hours * labor_rate).quantize(Decimal("0.01"))
        )
        operation = ServiceOperation(
            service_order_id=service_order_id,
            operation_type=operation_type,
            description=description,
            labor_hours=labor_hours,
            labor_rate=labor_rate,
            labor_cost=cost,
            currency=currency,
            technician_id=technician_id,
            status=status,
            notes=notes,
        )
        self._session.add(operation)
        await self._session.flush()
        return operation

    async def get_by_id(self, operation_id: uuid.UUID) -> ServiceOperation | None:
        result = await self._session.execute(
            select(ServiceOperation).where(ServiceOperation.id == operation_id)
        )
        return result.scalar_one_or_none()

    async def list_by_order(self, service_order_id: uuid.UUID) -> list[ServiceOperation]:
        result = await self._session.execute(
            select(ServiceOperation)
            .where(ServiceOperation.service_order_id == service_order_id)
            .order_by(ServiceOperation.created_at.asc())
        )
        return list(result.scalars().all())

    async def sum_labor_by_order(self, service_order_id: uuid.UUID) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(ServiceOperation.labor_cost), 0)).where(
                ServiceOperation.service_order_id == service_order_id
            )
        )
        return Decimal(str(result.scalar_one()))

    async def update_status(
        self,
        operation_id: uuid.UUID,
        status: str,
    ) -> ServiceOperation | None:
        operation = await self.get_by_id(operation_id)
        if operation is None:
            return None
        if status not in {s.value for s in ServiceOperationStatus}:
            raise ValueError(f"Invalid status: {status}")
        operation.status = status
        operation.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return operation


class ServicePartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        service_order_id: uuid.UUID,
        part_number: str,
        part_name: str,
        unit_price: Decimal,
        quantity: int = 1,
        service_operation_id: uuid.UUID | None = None,
        currency: str = "USD",
        notes: str | None = None,
        **extra: Any,
    ) -> ServicePart:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if quantity <= 0:
            raise ValueError("quantity must be > 0")

        total_price = (unit_price * quantity).quantize(Decimal("0.01"))
        part = ServicePart(
            service_order_id=service_order_id,
            service_operation_id=service_operation_id,
            part_number=part_number,
            part_name=part_name,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            currency=currency,
            notes=notes,
        )
        self._session.add(part)
        await self._session.flush()
        return part

    async def get_by_id(self, part_id: uuid.UUID) -> ServicePart | None:
        result = await self._session.execute(
            select(ServicePart).where(ServicePart.id == part_id)
        )
        return result.scalar_one_or_none()

    async def list_by_order(self, service_order_id: uuid.UUID) -> list[ServicePart]:
        result = await self._session.execute(
            select(ServicePart)
            .where(ServicePart.service_order_id == service_order_id)
            .order_by(ServicePart.created_at.asc())
        )
        return list(result.scalars().all())

    async def sum_parts_by_order(self, service_order_id: uuid.UUID) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(ServicePart.total_price), 0)).where(
                ServicePart.service_order_id == service_order_id
            )
        )
        return Decimal(str(result.scalar_one()))


class ServiceHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        service_order_id: uuid.UUID,
        to_status: str,
        from_status: str | None = None,
        changed_by: int | None = None,
        notes: str | None = None,
    ) -> ServiceHistory:
        if to_status not in {s.value for s in ServiceOrderStatus}:
            raise ValueError(f"Invalid status: {to_status}")

        entry = ServiceHistory(
            service_order_id=service_order_id,
            from_status=from_status,
            to_status=to_status,
            changed_by=changed_by,
            notes=notes,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_by_order(self, service_order_id: uuid.UUID) -> list[ServiceHistory]:
        result = await self._session.execute(
            select(ServiceHistory)
            .where(ServiceHistory.service_order_id == service_order_id)
            .order_by(ServiceHistory.created_at.asc())
        )
        return list(result.scalars().all())


class WarrantyRecordRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        vehicle_id: uuid.UUID,
        warranty_type: str,
        starts_at: datetime,
        expires_at: datetime,
        service_order_id: uuid.UUID | None = None,
        mileage_limit: int | None = None,
        coverage_description: str | None = None,
        status: str = WarrantyStatus.ACTIVE.value,
        notes: str | None = None,
        **extra: Any,
    ) -> WarrantyRecord:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if warranty_type not in {t.value for t in WarrantyType}:
            raise ValueError(f"Invalid warranty_type: {warranty_type}")
        if status not in {s.value for s in WarrantyStatus}:
            raise ValueError(f"Invalid status: {status}")

        record = WarrantyRecord(
            vehicle_id=vehicle_id,
            service_order_id=service_order_id,
            warranty_type=warranty_type,
            starts_at=starts_at,
            expires_at=expires_at,
            mileage_limit=mileage_limit,
            coverage_description=coverage_description,
            status=status,
            notes=notes,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_id(self, record_id: uuid.UUID) -> WarrantyRecord | None:
        result = await self._session.execute(
            select(WarrantyRecord).where(WarrantyRecord.id == record_id)
        )
        return result.scalar_one_or_none()

    async def list_by_vehicle(self, vehicle_id: uuid.UUID) -> list[WarrantyRecord]:
        result = await self._session.execute(
            select(WarrantyRecord)
            .where(WarrantyRecord.vehicle_id == vehicle_id)
            .order_by(WarrantyRecord.starts_at.desc())
        )
        return list(result.scalars().all())

    async def list_active_by_vehicle(self, vehicle_id: uuid.UUID) -> list[WarrantyRecord]:
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            select(WarrantyRecord)
            .where(
                WarrantyRecord.vehicle_id == vehicle_id,
                WarrantyRecord.status == WarrantyStatus.ACTIVE.value,
                WarrantyRecord.expires_at >= now,
            )
            .order_by(WarrantyRecord.expires_at.asc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        record_id: uuid.UUID,
        status: str,
    ) -> WarrantyRecord | None:
        record = await self.get_by_id(record_id)
        if record is None:
            return None
        if status not in {s.value for s in WarrantyStatus}:
            raise ValueError(f"Invalid status: {status}")
        record.status = status
        record.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return record
