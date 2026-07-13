# Car Entity Engine v1 — car CRUD, cost rollup, and profit calculation.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.car import CarStatus
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.car_repository import CarRepository
from repositories.user_role_repository import UserRoleRepository

CAR_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})


class CarEngineError(Exception):
    pass


class CarEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in CAR_ROLES for role in roles)

    @staticmethod
    def _car_snapshot(car) -> dict[str, Any]:
        return {
            "id": str(car.id),
            "vin": car.vin,
            "make": car.make,
            "model": car.model,
            "year": car.year,
            "color": car.color,
            "mileage": car.mileage,
            "purchase_price": str(car.purchase_price) if car.purchase_price is not None else None,
            "delivery_cost": str(car.delivery_cost) if car.delivery_cost is not None else None,
            "customs_cost": str(car.customs_cost) if car.customs_cost is not None else None,
            "repair_cost": str(car.repair_cost) if car.repair_cost is not None else None,
            "advertising_cost": str(car.advertising_cost) if car.advertising_cost is not None else None,
            "total_cost": str(car.total_cost) if car.total_cost is not None else None,
            "sale_price": str(car.sale_price) if car.sale_price is not None else None,
            "expected_profit": str(car.expected_profit) if car.expected_profit is not None else None,
            "manager_id": car.manager_id,
            "client_id": car.client_id,
            "status": car.status,
            "created_at": car.created_at.isoformat(),
            "updated_at": car.updated_at.isoformat(),
        }

    @staticmethod
    async def create_car(
        actor_id: int,
        *,
        vin: str,
        make: str,
        model: str,
        year: int,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await CarEngineV1.user_can_access(actor_id):
            raise CarEngineError("Access denied")

        async with get_session() as session:
            repo = CarRepository(session)
            if await repo.get_by_vin(vin):
                raise CarEngineError(f"Car with VIN already exists: {vin}")

            car = await repo.create_car(
                vin=vin,
                make=make,
                model=model,
                year=year,
                manager_id=fields.pop("manager_id", actor_id),
                **fields,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="car",
                entity_id=str(car.id),
                action=AuditAction.CREATE.value,
                new_value={"vin": car.vin, "make": car.make, "model": car.model},
            )
            return CarEngineV1._car_snapshot(car)

    @staticmethod
    async def update_car(
        actor_id: int,
        car_id: uuid.UUID,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await CarEngineV1.user_can_access(actor_id):
            raise CarEngineError("Access denied")

        async with get_session() as session:
            repo = CarRepository(session)
            old = await repo.get_car(car_id)
            if old is None:
                raise CarEngineError(f"Car not found: {car_id}")

            if "vin" in fields and fields["vin"]:
                existing = await repo.get_by_vin(fields["vin"])
                if existing is not None and existing.id != car_id:
                    raise CarEngineError(f"Car with VIN already exists: {fields['vin']}")

            car = await repo.update_car(car_id, **fields)
            if car is None:
                raise CarEngineError(f"Car not found: {car_id}")

            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="car",
                entity_id=str(car.id),
                action=AuditAction.UPDATE.value,
                old_value=CarEngineV1._car_snapshot(old),
                new_value=CarEngineV1._car_snapshot(car),
            )
            return CarEngineV1._car_snapshot(car)

    @staticmethod
    async def get_car(actor_id: int, car_id: uuid.UUID) -> dict[str, Any]:
        if not await CarEngineV1.user_can_access(actor_id):
            raise CarEngineError("Access denied")

        async with get_session() as session:
            car = await CarRepository(session).get_car(car_id)
            if car is None:
                raise CarEngineError(f"Car not found: {car_id}")
            return CarEngineV1._car_snapshot(car)

    @staticmethod
    async def list_cars(
        actor_id: int,
        *,
        status: str | None = None,
        manager_id: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not await CarEngineV1.user_can_access(actor_id):
            raise CarEngineError("Access denied")

        async with get_session() as session:
            cars = await CarRepository(session).list_cars(
                status=status,
                manager_id=manager_id,
                limit=limit,
            )
            return [CarEngineV1._car_snapshot(car) for car in cars]

    @staticmethod
    async def delete_car(actor_id: int, car_id: uuid.UUID) -> bool:
        if not await CarEngineV1.user_can_access(actor_id):
            raise CarEngineError("Access denied")

        async with get_session() as session:
            repo = CarRepository(session)
            car = await repo.get_car(car_id)
            if car is None:
                return False
            deleted = await repo.delete_car(car_id)
            if deleted:
                await AuditRepository(session).create_log(
                    user_id=actor_id,
                    entity_type="car",
                    entity_id=str(car_id),
                    action=AuditAction.DELETE.value,
                    old_value={"vin": car.vin},
                )
            return deleted

    @staticmethod
    async def calculate_profit(
        actor_id: int,
        car_id: uuid.UUID,
        *,
        sale_price: Decimal | float | int | None = None,
        persist: bool = False,
    ) -> dict[str, Any]:
        if not await CarEngineV1.user_can_access(actor_id):
            raise CarEngineError("Access denied")

        async with get_session() as session:
            repo = CarRepository(session)
            car = await repo.get_car(car_id)
            if car is None:
                raise CarEngineError(f"Car not found: {car_id}")

            effective_sale = sale_price if sale_price is not None else car.sale_price
            breakdown = repo.calculate_profit(
                purchase_price=car.purchase_price,
                delivery_cost=car.delivery_cost,
                customs_cost=car.customs_cost,
                repair_cost=car.repair_cost,
                advertising_cost=car.advertising_cost,
                sale_price=effective_sale,
            )

            if persist and sale_price is not None:
                car = await repo.update_car(car_id, sale_price=sale_price)
                if car is None:
                    raise CarEngineError(f"Car not found: {car_id}")

            return {
                "car_id": str(car_id),
                "purchase_price": str(breakdown["purchase_price"]),
                "delivery_cost": str(breakdown["delivery_cost"]),
                "customs_cost": str(breakdown["customs_cost"]),
                "repair_cost": str(breakdown["repair_cost"]),
                "advertising_cost": str(breakdown["advertising_cost"]),
                "total_cost": str(breakdown["total_cost"]),
                "sale_price": str(breakdown["sale_price"])
                if breakdown["sale_price"] is not None
                else None,
                "expected_profit": str(breakdown["expected_profit"])
                if breakdown["expected_profit"] is not None
                else None,
            }
