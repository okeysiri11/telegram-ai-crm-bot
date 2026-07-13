# Deal Engine model — exchange / OTC deal foundation.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class DealStatus(str, enum.Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    KYC_PENDING = "KYC_PENDING"
    FUNDS_EXPECTED = "FUNDS_EXPECTED"
    FUNDS_RECEIVED = "FUNDS_RECEIVED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DISPUTE = "DISPUTE"


TERMINAL_DEAL_STATUSES = frozenset({DealStatus.COMPLETED.value, DealStatus.CANCELLED.value})


class Deal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "deal_engine_deals"
    __table_args__ = (
        Index("ix_deal_engine_deals_status", "status"),
        Index("ix_deal_engine_deals_manager_id", "manager_id"),
        Index("ix_deal_engine_deals_client_id", "client_id"),
        Index("ix_deal_engine_deals_partner_id", "partner_id"),
        Index("ix_deal_engine_deals_tenant_id", "tenant_id"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )

    client_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    manager_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    partner_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    asset_in_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    asset_in_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)

    asset_out_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    asset_out_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)

    exchange_rate: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)

    commission_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    commission_currency: Mapped[str | None] = mapped_column(String(20), nullable=True)

    status: Mapped[str] = mapped_column(
        String(50),
        default=DealStatus.NEW.value,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Deal id={self.id} status={self.status}>"
