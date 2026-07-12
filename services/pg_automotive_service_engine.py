# Automotive Service Engine v1 — service orders, labor, parts, warranty.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from config import OWNER_ID
from database.models.automotive_service import (
    OperationType,
    ServiceOperationStatus,
    ServiceOrderStatus,
    WarrantyStatus,
    WarrantyType,
)
from database.session import get_session
from repositories.automotive_inventory_repository import VehicleRepository
from repositories.automotive_service_repository import (
    ServiceHistoryRepository,
    ServiceOperationRepository,
    ServiceOrderRepository,
    ServicePartRepository,
    WarrantyRecordRepository,
)
from repositories.user_role_repository import UserRoleRepository

SERVICE_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
MONEY = Decimal("0.01")


class AutomotiveServiceEngineError(Exception):
    pass


class AutomotiveServiceEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in SERVICE_ROLES for role in roles)

    @staticmethod
    def _quantize(amount: Decimal) -> Decimal:
        return amount.quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def _order_snapshot(order) -> dict[str, Any]:
        return {
            "id": str(order.id),
            "order_number": order.order_number,
            "vehicle_id": str(order.vehicle_id),
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "status": order.status,
            "assigned_to": order.assigned_to,
            "labor_total": str(order.labor_total),
            "parts_total": str(order.parts_total),
            "total_cost": str(order.total_cost),
            "currency": order.currency,
            "diagnosis_notes": order.diagnosis_notes,
            "notes": order.notes,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
        }

    @staticmethod
    def _operation_snapshot(op) -> dict[str, Any]:
        return {
            "id": str(op.id),
            "service_order_id": str(op.service_order_id),
            "operation_type": op.operation_type,
            "description": op.description,
            "labor_hours": str(op.labor_hours),
            "labor_rate": str(op.labor_rate),
            "labor_cost": str(op.labor_cost),
            "technician_id": op.technician_id,
            "status": op.status,
            "currency": op.currency,
        }

    @staticmethod
    def _part_snapshot(part) -> dict[str, Any]:
        return {
            "id": str(part.id),
            "service_order_id": str(part.service_order_id),
            "service_operation_id": (
                str(part.service_operation_id) if part.service_operation_id else None
            ),
            "part_number": part.part_number,
            "part_name": part.part_name,
            "quantity": part.quantity,
            "unit_price": str(part.unit_price),
            "total_price": str(part.total_price),
            "currency": part.currency,
        }

    @staticmethod
    def _warranty_snapshot(record) -> dict[str, Any]:
        return {
            "id": str(record.id),
            "vehicle_id": str(record.vehicle_id),
            "service_order_id": (
                str(record.service_order_id) if record.service_order_id else None
            ),
            "warranty_type": record.warranty_type,
            "status": record.status,
            "starts_at": record.starts_at.isoformat(),
            "expires_at": record.expires_at.isoformat(),
            "mileage_limit": record.mileage_limit,
            "coverage_description": record.coverage_description,
        }

    @staticmethod
    async def calculate_service_cost(
        service_order_id: uuid.UUID,
        *,
        session=None,
    ) -> dict[str, Decimal]:
        async def _calc(active_session) -> dict[str, Decimal]:
            op_repo = ServiceOperationRepository(active_session)
            part_repo = ServicePartRepository(active_session)
            labor_total = AutomotiveServiceEngineV1._quantize(
                await op_repo.sum_labor_by_order(service_order_id)
            )
            parts_total = AutomotiveServiceEngineV1._quantize(
                await part_repo.sum_parts_by_order(service_order_id)
            )
            total_cost = AutomotiveServiceEngineV1._quantize(labor_total + parts_total)
            return {
                "labor_total": labor_total,
                "parts_total": parts_total,
                "total_cost": total_cost,
            }

        if session is not None:
            return await _calc(session)
        async with get_session() as owned_session:
            return await _calc(owned_session)

    @staticmethod
    async def create_service_order(
        actor_id: int,
        *,
        order_number: str,
        vehicle_id: uuid.UUID,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveServiceEngineV1.user_can_access(actor_id):
            raise AutomotiveServiceEngineError("Access denied")

        async with get_session() as session:
            if await ServiceOrderRepository(session).get_by_order_number(order_number):
                raise AutomotiveServiceEngineError(
                    f"Service order already exists: {order_number}"
                )

            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveServiceEngineError(f"Vehicle not found: {vehicle_id}")

            order = await ServiceOrderRepository(session).create(
                order_number=order_number,
                vehicle_id=vehicle_id,
                assigned_to=fields.pop("assigned_to", actor_id),
                **fields,
            )
            await ServiceHistoryRepository(session).record(
                service_order_id=order.id,
                to_status=order.status,
                changed_by=actor_id,
                notes="Service order created",
            )
            return AutomotiveServiceEngineV1._order_snapshot(order)

    @staticmethod
    async def update_service_status(
        actor_id: int,
        service_order_id: uuid.UUID,
        status: str,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveServiceEngineV1.user_can_access(actor_id):
            raise AutomotiveServiceEngineError("Access denied")
        if status not in {s.value for s in ServiceOrderStatus}:
            raise AutomotiveServiceEngineError(f"Invalid status: {status}")

        async with get_session() as session:
            repo = ServiceOrderRepository(session)
            order = await repo.get_by_id(service_order_id)
            if order is None:
                raise AutomotiveServiceEngineError(
                    f"Service order not found: {service_order_id}"
                )

            old_status = order.status
            order = await repo.update_status(service_order_id, status)
            await ServiceHistoryRepository(session).record(
                service_order_id=service_order_id,
                from_status=old_status,
                to_status=status,
                changed_by=actor_id,
                notes=notes,
            )
            return AutomotiveServiceEngineV1._order_snapshot(order)

    @staticmethod
    async def add_operation(
        actor_id: int,
        service_order_id: uuid.UUID,
        *,
        operation_type: str,
        description: str,
        labor_rate: Decimal,
        labor_hours: Decimal = Decimal("0"),
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveServiceEngineV1.user_can_access(actor_id):
            raise AutomotiveServiceEngineError("Access denied")
        if operation_type not in {t.value for t in OperationType}:
            raise AutomotiveServiceEngineError(f"Invalid operation_type: {operation_type}")

        async with get_session() as session:
            order = await ServiceOrderRepository(session).get_by_id(service_order_id)
            if order is None:
                raise AutomotiveServiceEngineError(
                    f"Service order not found: {service_order_id}"
                )

            operation = await ServiceOperationRepository(session).create(
                service_order_id=service_order_id,
                operation_type=operation_type,
                description=description,
                labor_rate=labor_rate,
                labor_hours=labor_hours,
                technician_id=fields.pop("technician_id", actor_id),
                **fields,
            )
            costs = await AutomotiveServiceEngineV1.calculate_service_cost(
                service_order_id,
                session=session,
            )
            await ServiceOrderRepository(session).update_costs(
                service_order_id,
                **costs,
            )
            return AutomotiveServiceEngineV1._operation_snapshot(operation)

    @staticmethod
    async def add_part(
        actor_id: int,
        service_order_id: uuid.UUID,
        *,
        part_number: str,
        part_name: str,
        unit_price: Decimal,
        quantity: int = 1,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveServiceEngineV1.user_can_access(actor_id):
            raise AutomotiveServiceEngineError("Access denied")

        async with get_session() as session:
            order = await ServiceOrderRepository(session).get_by_id(service_order_id)
            if order is None:
                raise AutomotiveServiceEngineError(
                    f"Service order not found: {service_order_id}"
                )

            part = await ServicePartRepository(session).create(
                service_order_id=service_order_id,
                part_number=part_number,
                part_name=part_name,
                unit_price=unit_price,
                quantity=quantity,
                **fields,
            )
            costs = await AutomotiveServiceEngineV1.calculate_service_cost(
                service_order_id,
                session=session,
            )
            order = await ServiceOrderRepository(session).update_costs(
                service_order_id,
                **costs,
            )

            if order.status == ServiceOrderStatus.WAITING_PARTS.value:
                old_status = order.status
                order = await ServiceOrderRepository(session).update_status(
                    service_order_id,
                    ServiceOrderStatus.IN_PROGRESS.value,
                )
                await ServiceHistoryRepository(session).record(
                    service_order_id=service_order_id,
                    from_status=old_status,
                    to_status=ServiceOrderStatus.IN_PROGRESS.value,
                    changed_by=actor_id,
                    notes="Parts received",
                )

            return AutomotiveServiceEngineV1._part_snapshot(part)

    @staticmethod
    async def recalculate_service_cost(
        actor_id: int,
        service_order_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveServiceEngineV1.user_can_access(actor_id):
            raise AutomotiveServiceEngineError("Access denied")

        async with get_session() as session:
            order = await ServiceOrderRepository(session).get_by_id(service_order_id)
            if order is None:
                raise AutomotiveServiceEngineError(
                    f"Service order not found: {service_order_id}"
                )

            costs = await AutomotiveServiceEngineV1.calculate_service_cost(
                service_order_id,
                session=session,
            )
            order = await ServiceOrderRepository(session).update_costs(
                service_order_id,
                **costs,
            )
            return AutomotiveServiceEngineV1._order_snapshot(order)

    @staticmethod
    async def create_warranty_record(
        actor_id: int,
        *,
        vehicle_id: uuid.UUID,
        warranty_type: str,
        starts_at: datetime | None = None,
        duration_days: int = 365,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveServiceEngineV1.user_can_access(actor_id):
            raise AutomotiveServiceEngineError("Access denied")
        if warranty_type not in {t.value for t in WarrantyType}:
            raise AutomotiveServiceEngineError(f"Invalid warranty_type: {warranty_type}")

        start = starts_at or datetime.now(timezone.utc)
        expires = start + timedelta(days=duration_days)

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveServiceEngineError(f"Vehicle not found: {vehicle_id}")

            record = await WarrantyRecordRepository(session).create(
                vehicle_id=vehicle_id,
                warranty_type=warranty_type,
                starts_at=start,
                expires_at=expires,
                **fields,
            )
            return AutomotiveServiceEngineV1._warranty_snapshot(record)

    @staticmethod
    async def get_service_order(
        actor_id: int,
        service_order_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveServiceEngineV1.user_can_access(actor_id):
            raise AutomotiveServiceEngineError("Access denied")

        async with get_session() as session:
            order = await ServiceOrderRepository(session).get_by_id(service_order_id)
            if order is None:
                raise AutomotiveServiceEngineError(
                    f"Service order not found: {service_order_id}"
                )

            operations = await ServiceOperationRepository(session).list_by_order(
                service_order_id
            )
            parts = await ServicePartRepository(session).list_by_order(service_order_id)
            history = await ServiceHistoryRepository(session).list_by_order(
                service_order_id
            )
            warranties = await WarrantyRecordRepository(session).list_by_vehicle(
                order.vehicle_id
            )

            return {
                "order": AutomotiveServiceEngineV1._order_snapshot(order),
                "operations": [
                    AutomotiveServiceEngineV1._operation_snapshot(o) for o in operations
                ],
                "parts": [
                    AutomotiveServiceEngineV1._part_snapshot(p) for p in parts
                ],
                "history": [
                    {
                        "from_status": h.from_status,
                        "to_status": h.to_status,
                        "created_at": h.created_at.isoformat(),
                        "notes": h.notes,
                    }
                    for h in history
                ],
                "warranties": [
                    AutomotiveServiceEngineV1._warranty_snapshot(w)
                    for w in warranties
                    if w.service_order_id == service_order_id
                    or w.service_order_id is None
                ],
            }

    @staticmethod
    async def list_service_orders(
        actor_id: int,
        *,
        status: str | None = None,
        vehicle_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveServiceEngineV1.user_can_access(actor_id):
            raise AutomotiveServiceEngineError("Access denied")

        async with get_session() as session:
            repo = ServiceOrderRepository(session)
            if vehicle_id is not None:
                orders = await repo.list_by_vehicle(vehicle_id)
            elif status:
                orders = await repo.list_by_status(status, limit=limit)
            else:
                orders = await repo.list_by_status(
                    ServiceOrderStatus.IN_PROGRESS.value,
                    limit=limit,
                )

            return [AutomotiveServiceEngineV1._order_snapshot(o) for o in orders]

    @staticmethod
    async def get_active_warranties(
        actor_id: int,
        vehicle_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveServiceEngineV1.user_can_access(actor_id):
            raise AutomotiveServiceEngineError("Access denied")

        async with get_session() as session:
            records = await WarrantyRecordRepository(session).list_active_by_vehicle(
                vehicle_id
            )
            return [AutomotiveServiceEngineV1._warranty_snapshot(r) for r in records]

    @staticmethod
    async def void_warranty(
        actor_id: int,
        warranty_id: uuid.UUID,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveServiceEngineV1.user_can_access(actor_id):
            raise AutomotiveServiceEngineError("Access denied")

        async with get_session() as session:
            record = await WarrantyRecordRepository(session).update_status(
                warranty_id,
                WarrantyStatus.VOID.value,
            )
            if record is None:
                raise AutomotiveServiceEngineError(f"Warranty not found: {warranty_id}")
            if notes:
                record.notes = notes
                record.updated_at = datetime.now(timezone.utc)
            return AutomotiveServiceEngineV1._warranty_snapshot(record)
