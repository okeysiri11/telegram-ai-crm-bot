# Automotive Parts Warehouse Engine v1 — stock control, suppliers, reservations.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from config import OWNER_ID
from database.models.automotive_warehouse import (
    PartReservationStatus,
    StockMovementType,
    StockReferenceType,
)
from database.session import get_session
from repositories.automotive_service_repository import ServiceOrderRepository
from repositories.automotive_warehouse_repository import (
    PartRepository,
    PartReservationRepository,
    ReorderRuleRepository,
    StockMovementRepository,
    SupplierRepository,
)
from repositories.user_role_repository import UserRoleRepository

WAREHOUSE_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})


class AutomotiveWarehouseEngineError(Exception):
    pass


class AutomotiveWarehouseEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in WAREHOUSE_ROLES for role in roles)

    @staticmethod
    def _supplier_snapshot(supplier) -> dict[str, Any]:
        return {
            "id": str(supplier.id),
            "name": supplier.name,
            "contact_name": supplier.contact_name,
            "phone": supplier.phone,
            "email": supplier.email,
            "country": supplier.country,
            "is_active": supplier.is_active,
        }

    @staticmethod
    def _part_snapshot(part) -> dict[str, Any]:
        return {
            "id": str(part.id),
            "part_number": part.part_number,
            "name": part.name,
            "description": part.description,
            "supplier_id": str(part.supplier_id) if part.supplier_id else None,
            "quantity_on_hand": part.quantity_on_hand,
            "quantity_reserved": part.quantity_reserved,
            "quantity_available": part.quantity_available,
            "min_stock_level": part.min_stock_level,
            "reorder_quantity": part.reorder_quantity,
            "unit_cost": str(part.unit_cost) if part.unit_cost else None,
            "currency": part.currency,
            "location": part.location,
            "is_active": part.is_active,
        }

    @staticmethod
    def _reservation_snapshot(reservation) -> dict[str, Any]:
        return {
            "id": str(reservation.id),
            "part_id": str(reservation.part_id),
            "service_order_id": str(reservation.service_order_id),
            "quantity": reservation.quantity,
            "status": reservation.status,
            "reserved_until": (
                reservation.reserved_until.isoformat()
                if reservation.reserved_until
                else None
            ),
        }

    @staticmethod
    def _reorder_rule_snapshot(rule) -> dict[str, Any]:
        return {
            "id": str(rule.id),
            "part_id": str(rule.part_id),
            "supplier_id": str(rule.supplier_id) if rule.supplier_id else None,
            "min_quantity": rule.min_quantity,
            "reorder_quantity": rule.reorder_quantity,
            "is_active": rule.is_active,
            "priority": rule.priority,
        }

    @staticmethod
    async def create_supplier(
        actor_id: int,
        *,
        name: str,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveWarehouseEngineV1.user_can_access(actor_id):
            raise AutomotiveWarehouseEngineError("Access denied")

        async with get_session() as session:
            supplier = await SupplierRepository(session).create(name=name, **fields)
            return AutomotiveWarehouseEngineV1._supplier_snapshot(supplier)

    @staticmethod
    async def create_part(
        actor_id: int,
        *,
        part_number: str,
        name: str,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveWarehouseEngineV1.user_can_access(actor_id):
            raise AutomotiveWarehouseEngineError("Access denied")

        async with get_session() as session:
            repo = PartRepository(session)
            if await repo.get_by_part_number(part_number):
                raise AutomotiveWarehouseEngineError(
                    f"Part already exists: {part_number}"
                )

            part = await repo.create(part_number=part_number, name=name, **fields)
            return AutomotiveWarehouseEngineV1._part_snapshot(part)

    @staticmethod
    async def receive_stock(
        actor_id: int,
        part_id: uuid.UUID,
        quantity: int,
        *,
        reference_type: str = StockReferenceType.PURCHASE.value,
        reference_id: uuid.UUID | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveWarehouseEngineV1.user_can_access(actor_id):
            raise AutomotiveWarehouseEngineError("Access denied")
        if quantity <= 0:
            raise AutomotiveWarehouseEngineError("quantity must be > 0")

        async with get_session() as session:
            part_repo = PartRepository(session)
            part = await part_repo.get_by_id(part_id)
            if part is None:
                raise AutomotiveWarehouseEngineError(f"Part not found: {part_id}")

            await StockMovementRepository(session).record(
                part_id=part_id,
                movement_type=StockMovementType.IN.value,
                quantity=quantity,
                reference_type=reference_type,
                reference_id=reference_id,
                created_by=actor_id,
                notes=notes,
            )
            part = await part_repo.adjust_stock(part_id, on_hand_delta=quantity)
            return AutomotiveWarehouseEngineV1._part_snapshot(part)

    @staticmethod
    async def issue_stock(
        actor_id: int,
        part_id: uuid.UUID,
        quantity: int,
        *,
        service_order_id: uuid.UUID | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveWarehouseEngineV1.user_can_access(actor_id):
            raise AutomotiveWarehouseEngineError("Access denied")
        if quantity <= 0:
            raise AutomotiveWarehouseEngineError("quantity must be > 0")

        async with get_session() as session:
            part_repo = PartRepository(session)
            part = await part_repo.get_by_id(part_id)
            if part is None:
                raise AutomotiveWarehouseEngineError(f"Part not found: {part_id}")
            if part.quantity_available < quantity:
                raise AutomotiveWarehouseEngineError("Insufficient available stock")

            await StockMovementRepository(session).record(
                part_id=part_id,
                movement_type=StockMovementType.OUT.value,
                quantity=quantity,
                reference_type=StockReferenceType.SERVICE_ORDER.value
                if service_order_id
                else StockReferenceType.MANUAL.value,
                service_order_id=service_order_id,
                created_by=actor_id,
                notes=notes,
            )
            part = await part_repo.adjust_stock(part_id, on_hand_delta=-quantity)
            return AutomotiveWarehouseEngineV1._part_snapshot(part)

    @staticmethod
    async def reserve_for_service_order(
        actor_id: int,
        part_id: uuid.UUID,
        service_order_id: uuid.UUID,
        quantity: int,
        *,
        reserved_until: datetime | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveWarehouseEngineV1.user_can_access(actor_id):
            raise AutomotiveWarehouseEngineError("Access denied")
        if quantity <= 0:
            raise AutomotiveWarehouseEngineError("quantity must be > 0")

        async with get_session() as session:
            part_repo = PartRepository(session)
            part = await part_repo.get_by_id(part_id)
            if part is None:
                raise AutomotiveWarehouseEngineError(f"Part not found: {part_id}")

            order = await ServiceOrderRepository(session).get_by_id(service_order_id)
            if order is None:
                raise AutomotiveWarehouseEngineError(
                    f"Service order not found: {service_order_id}"
                )
            if part.quantity_available < quantity:
                raise AutomotiveWarehouseEngineError("Insufficient available stock")

            reservation = await PartReservationRepository(session).create(
                part_id=part_id,
                service_order_id=service_order_id,
                quantity=quantity,
                reserved_until=reserved_until,
                notes=notes,
            )
            await StockMovementRepository(session).record(
                part_id=part_id,
                movement_type=StockMovementType.RESERVE.value,
                quantity=quantity,
                reference_type=StockReferenceType.SERVICE_ORDER.value,
                reference_id=reservation.id,
                service_order_id=service_order_id,
                created_by=actor_id,
                notes=notes,
            )
            part = await part_repo.adjust_stock(part_id, reserved_delta=quantity)
            return {
                "reservation": AutomotiveWarehouseEngineV1._reservation_snapshot(
                    reservation
                ),
                "part": AutomotiveWarehouseEngineV1._part_snapshot(part),
            }

    @staticmethod
    async def fulfill_reservation(
        actor_id: int,
        reservation_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveWarehouseEngineV1.user_can_access(actor_id):
            raise AutomotiveWarehouseEngineError("Access denied")

        async with get_session() as session:
            res_repo = PartReservationRepository(session)
            reservation = await res_repo.get_by_id(reservation_id)
            if reservation is None:
                raise AutomotiveWarehouseEngineError(
                    f"Reservation not found: {reservation_id}"
                )
            if reservation.status != PartReservationStatus.ACTIVE.value:
                raise AutomotiveWarehouseEngineError(
                    f"Reservation is not active: {reservation.status}"
                )

            part_repo = PartRepository(session)
            await StockMovementRepository(session).record(
                part_id=reservation.part_id,
                movement_type=StockMovementType.CONSUME.value,
                quantity=reservation.quantity,
                reference_type=StockReferenceType.SERVICE_ORDER.value,
                reference_id=reservation.id,
                service_order_id=reservation.service_order_id,
                created_by=actor_id,
                notes="Reservation fulfilled",
            )
            part = await part_repo.adjust_stock(
                reservation.part_id,
                on_hand_delta=-reservation.quantity,
                reserved_delta=-reservation.quantity,
            )
            reservation = await res_repo.update_status(
                reservation_id,
                PartReservationStatus.FULFILLED.value,
            )
            return {
                "reservation": AutomotiveWarehouseEngineV1._reservation_snapshot(
                    reservation
                ),
                "part": AutomotiveWarehouseEngineV1._part_snapshot(part),
            }

    @staticmethod
    async def cancel_reservation(
        actor_id: int,
        reservation_id: uuid.UUID,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveWarehouseEngineV1.user_can_access(actor_id):
            raise AutomotiveWarehouseEngineError("Access denied")

        async with get_session() as session:
            res_repo = PartReservationRepository(session)
            reservation = await res_repo.get_by_id(reservation_id)
            if reservation is None:
                raise AutomotiveWarehouseEngineError(
                    f"Reservation not found: {reservation_id}"
                )
            if reservation.status != PartReservationStatus.ACTIVE.value:
                raise AutomotiveWarehouseEngineError(
                    f"Reservation is not active: {reservation.status}"
                )

            await StockMovementRepository(session).record(
                part_id=reservation.part_id,
                movement_type=StockMovementType.RELEASE.value,
                quantity=reservation.quantity,
                reference_type=StockReferenceType.SERVICE_ORDER.value,
                reference_id=reservation.id,
                service_order_id=reservation.service_order_id,
                created_by=actor_id,
                notes=notes or "Reservation cancelled",
            )
            part = await PartRepository(session).adjust_stock(
                reservation.part_id,
                reserved_delta=-reservation.quantity,
            )
            reservation = await res_repo.update_status(
                reservation_id,
                PartReservationStatus.CANCELLED.value,
            )
            return {
                "reservation": AutomotiveWarehouseEngineV1._reservation_snapshot(
                    reservation
                ),
                "part": AutomotiveWarehouseEngineV1._part_snapshot(part),
            }

    @staticmethod
    async def create_reorder_rule(
        actor_id: int,
        part_id: uuid.UUID,
        *,
        min_quantity: int,
        reorder_quantity: int,
        supplier_id: uuid.UUID | None = None,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveWarehouseEngineV1.user_can_access(actor_id):
            raise AutomotiveWarehouseEngineError("Access denied")

        async with get_session() as session:
            part = await PartRepository(session).get_by_id(part_id)
            if part is None:
                raise AutomotiveWarehouseEngineError(f"Part not found: {part_id}")

            if supplier_id is not None:
                supplier = await SupplierRepository(session).get_by_id(supplier_id)
                if supplier is None:
                    raise AutomotiveWarehouseEngineError(
                        f"Supplier not found: {supplier_id}"
                    )

            rule_repo = ReorderRuleRepository(session)
            existing = await rule_repo.get_by_part(part_id)
            if existing is not None:
                existing.min_quantity = min_quantity
                existing.reorder_quantity = reorder_quantity
                existing.supplier_id = supplier_id
                existing.is_active = fields.get("is_active", True)
                existing.priority = fields.get("priority", existing.priority)
                existing.updated_at = datetime.now(timezone.utc)
                await session.flush()
                rule = existing
            else:
                rule = await rule_repo.create(
                    part_id=part_id,
                    min_quantity=min_quantity,
                    reorder_quantity=reorder_quantity,
                    supplier_id=supplier_id,
                    **fields,
                )

            part.min_stock_level = min_quantity
            part.reorder_quantity = reorder_quantity
            if supplier_id is not None:
                part.supplier_id = supplier_id
            part.updated_at = datetime.now(timezone.utc)

            return AutomotiveWarehouseEngineV1._reorder_rule_snapshot(rule)

    @staticmethod
    async def check_low_stock_alerts(
        actor_id: int,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveWarehouseEngineV1.user_can_access(actor_id):
            raise AutomotiveWarehouseEngineError("Access denied")

        async with get_session() as session:
            parts = await PartRepository(session).list_low_stock()
            alerts: list[dict[str, Any]] = []
            for part in parts:
                rule = await ReorderRuleRepository(session).get_by_part(part.id)
                supplier = None
                if part.supplier_id:
                    supplier = await SupplierRepository(session).get_by_id(
                        part.supplier_id
                    )
                alerts.append({
                    "part": AutomotiveWarehouseEngineV1._part_snapshot(part),
                    "reorder_rule": (
                        AutomotiveWarehouseEngineV1._reorder_rule_snapshot(rule)
                        if rule
                        else None
                    ),
                    "supplier": (
                        AutomotiveWarehouseEngineV1._supplier_snapshot(supplier)
                        if supplier
                        else None
                    ),
                    "suggested_reorder_qty": (
                        rule.reorder_quantity if rule else part.reorder_quantity
                    ),
                })
            return alerts

    @staticmethod
    async def get_reorder_suggestions(
        actor_id: int,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveWarehouseEngineV1.user_can_access(actor_id):
            raise AutomotiveWarehouseEngineError("Access denied")

        async with get_session() as session:
            triggered = await ReorderRuleRepository(session).list_triggered()
            suggestions: list[dict[str, Any]] = []
            for rule, part in triggered:
                supplier = None
                if rule.supplier_id:
                    supplier = await SupplierRepository(session).get_by_id(
                        rule.supplier_id
                    )
                suggestions.append({
                    "part": AutomotiveWarehouseEngineV1._part_snapshot(part),
                    "reorder_rule": AutomotiveWarehouseEngineV1._reorder_rule_snapshot(
                        rule
                    ),
                    "supplier": (
                        AutomotiveWarehouseEngineV1._supplier_snapshot(supplier)
                        if supplier
                        else None
                    ),
                    "order_quantity": rule.reorder_quantity,
                })
            return suggestions

    @staticmethod
    async def get_part(
        actor_id: int,
        part_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveWarehouseEngineV1.user_can_access(actor_id):
            raise AutomotiveWarehouseEngineError("Access denied")

        async with get_session() as session:
            part = await PartRepository(session).get_by_id(part_id)
            if part is None:
                raise AutomotiveWarehouseEngineError(f"Part not found: {part_id}")

            movements = await StockMovementRepository(session).list_by_part(part_id)
            reservations = await PartReservationRepository(session).list_active_by_part(
                part_id
            )
            rule = await ReorderRuleRepository(session).get_by_part(part_id)

            return {
                "part": AutomotiveWarehouseEngineV1._part_snapshot(part),
                "reorder_rule": (
                    AutomotiveWarehouseEngineV1._reorder_rule_snapshot(rule)
                    if rule
                    else None
                ),
                "movements": [
                    {
                        "id": str(m.id),
                        "movement_type": m.movement_type,
                        "quantity": m.quantity,
                        "reference_type": m.reference_type,
                        "service_order_id": (
                            str(m.service_order_id) if m.service_order_id else None
                        ),
                        "created_at": m.created_at.isoformat(),
                    }
                    for m in movements
                ],
                "active_reservations": [
                    AutomotiveWarehouseEngineV1._reservation_snapshot(r)
                    for r in reservations
                ],
            }

    @staticmethod
    async def list_parts(
        actor_id: int,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveWarehouseEngineV1.user_can_access(actor_id):
            raise AutomotiveWarehouseEngineError("Access denied")

        async with get_session() as session:
            parts = await PartRepository(session).list_all(limit=limit)
            return [AutomotiveWarehouseEngineV1._part_snapshot(p) for p in parts]

    @staticmethod
    async def list_suppliers(
        actor_id: int,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveWarehouseEngineV1.user_can_access(actor_id):
            raise AutomotiveWarehouseEngineError("Access denied")

        async with get_session() as session:
            suppliers = await SupplierRepository(session).list_active(limit=limit)
            return [
                AutomotiveWarehouseEngineV1._supplier_snapshot(s) for s in suppliers
            ]
