# Recommendation Engine v1 — profiles, history, feedback for personalized recommendations.

from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
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


class RecommendationType(str, enum.Enum):
    VEHICLE = "VEHICLE"
    CUSTOMER_SIMILARITY = "CUSTOMER_SIMILARITY"
    UPSELL = "UPSELL"
    CROSS_SELL = "CROSS_SELL"
    FINANCING = "FINANCING"


class RecommendationFeedbackType(str, enum.Enum):
    HELPFUL = "HELPFUL"
    NOT_HELPFUL = "NOT_HELPFUL"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PURCHASED = "PURCHASED"
    DISMISSED = "DISMISSED"


RECOMMENDATION_TYPES = frozenset(t.value for t in RecommendationType)
RECOMMENDATION_FEEDBACK_TYPES = frozenset(f.value for f in RecommendationFeedbackType)


class RecommendationProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recommendation_engine_v1_profiles"
    __table_args__ = (
        CheckConstraint(
            "budget_min IS NULL OR budget_max IS NULL OR budget_min <= budget_max",
            name="ck_recommendation_engine_v1_profiles_budget",
        ),
        Index("ix_recommendation_engine_v1_profiles_tenant", "tenant_id"),
        Index("ix_recommendation_engine_v1_profiles_company", "company_id"),
        Index("ix_recommendation_engine_v1_profiles_sales_lead", "sales_lead_id"),
        Index("ix_recommendation_engine_v1_profiles_user", "user_id"),
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
    sales_lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_sales_agent_v1_sales_leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    vehicle_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fuel_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    transmission: Mapped[str | None] = mapped_column(String(30), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    previous_interactions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    preferences: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<RecommendationProfile tenant={self.tenant_id} label={self.label}>"


class RecommendationHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recommendation_engine_v1_history"
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_recommendation_engine_v1_history_confidence",
        ),
        Index("ix_recommendation_engine_v1_history_profile", "profile_id"),
        Index("ix_recommendation_engine_v1_history_tenant", "tenant_id"),
        Index("ix_recommendation_engine_v1_history_type", "recommendation_type"),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendation_engine_v1_profiles.id", ondelete="CASCADE"),
        nullable=False,
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
    recommendation_type: Mapped[str] = mapped_column(String(40), nullable=False)
    input_context: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<RecommendationHistory profile={self.profile_id} type={self.recommendation_type}>"


class RecommendationFeedback(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recommendation_engine_v1_feedback"
    __table_args__ = (
        CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)",
            name="ck_recommendation_engine_v1_feedback_rating",
        ),
        Index("ix_recommendation_engine_v1_feedback_history", "history_id"),
        Index("ix_recommendation_engine_v1_feedback_profile", "profile_id"),
        Index("ix_recommendation_engine_v1_feedback_tenant", "tenant_id"),
        UniqueConstraint(
            "history_id",
            "created_by",
            name="uq_recommendation_engine_v1_feedback_history_user",
        ),
    )

    history_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendation_engine_v1_history.id", ondelete="CASCADE"),
        nullable=False,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendation_engine_v1_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    feedback_type: Mapped[str] = mapped_column(String(30), nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<RecommendationFeedback history={self.history_id} type={self.feedback_type}>"
