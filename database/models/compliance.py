# KYC / AML Engine v1 models — partner-centric compliance.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

import database.models.partner_engine  # noqa: F401 — register partner_engine_partners


class ComplianceEntityType(str, enum.Enum):
    INDIVIDUAL = "INDIVIDUAL"
    COMPANY = "COMPANY"


class ComplianceVerificationLevel(str, enum.Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


class ComplianceKycStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ComplianceDocumentType(str, enum.Enum):
    PASSPORT = "PASSPORT"
    ID_CARD = "ID_CARD"
    DRIVER_LICENSE = "DRIVER_LICENSE"
    COMPANY_REGISTRATION = "COMPANY_REGISTRATION"
    BANK_STATEMENT = "BANK_STATEMENT"
    PROOF_OF_ADDRESS = "PROOF_OF_ADDRESS"
    TAX_DOCUMENT = "TAX_DOCUMENT"


class ComplianceDocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AmlCheckType(str, enum.Enum):
    SANCTIONS = "SANCTIONS"
    PEP = "PEP"
    WATCHLIST = "WATCHLIST"
    ADVERSE_MEDIA = "ADVERSE_MEDIA"


class AmlCheckResult(str, enum.Enum):
    CLEAR = "CLEAR"
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"


class ComplianceRiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplianceKycProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Partner KYC profile — maps to logical table kyc_profiles."""

    __tablename__ = "compliance_engine_kyc_profiles"
    __table_args__ = (
        UniqueConstraint("partner_id", name="uq_compliance_engine_kyc_profiles_partner_id"),
        Index("ix_compliance_engine_kyc_profiles_status", "status"),
        Index("ix_compliance_engine_kyc_profiles_verification_level", "verification_level"),
        Index("ix_compliance_engine_kyc_profiles_entity_type", "entity_type"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    verification_level: Mapped[str] = mapped_column(
        String(20),
        default=ComplianceVerificationLevel.L0.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=ComplianceKycStatus.NOT_STARTED.value,
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

    def __repr__(self) -> str:
        return (
            f"<ComplianceKycProfile id={self.id} partner={self.partner_id} "
            f"level={self.verification_level} status={self.status}>"
        )


class ComplianceKycDocument(UUIDPrimaryKeyMixin, Base):
    """KYC document — maps to logical table kyc_documents."""

    __tablename__ = "compliance_engine_kyc_documents"
    __table_args__ = (
        Index("ix_compliance_engine_kyc_documents_profile_id", "kyc_profile_id"),
        Index("ix_compliance_engine_kyc_documents_status", "status"),
        Index("ix_compliance_engine_kyc_documents_document_type", "document_type"),
    )

    kyc_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_engine_kyc_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issue_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ComplianceDocumentStatus.PENDING.value,
        nullable=False,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<ComplianceKycDocument id={self.id} type={self.document_type} "
            f"status={self.status}>"
        )


class ComplianceAmlCheck(UUIDPrimaryKeyMixin, Base):
    """AML screening result — maps to logical table aml_checks."""

    __tablename__ = "compliance_engine_aml_checks"
    __table_args__ = (
        Index("ix_compliance_engine_aml_checks_partner_id", "partner_id"),
        Index("ix_compliance_engine_aml_checks_check_type", "check_type"),
        Index("ix_compliance_engine_aml_checks_result", "result"),
        Index("ix_compliance_engine_aml_checks_checked_at", "checked_at"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    check_type: Mapped[str] = mapped_column(String(50), nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<ComplianceAmlCheck id={self.id} partner={self.partner_id} "
            f"type={self.check_type} result={self.result}>"
        )


class ComplianceRiskProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Partner risk profile — maps to logical table risk_profiles."""

    __tablename__ = "compliance_engine_risk_profiles"
    __table_args__ = (
        UniqueConstraint("partner_id", name="uq_compliance_engine_risk_profiles_partner_id"),
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="ck_compliance_engine_risk_profiles_score_range",
        ),
        Index("ix_compliance_engine_risk_profiles_risk_level", "risk_level"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    risk_level: Mapped[str] = mapped_column(
        String(20),
        default=ComplianceRiskLevel.LOW.value,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ComplianceRiskProfile id={self.id} partner={self.partner_id} "
            f"level={self.risk_level} score={self.risk_score}>"
        )
