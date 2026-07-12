# Settlement Engine v1 models — settlements, routes, steps, status history.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

import database.models.deal  # noqa: F401 — register deal_engine_deals for FK resolution


class SettlementType(str, enum.Enum):
    CASH = "CASH"
    BANK = "BANK"
    CRYPTO = "CRYPTO"
    HYBRID = "HYBRID"


class SettlementStatus(str, enum.Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SettlementStepType(str, enum.Enum):
    CASH = "CASH"
    BANK = "BANK"
    CRYPTO = "CRYPTO"
    INTERNAL = "INTERNAL"


class Settlement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "settlement_v1_settlements"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_settlement_v1_settlements_amount"),
        Index("ix_settlement_v1_settlements_deal_id", "deal_id"),
        Index("ix_settlement_v1_settlements_status", "status"),
        Index("ix_settlement_v1_settlements_settlement_type", "settlement_type"),
    )

    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_deals.id", ondelete="SET NULL"),
        nullable=True,
    )
    settlement_type: Mapped[str] = mapped_column(String(20), nullable=False)
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=SettlementStatus.CREATED.value,
        nullable=False,
    )
    reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Settlement id={self.id} type={self.settlement_type} "
            f"{self.amount} {self.asset} status={self.status}>"
        )


class SettlementRoute(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "settlement_v1_routes"
    __table_args__ = (
        Index("ix_settlement_v1_routes_settlement_id", "settlement_id"),
    )

    settlement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("settlement_v1_settlements.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    step_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<SettlementRoute id={self.id} settlement={self.settlement_id} steps={self.step_count}>"


class SettlementStep(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "settlement_v1_steps"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_settlement_v1_steps_amount"),
        Index("ix_settlement_v1_steps_route_id", "route_id"),
        Index("ix_settlement_v1_steps_status", "status"),
        Index("ix_settlement_v1_steps_step_order", "step_order"),
    )

    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("settlement_v1_routes.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(20), nullable=False)
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=SettlementStatus.CREATED.value,
        nullable=False,
    )
    source_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    destination_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<SettlementStep id={self.id} order={self.step_order} "
            f"type={self.step_type} status={self.status}>"
        )


class SettlementStatusHistory(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "settlement_v1_status_history"
    __table_args__ = (
        Index("ix_settlement_v1_status_history_settlement_id", "settlement_id"),
        Index("ix_settlement_v1_status_history_step_id", "step_id"),
    )

    settlement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("settlement_v1_settlements.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("settlement_v1_steps.id", ondelete="SET NULL"),
        nullable=True,
    )
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<SettlementStatusHistory settlement={self.settlement_id} "
            f"{self.from_status}->{self.to_status}>"
        )
