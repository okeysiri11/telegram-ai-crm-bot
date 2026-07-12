# KYC Engine models — profiles, documents, sanctions checks, risk profiles.

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class VerificationLevel(str, enum.Enum):
    NONE = "NONE"
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    ENHANCED = "ENHANCED"


class KycProfileStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"


class KycDocumentType(str, enum.Enum):
    PASSPORT = "PASSPORT"
    ID_CARD = "ID_CARD"
    DRIVERS_LICENSE = "DRIVERS_LICENSE"
    PROOF_OF_ADDRESS = "PROOF_OF_ADDRESS"
    SOURCE_OF_FUNDS = "SOURCE_OF_FUNDS"
    CORPORATE_REGISTRATION = "CORPORATE_REGISTRATION"
    OTHER = "OTHER"


class KycDocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class SanctionsCheckType(str, enum.Enum):
    OFAC = "OFAC"
    EU = "EU"
    UN = "UN"
    PEP = "PEP"
    ADVERSE_MEDIA = "ADVERSE_MEDIA"


class SanctionsCheckStatus(str, enum.Enum):
    PENDING = "PENDING"
    CLEAR = "CLEAR"
    MATCH = "MATCH"
    ERROR = "ERROR"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class KycProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "kyc_engine_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_kyc_engine_profiles_user_id"),
        Index("ix_kyc_engine_profiles_status", "status"),
        Index("ix_kyc_engine_profiles_verification_level", "verification_level"),
        Index("ix_kyc_engine_profiles_country", "country"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    country: Mapped[str | None] = mapped_column(String(3), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    verification_level: Mapped[str] = mapped_column(
        String(20),
        default=VerificationLevel.NONE.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=KycProfileStatus.PENDING.value,
        nullable=False,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<KycProfile id={self.id} user={self.user_id} "
            f"level={self.verification_level} status={self.status}>"
        )


class KycDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "kyc_engine_documents"
    __table_args__ = (
        Index("ix_kyc_engine_documents_profile_id", "profile_id"),
        Index("ix_kyc_engine_documents_status", "status"),
        Index("ix_kyc_engine_documents_expires_at", "expires_at"),
        Index("ix_kyc_engine_documents_document_type", "document_type"),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kyc_engine_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issuing_country: Mapped[str | None] = mapped_column(String(3), nullable=True)
    issued_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=KycDocumentStatus.PENDING.value,
        nullable=False,
    )
    storage_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<KycDocument id={self.id} type={self.document_type} "
            f"status={self.status} expires={self.expires_at}>"
        )


class SanctionsCheck(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "kyc_engine_sanctions_checks"
    __table_args__ = (
        Index("ix_kyc_engine_sanctions_checks_profile_id", "profile_id"),
        Index("ix_kyc_engine_sanctions_checks_status", "status"),
        Index("ix_kyc_engine_sanctions_checks_check_type", "check_type"),
        Index("ix_kyc_engine_sanctions_checks_checked_at", "checked_at"),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kyc_engine_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    check_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=SanctionsCheckStatus.PENDING.value,
        nullable=False,
    )
    match_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    matched_entities: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_check_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<SanctionsCheck id={self.id} type={self.check_type} "
            f"status={self.status} profile={self.profile_id}>"
        )


class RiskProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "kyc_engine_risk_profiles"
    __table_args__ = (
        UniqueConstraint("profile_id", name="uq_kyc_engine_risk_profiles_profile_id"),
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="ck_kyc_engine_risk_profiles_score_range",
        ),
        Index("ix_kyc_engine_risk_profiles_risk_level", "risk_level"),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kyc_engine_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    risk_level: Mapped[str] = mapped_column(
        String(20),
        default=RiskLevel.LOW.value,
        nullable=False,
    )
    aml_flags: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    pep_status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sanctions_hit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    adverse_media: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_of_funds_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<RiskProfile id={self.id} profile={self.profile_id} "
            f"level={self.risk_level} score={self.risk_score}>"
        )
