# Risk Engine v1 models — rules, events, decisions, blocked ops, exposure limits.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

import database.models.deal  # noqa: F401 — register deal_engine_deals for FK resolution
import database.models.partner_engine  # noqa: F401 — register partner_engine_partners


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskDecisionResult(str, enum.Enum):
    APPROVED = "APPROVED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    OWNER_APPROVAL_REQUIRED = "OWNER_APPROVAL_REQUIRED"
    REJECTED = "REJECTED"


class RiskRuleType(str, enum.Enum):
    PARTNER_RISK = "PARTNER_RISK"
    TRANSACTION_RISK = "TRANSACTION_RISK"
    LIQUIDITY_RISK = "LIQUIDITY_RISK"
    CONCENTRATION_RISK = "CONCENTRATION_RISK"
    COUNTRY_RISK = "COUNTRY_RISK"
    KYC_RISK = "KYC_RISK"
    SANCTIONS_RISK = "SANCTIONS_RISK"


class RiskEvaluationType(str, enum.Enum):
    DEAL = "DEAL"
    PARTNER = "PARTNER"
    LIQUIDITY = "LIQUIDITY"


class RiskEventStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    OVERRIDDEN = "OVERRIDDEN"


class RiskExposureScope(str, enum.Enum):
    GLOBAL = "GLOBAL"
    PARTNER = "PARTNER"
    COUNTRY = "COUNTRY"
    ASSET = "ASSET"


class RiskRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "risk_v1_rules"
    __table_args__ = (
        Index("ix_risk_v1_rules_rule_type", "rule_type"),
        Index("ix_risk_v1_rules_is_active", "is_active"),
        Index("ix_risk_v1_rules_rule_code", "rule_code"),
    )

    rule_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    rule_type: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str] = mapped_column(
        String(20),
        default=RiskLevel.MEDIUM.value,
        nullable=False,
    )
    threshold: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<RiskRule code={self.rule_code} type={self.rule_type}>"


class RiskEvent(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "risk_v1_events"
    __table_args__ = (
        Index("ix_risk_v1_events_risk_level", "risk_level"),
        Index("ix_risk_v1_events_status", "status"),
        Index("ix_risk_v1_events_deal_id", "deal_id"),
        Index("ix_risk_v1_events_partner_id", "partner_id"),
        Index("ix_risk_v1_events_rule_id", "rule_id"),
    )

    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("risk_v1_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=RiskEventStatus.OPEN.value,
        nullable=False,
    )
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_deals.id", ondelete="SET NULL"),
        nullable=True,
    )
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<RiskEvent id={self.id} type={self.event_type} level={self.risk_level}>"


class RiskDecision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "risk_v1_decisions"
    __table_args__ = (
        Index("ix_risk_v1_decisions_evaluation_type", "evaluation_type"),
        Index("ix_risk_v1_decisions_decision", "decision"),
        Index("ix_risk_v1_decisions_risk_level", "risk_level"),
        Index("ix_risk_v1_decisions_deal_id", "deal_id"),
        Index("ix_risk_v1_decisions_partner_id", "partner_id"),
    )

    evaluation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_deals.id", ondelete="SET NULL"),
        nullable=True,
    )
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="SET NULL"),
        nullable=True,
    )
    asset: Mapped[str | None] = mapped_column(String(20), nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    checks: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    decided_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    override_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    overridden_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<RiskDecision id={self.id} type={self.evaluation_type} "
            f"decision={self.decision} level={self.risk_level}>"
        )


class BlockedOperation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "risk_v1_blocked_operations"
    __table_args__ = (
        Index("ix_risk_v1_blocked_operations_is_active", "is_active"),
        Index("ix_risk_v1_blocked_operations_decision_id", "decision_id"),
        Index("ix_risk_v1_blocked_operations_operation_type", "operation_type"),
    )

    decision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("risk_v1_decisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    operation_type: Mapped[str] = mapped_column(String(40), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(40), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    rule_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<BlockedOperation id={self.id} type={self.operation_type} "
            f"active={self.is_active}>"
        )


class ExposureLimit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "risk_v1_exposure_limits"
    __table_args__ = (
        CheckConstraint("max_exposure >= 0", name="ck_risk_v1_exposure_limits_max"),
        CheckConstraint(
            "current_exposure >= 0",
            name="ck_risk_v1_exposure_limits_current",
        ),
        Index("ix_risk_v1_exposure_limits_scope", "scope"),
        Index("ix_risk_v1_exposure_limits_scope_key", "scope_key"),
        Index("ix_risk_v1_exposure_limits_is_active", "is_active"),
    )

    scope: Mapped[str] = mapped_column(String(20), nullable=False)
    scope_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    asset: Mapped[str | None] = mapped_column(String(20), nullable=True)
    max_exposure: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    current_exposure: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("0"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<ExposureLimit scope={self.scope} key={self.scope_key} "
            f"{self.current_exposure}/{self.max_exposure}>"
        )
