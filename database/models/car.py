# Car Entity Engine v1 — car lifecycle and cost/profit tracking.

from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CarStatus(str, enum.Enum):
    PURCHASED = "purchased"
    IN_TRANSIT = "in_transit"
    CUSTOMS = "customs"
    REPAIR = "repair"
    READY_FOR_SALE = "ready_for_sale"
    RESERVED = "reserved"
    SOLD = "sold"


CAR_STATUSES = frozenset(s.value for s in CarStatus)


class Car(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "car_engine_v1_cars"
    __table_args__ = (
        UniqueConstraint("vin", name="uq_car_engine_v1_cars_vin"),
        CheckConstraint("year >= 1900", name="ck_car_engine_v1_cars_year"),
        CheckConstraint("mileage >= 0", name="ck_car_engine_v1_cars_mileage"),
        Index("ix_car_engine_v1_cars_status", "status"),
        Index("ix_car_engine_v1_cars_manager", "manager_id"),
        Index("ix_car_engine_v1_cars_client", "client_id"),
        Index("ix_car_engine_v1_cars_make_model", "make", "model"),
    )

    vin: Mapped[str] = mapped_column(String(50), nullable=False)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    delivery_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    customs_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    repair_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    advertising_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    expected_profit: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    manager_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    client_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        default=CarStatus.PURCHASED.value,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Car id={self.id} {self.year} {self.make} {self.model} "
            f"status={self.status}>"
        )
