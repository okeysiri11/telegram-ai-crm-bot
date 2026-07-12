# Multi Company Engine v1 — companies, branches, intercompany, consolidated reporting.

from __future__ import annotations

import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
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

import database.models.automotive_inventory  # noqa: F401


class IntercompanyTransactionType(str, enum.Enum):
    TRANSFER = "TRANSFER"
    SETTLEMENT = "SETTLEMENT"
    INVENTORY_ALLOCATION = "INVENTORY_ALLOCATION"
    EXPENSE_ALLOCATION = "EXPENSE_ALLOCATION"
    REVENUE_SHARING = "REVENUE_SHARING"


class IntercompanyTransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    SETTLED = "SETTLED"
    CANCELLED = "CANCELLED"


class ConsolidatedReportType(str, enum.Enum):
    BALANCE_SHEET = "BALANCE_SHEET"
    INCOME_STATEMENT = "INCOME_STATEMENT"
    INVENTORY = "INVENTORY"
    CASH_FLOW = "CASH_FLOW"


class ConsolidatedReportStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    PUBLISHED = "PUBLISHED"


class Company(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "multi_company_v1_companies"
    __table_args__ = (
        UniqueConstraint("code", name="uq_multi_company_v1_companies_code"),
        Index("ix_multi_company_v1_companies_is_active", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(300), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    country: Mapped[str | None] = mapped_column(String(50), nullable=True)
    accounting_prefix: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<Company code={self.code} name={self.legal_name}>"


class Branch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "multi_company_v1_branches"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "code",
            name="uq_multi_company_v1_branches_company_code",
        ),
        Index("ix_multi_company_v1_branches_company", "company_id"),
        Index("ix_multi_company_v1_branches_region", "region"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str | None] = mapped_column(String(50), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shared_inventory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Branch code={self.code} company={self.company_id}>"


class IntercompanyTransaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "multi_company_v1_intercompany_transactions"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_multi_company_v1_ict_amount"),
        Index("ix_multi_company_v1_ict_from_company", "from_company_id"),
        Index("ix_multi_company_v1_ict_to_company", "to_company_id"),
        Index("ix_multi_company_v1_ict_status", "status"),
        Index("ix_multi_company_v1_ict_reference", "reference"),
    )

    from_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    to_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    from_branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_branches.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_branches.id", ondelete="SET NULL"),
        nullable=True,
    )
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    reference: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=IntercompanyTransactionStatus.PENDING.value,
        nullable=False,
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<IntercompanyTransaction ref={self.reference} "
            f"amount={self.amount} status={self.status}>"
        )


class ConsolidatedReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "multi_company_v1_consolidated_reports"
    __table_args__ = (
        Index("ix_multi_company_v1_cr_type", "report_type"),
        Index("ix_multi_company_v1_cr_period", "period_start", "period_end"),
        Index("ix_multi_company_v1_cr_status", "status"),
    )

    report_type: Mapped[str] = mapped_column(String(30), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    companies_included: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ConsolidatedReportStatus.DRAFT.value,
        nullable=False,
    )
    generated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ConsolidatedReport type={self.report_type} "
            f"period={self.period_start}..{self.period_end}>"
        )
