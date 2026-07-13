# Dealer Onboarding Flow v1 — persisted sessions and step history.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class OnboardingSessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class OnboardingStepStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class OnboardingStepName(str, enum.Enum):
    STARTED = "started"
    AUTOMOTIVE_SELECTED = "automotive_selected"
    TARIFF_SELECTED = "tariff_selected"
    PRICING_MODEL_SELECTED = "pricing_model_selected"
    PAYMENT_CREATED = "payment_created"
    RECEIPT_UPLOADED = "receipt_uploaded"
    OWNER_APPROVED = "owner_approved"
    TENANT_CREATED = "tenant_created"
    ROLE_ASSIGNED = "role_assigned"
    COMPLETED = "completed"


ONBOARDING_STEP_NAMES = frozenset(step.value for step in OnboardingStepName)
ONBOARDING_SESSION_STATUSES = frozenset(status.value for status in OnboardingSessionStatus)
ONBOARDING_STEP_STATUSES = frozenset(status.value for status in OnboardingStepStatus)


class OnboardingSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "onboarding_sessions"
    __table_args__ = (
        Index("ix_onboarding_sessions_user", "telegram_user_id"),
        Index("ix_onboarding_sessions_status", "status"),
        Index("ix_onboarding_sessions_current_step", "current_step"),
        Index("ix_onboarding_sessions_expires_at", "expires_at"),
    )

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=OnboardingSessionStatus.ACTIVE.value,
    )
    current_step: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=OnboardingStepName.STARTED.value,
    )
    plan_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pricing_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("commercial_billing_engine_v1_payments.id", ondelete="SET NULL"),
        nullable=True,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<OnboardingSession id={self.id} user={self.telegram_user_id} "
            f"step={self.current_step} status={self.status}>"
        )


class OnboardingStep(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "onboarding_steps"
    __table_args__ = (
        Index("ix_onboarding_steps_session", "session_id"),
        Index("ix_onboarding_steps_name", "step_name"),
        Index("ix_onboarding_steps_session_name", "session_id", "step_name"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("onboarding_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=OnboardingStepStatus.COMPLETED.value,
    )
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<OnboardingStep session={self.session_id} step={self.step_name}>"
