# Universal Deal Engine v1 — cross-vertical deals from leads.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class DealEngineV1Status(str, enum.Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


DEAL_ENGINE_V1_STATUSES = frozenset(s.value for s in DealEngineV1Status)
DEAL_ENGINE_V1_TERMINAL_STATUSES = frozenset({
    DealEngineV1Status.COMPLETED.value,
    DealEngineV1Status.CANCELLED.value,
})
DEAL_ENGINE_V1_SUPPORTED_VERTICALS = frozenset({"auto", "agro"})


class DealEngineV1Deal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "deal_engine_v1_deals"
    __table_args__ = (
        Index("ix_deal_engine_v1_lead", "lead_id"),
        Index("ix_deal_engine_v1_vertical", "vertical"),
        Index("ix_deal_engine_v1_status", "status"),
        Index("ix_deal_engine_v1_client", "client_id"),
        Index("ix_deal_engine_v1_manager", "manager_id"),
        Index("ix_deal_engine_v1_partner", "partner_id"),
        Index("ix_deal_engine_v1_created", "created_at"),
    )

    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_engine_v1_leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    vertical: Mapped[str] = mapped_column(String(50), nullable=False)

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_partner_v1_partners.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    status: Mapped[str] = mapped_column(
        String(50),
        default=DealEngineV1Status.NEW.value,
        nullable=False,
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
