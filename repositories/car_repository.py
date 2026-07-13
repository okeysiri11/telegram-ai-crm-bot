# Car Entity Engine v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.car import CAR_STATUSES, Car, CarStatus


def _decimal(value: Decimal | float | int | None) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


class CarRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def calculate_profit(
        *,
        purchase_price: Decimal | float | int | None = None,
        delivery_cost: Decimal | float | int | None = None,
        customs_cost: Decimal | float | int | None = None,
        repair_cost: Decimal | float | int | None = None,
        advertising_cost: Decimal | float | int | None = None,
        sale_price: Decimal | float | int | None = None,
    ) -> dict[str, Decimal | None]:
        purchase = _decimal(purchase_price)
        delivery = _decimal(delivery_cost)
        customs = _decimal(customs_cost)
        repair = _decimal(repair_cost)
        advertising = _decimal(advertising_cost)
        total_cost = purchase + delivery + customs + repair + advertising
        expected_profit = None
        if sale_price is not None:
            expected_profit = _decimal(sale_price) - total_cost
        return {
            "purchase_price": purchase,
            "delivery_cost": delivery,
            "customs_cost": customs,
            "repair_cost": repair,
            "advertising_cost": advertising,
            "total_cost": total_cost,
            "sale_price": _decimal(sale_price) if sale_price is not None else None,
            "expected_profit": expected_profit,
        }

    @staticmethod
    def _apply_costs(car: Car) -> None:
        costs = CarRepository.calculate_profit(
            purchase_price=car.purchase_price,
            delivery_cost=car.delivery_cost,
            customs_cost=car.customs_cost,
            repair_cost=car.repair_cost,
            advertising_cost=car.advertising_cost,
            sale_price=car.sale_price,
        )
        car.total_cost = costs["total_cost"]
        car.expected_profit = costs["expected_profit"]

    async def create_car(
        self,
        *,
        vin: str,
        make: str,
        model: str,
        year: int,
        color: str | None = None,
        mileage: int | None = None,
        purchase_price: Decimal | float | int | None = None,
        delivery_cost: Decimal | float | int | None = None,
        customs_cost: Decimal | float | int | None = None,
        repair_cost: Decimal | float | int | None = None,
        advertising_cost: Decimal | float | int | None = None,
        sale_price: Decimal | float | int | None = None,
        manager_id: int | None = None,
        client_id: int | None = None,
        status: str = CarStatus.PURCHASED.value,
        **extra: Any,
    ) -> Car:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in CAR_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        car = Car(
            vin=vin.upper(),
            make=make,
            model=model,
            year=year,
            color=color,
            mileage=mileage,
            purchase_price=_decimal(purchase_price) if purchase_price is not None else None,
            delivery_cost=_decimal(delivery_cost) if delivery_cost is not None else None,
            customs_cost=_decimal(customs_cost) if customs_cost is not None else None,
            repair_cost=_decimal(repair_cost) if repair_cost is not None else None,
            advertising_cost=_decimal(advertising_cost) if advertising_cost is not None else None,
            sale_price=_decimal(sale_price) if sale_price is not None else None,
            manager_id=manager_id,
            client_id=client_id,
            status=status,
        )
        self._apply_costs(car)
        self._session.add(car)
        await self._session.flush()
        return car

    async def update_car(
        self,
        car_id: uuid.UUID,
        **fields: Any,
    ) -> Car | None:
        car = await self.get_car(car_id)
        if car is None:
            return None

        allowed = {
            "vin",
            "make",
            "model",
            "year",
            "color",
            "mileage",
            "purchase_price",
            "delivery_cost",
            "customs_cost",
            "repair_cost",
            "advertising_cost",
            "sale_price",
            "manager_id",
            "client_id",
            "status",
        }
        unknown = set(fields) - allowed
        if unknown:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(unknown))}")

        if "status" in fields and fields["status"] not in CAR_STATUSES:
            raise ValueError(f"Invalid status: {fields['status']}")

        decimal_fields = {
            "purchase_price",
            "delivery_cost",
            "customs_cost",
            "repair_cost",
            "advertising_cost",
            "sale_price",
        }
        for key, value in fields.items():
            if key in decimal_fields and value is not None:
                value = _decimal(value)
            if key == "vin" and value is not None:
                value = str(value).upper()
            setattr(car, key, value)

        car.updated_at = datetime.now(timezone.utc)
        self._apply_costs(car)
        await self._session.flush()
        return car

    async def get_car(self, car_id: uuid.UUID) -> Car | None:
        result = await self._session.execute(select(Car).where(Car.id == car_id))
        return result.scalar_one_or_none()

    async def get_by_vin(self, vin: str) -> Car | None:
        result = await self._session.execute(
            select(Car).where(Car.vin == vin.upper())
        )
        return result.scalar_one_or_none()

    async def list_cars(
        self,
        *,
        status: str | None = None,
        manager_id: int | None = None,
        limit: int = 100,
    ) -> list[Car]:
        query = select(Car).order_by(Car.created_at.desc()).limit(limit)
        if status is not None:
            if status not in CAR_STATUSES:
                raise ValueError(f"Invalid status: {status}")
            query = query.where(Car.status == status)
        if manager_id is not None:
            query = query.where(Car.manager_id == manager_id)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def delete_car(self, car_id: uuid.UUID) -> bool:
        car = await self.get_car(car_id)
        if car is None:
            return False
        await self._session.delete(car)
        await self._session.flush()
        return True
