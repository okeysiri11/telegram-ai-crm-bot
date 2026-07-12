# Partner Engine models — partners, contacts, wallets, limits, commissions.

from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PartnerType(str, enum.Enum):
    CLIENT = "CLIENT"
    OTC_PARTNER = "OTC_PARTNER"
    BROKER = "BROKER"
    SUPPLIER = "SUPPLIER"
    LOGISTICS = "LOGISTICS"
    INSURANCE = "INSURANCE"
    BANK = "BANK"
    LAWYER = "LAWYER"
    CUSTOMS = "CUSTOMS"
    SERVICE_CENTER = "SERVICE_CENTER"
    DEALER = "DEALER"
    INVESTOR = "INVESTOR"


class PartnerStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    BLOCKED = "BLOCKED"
    ARCHIVED = "ARCHIVED"


class PartnerRiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PartnerKycStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PartnerAmlStatus(str, enum.Enum):
    CLEAR = "CLEAR"
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"


class PartnerWalletType(str, enum.Enum):
    BANK = "BANK"
    TRC20 = "TRC20"
    ERC20 = "ERC20"
    BEP20 = "BEP20"
    CASH = "CASH"
    IBAN = "IBAN"


class PartnerCommissionType(str, enum.Enum):
    FIXED = "FIXED"
    PERCENTAGE = "PERCENTAGE"


class Partner(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "partner_engine_partners"
    __table_args__ = (
        Index("ix_partner_engine_partners_partner_type", "partner_type"),
        Index("ix_partner_engine_partners_status", "status"),
        Index("ix_partner_engine_partners_risk_level", "risk_level"),
        Index("ix_partner_engine_partners_kyc_status", "kyc_status"),
        Index("ix_partner_engine_partners_aml_status", "aml_status"),
        Index("ix_partner_engine_partners_country", "country"),
        Index("ix_partner_engine_partners_company_name", "company_name"),
    )

    partner_type: Mapped[str] = mapped_column(String(50), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        default=PartnerStatus.ACTIVE.value,
        nullable=False,
    )
    risk_level: Mapped[str] = mapped_column(
        String(20),
        default=PartnerRiskLevel.LOW.value,
        nullable=False,
    )
    kyc_status: Mapped[str] = mapped_column(
        String(30),
        default=PartnerKycStatus.NOT_STARTED.value,
        nullable=False,
    )
    aml_status: Mapped[str] = mapped_column(
        String(30),
        default=PartnerAmlStatus.CLEAR.value,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Partner id={self.id} type={self.partner_type} "
            f"company={self.company_name} status={self.status}>"
        )


class PartnerContact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "partner_engine_contacts"
    __table_args__ = (
        Index("ix_partner_engine_contacts_partner_id", "partner_id"),
        Index("ix_partner_engine_contacts_is_primary", "is_primary"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram: Mapped[str | None] = mapped_column(String(255), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<PartnerContact id={self.id} partner={self.partner_id} name={self.full_name}>"


class PartnerWallet(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "partner_engine_wallets"
    __table_args__ = (
        Index("ix_partner_engine_wallets_partner_id", "partner_id"),
        Index("ix_partner_engine_wallets_asset", "asset"),
        Index("ix_partner_engine_wallets_is_active", "is_active"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    wallet_type: Mapped[str] = mapped_column(String(50), nullable=False)
    wallet_address: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<PartnerWallet id={self.id} partner={self.partner_id} "
            f"{self.asset} {self.wallet_type}>"
        )


class PartnerLimit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "partner_engine_limits"
    __table_args__ = (
        UniqueConstraint("partner_id", name="uq_partner_engine_limits_partner_id"),
        CheckConstraint(
            "daily_limit >= 0",
            name="ck_partner_engine_limits_daily_limit",
        ),
        CheckConstraint(
            "monthly_limit >= 0",
            name="ck_partner_engine_limits_monthly_limit",
        ),
        CheckConstraint(
            "current_daily_volume >= 0",
            name="ck_partner_engine_limits_daily_volume",
        ),
        CheckConstraint(
            "current_monthly_volume >= 0",
            name="ck_partner_engine_limits_monthly_volume",
        ),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    daily_limit: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("0"),
        nullable=False,
    )
    monthly_limit: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("0"),
        nullable=False,
    )
    current_daily_volume: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("0"),
        nullable=False,
    )
    current_monthly_volume: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("0"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<PartnerLimit partner={self.partner_id} "
            f"daily={self.current_daily_volume}/{self.daily_limit}>"
        )


class PartnerCommission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "partner_engine_commissions"
    __table_args__ = (
        Index("ix_partner_engine_commissions_partner_id", "partner_id"),
        Index("ix_partner_engine_commissions_asset", "asset"),
        UniqueConstraint(
            "partner_id",
            "asset",
            "commission_type",
            name="uq_partner_engine_commissions_partner_asset_type",
        ),
        CheckConstraint("value >= 0", name="ck_partner_engine_commissions_value"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    commission_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<PartnerCommission id={self.id} partner={self.partner_id} "
            f"{self.commission_type}={self.value} {self.asset}>"
        )
