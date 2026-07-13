# VIN Engine v1 — decoded VIN reports, history, and auction references.

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class VinReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vin_engine_v1_vin_reports"
    __table_args__ = (
        UniqueConstraint("vin", name="uq_vin_engine_v1_vin_reports_vin"),
        Index("ix_vin_engine_v1_vin_reports_car", "car_id"),
        Index("ix_vin_engine_v1_vin_reports_valid", "is_valid"),
    )

    vin: Mapped[str] = mapped_column(String(17), nullable=False)
    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    decoded_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    vehicle_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    auction_references: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    validation_errors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<VinReport vin={self.vin} valid={self.is_valid}>"
