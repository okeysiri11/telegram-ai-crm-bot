# Revenue Sharing Engine v1 — partner revenue models, reports, settlements.

from __future__ import annotations

import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RevenueShareModel(str, enum.Enum):
    FIXED_SUBSCRIPTION = "FIXED_SUBSCRIPTION"
    PER_LEAD = "PER_LEAD"
    REVENUE_SHARE = "REVENUE_SHARE"
    HYBRID = "HYBRID"


REVENUE_SHARE_MODELS = frozenset(m.value for m in RevenueShareModel)


class AgreementStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    TERMINATED = "TERMINATED"


class ReportStatus(str, enum.Enum):
    GENERATED = "GENERATED"
    PUBLISHED = "PUBLISHED"


class SettlementStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"


class RevenueShareAgreement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "revenue_sharing_engine_v1_agreements"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "partner_ref",
            name="uq_revenue_sharing_engine_v1_agreements_tenant_partner",
        ),
        Index("ix_revenue_sharing_engine_v1_agreements_tenant", "tenant_id"),
        Index("ix_revenue_sharing_engine_v1_agreements_company", "company_id"),
        Index("ix_revenue_sharing_engine_v1_agreements_model", "model_type"),
        Index("ix_revenue_sharing_engine_v1_agreements_status", "status"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    partner_ref: Mapped[str] = mapped_column(String(120), nullable=False)
    partner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_type: Mapped[str] = mapped_column(String(40), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=AgreementStatus.ACTIVE.value,
        nullable=False,
    )
    terms: Mapped[dict] = mapped_column(JSONB, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<RevenueShareAgreement partner={self.partner_ref} model={self.model_type}>"


class RevenueShareCalculation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "revenue_sharing_engine_v1_calculations"
    __table_args__ = (
        UniqueConstraint(
            "agreement_id",
            "period_start",
            "period_end",
            name="uq_revenue_sharing_engine_v1_calc_agreement_period",
        ),
        CheckConstraint("total_amount >= 0", name="ck_revenue_sharing_engine_v1_calc_total"),
        Index("ix_revenue_sharing_engine_v1_calc_agreement", "agreement_id"),
        Index("ix_revenue_sharing_engine_v1_calc_period", "period_start", "period_end"),
    )

    agreement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("revenue_sharing_engine_v1_agreements.id", ondelete="CASCADE"),
        nullable=False,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    def __repr__(self) -> str:
        return f"<RevenueShareCalculation agreement={self.agreement_id} total={self.total_amount}>"


class RevenueShareReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "revenue_sharing_engine_v1_reports"
    __table_args__ = (
        UniqueConstraint(
            "agreement_id",
            "report_month",
            name="uq_revenue_sharing_engine_v1_reports_agreement_month",
        ),
        Index("ix_revenue_sharing_engine_v1_reports_agreement", "agreement_id"),
        Index("ix_revenue_sharing_engine_v1_reports_month", "report_month"),
        Index("ix_revenue_sharing_engine_v1_reports_status", "status"),
    )

    agreement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("revenue_sharing_engine_v1_agreements.id", ondelete="CASCADE"),
        nullable=False,
    )
    calculation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("revenue_sharing_engine_v1_calculations.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_month: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=ReportStatus.GENERATED.value,
        nullable=False,
    )
    summary: Mapped[dict] = mapped_column(JSONB, nullable=False)

    def __repr__(self) -> str:
        return f"<RevenueShareReport agreement={self.agreement_id} month={self.report_month}>"


class RevenueShareSettlement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "revenue_sharing_engine_v1_settlements"
    __table_args__ = (
        Index("ix_revenue_sharing_engine_v1_settlements_agreement", "agreement_id"),
        Index("ix_revenue_sharing_engine_v1_settlements_report", "report_id"),
        Index("ix_revenue_sharing_engine_v1_settlements_status", "status"),
    )

    agreement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("revenue_sharing_engine_v1_agreements.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("revenue_sharing_engine_v1_reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=SettlementStatus.PENDING.value,
        nullable=False,
    )
    reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<RevenueShareSettlement agreement={self.agreement_id} amount={self.amount}>"
