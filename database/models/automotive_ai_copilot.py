# Automotive AI Copilot v1 — recommendations, predictions, decisions, feedback.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

import database.models.automotive_inventory  # noqa: F401


class RecommendationType(str, enum.Enum):
    PURCHASE_PRICE = "PURCHASE_PRICE"
    SALE_PRICE = "SALE_PRICE"
    LIQUIDATION_DISCOUNT = "LIQUIDATION_DISCOUNT"
    SLOW_MOVING_INVENTORY = "SLOW_MOVING_INVENTORY"
    RISKY_SUPPLIER = "RISKY_SUPPLIER"
    PROFITABLE_REGION = "PROFITABLE_REGION"
    ABNORMAL_COST = "ABNORMAL_COST"


class PredictionType(str, enum.Enum):
    SALE_PROBABILITY = "SALE_PROBABILITY"
    HOLDING_PERIOD = "HOLDING_PERIOD"
    EXPECTED_MARGIN = "EXPECTED_MARGIN"


class DecisionStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"


class FeedbackRating(str, enum.Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class AiRecommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_ai_copilot_v1_ai_recommendations"
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_automotive_ai_copilot_v1_rec_confidence",
        ),
        Index("ix_automotive_ai_copilot_v1_rec_type", "recommendation_type"),
        Index("ix_automotive_ai_copilot_v1_rec_vehicle", "vehicle_id"),
        Index("ix_automotive_ai_copilot_v1_rec_model", "model_version"),
    )

    recommendation_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    input_context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AiRecommendation type={self.recommendation_type} "
            f"confidence={self.confidence_score}>"
        )


class AiPrediction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_ai_copilot_v1_ai_predictions"
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_automotive_ai_copilot_v1_pred_confidence",
        ),
        Index("ix_automotive_ai_copilot_v1_pred_type", "prediction_type"),
        Index("ix_automotive_ai_copilot_v1_pred_vehicle", "vehicle_id"),
        Index("ix_automotive_ai_copilot_v1_pred_model", "model_version"),
    )

    prediction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    predicted_value: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AiPrediction type={self.prediction_type} "
            f"value={self.predicted_value}>"
        )


class AiDecision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_ai_copilot_v1_ai_decisions"
    __table_args__ = (
        Index("ix_automotive_ai_copilot_v1_dec_status", "status"),
        Index("ix_automotive_ai_copilot_v1_dec_vehicle", "vehicle_id"),
    )

    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_ai_copilot_v1_ai_recommendations.id", ondelete="SET NULL"),
        nullable=True,
    )
    prediction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_ai_copilot_v1_ai_predictions.id", ondelete="SET NULL"),
        nullable=True,
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=DecisionStatus.PENDING.value,
        nullable=False,
    )
    decided_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    applied_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AiDecision type={self.decision_type} status={self.status}>"


class AiFeedback(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "automotive_ai_copilot_v1_ai_feedback"
    __table_args__ = (
        Index("ix_automotive_ai_copilot_v1_fb_recommendation", "recommendation_id"),
        Index("ix_automotive_ai_copilot_v1_fb_decision", "decision_id"),
        Index("ix_automotive_ai_copilot_v1_fb_model", "model_version"),
    )

    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_ai_copilot_v1_ai_recommendations.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_ai_copilot_v1_ai_decisions.id", ondelete="SET NULL"),
        nullable=True,
    )
    rating: Mapped[str] = mapped_column(String(10), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    def __repr__(self) -> str:
        return f"<AiFeedback rating={self.rating}>"
