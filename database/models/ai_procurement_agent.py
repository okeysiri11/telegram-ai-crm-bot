# AI Procurement Agent v1 — market analysis, undervalued vehicles, ROI estimates.

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
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

import database.models.automotive_inventory  # noqa: F401
import database.models.automotive_procurement  # noqa: F401


class ProcurementAnalysisType(str, enum.Enum):
    MARKET_ANALYSIS = "MARKET_ANALYSIS"
    REPAIR_ESTIMATE = "REPAIR_ESTIMATE"
    SALE_PRICE_ESTIMATE = "SALE_PRICE_ESTIMATE"
    ROI_ESTIMATE = "ROI_ESTIMATE"
    FULL_EVALUATION = "FULL_EVALUATION"


class ProcurementSubjectType(str, enum.Enum):
    AUCTION_LOT = "auction_lot"
    VEHICLE = "vehicle"
    MARKET_SEGMENT = "market_segment"


class ProcurementOpportunityStatus(str, enum.Enum):
    OPEN = "OPEN"
    REVIEWED = "REVIEWED"
    DISMISSED = "DISMISSED"
    PURSUED = "PURSUED"


PROCUREMENT_ANALYSIS_TYPES = frozenset(t.value for t in ProcurementAnalysisType)
PROCUREMENT_SUBJECT_TYPES = frozenset(t.value for t in ProcurementSubjectType)
PROCUREMENT_OPPORTUNITY_STATUSES = frozenset(s.value for s in ProcurementOpportunityStatus)


class ProcurementAnalysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_procurement_agent_v1_analyses"
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_ai_procurement_agent_v1_analysis_confidence",
        ),
        Index("ix_ai_procurement_agent_v1_analyses_type", "analysis_type"),
        Index("ix_ai_procurement_agent_v1_analyses_subject", "subject_type", "subject_id"),
        Index("ix_ai_procurement_agent_v1_analyses_model", "model_version"),
        Index("ix_ai_procurement_agent_v1_analyses_actor", "created_by"),
    )

    analysis_type: Mapped[str] = mapped_column(String(40), nullable=False)
    subject_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_context: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<ProcurementAnalysis type={self.analysis_type} subject={self.subject_id}>"


class ProcurementOpportunity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_procurement_agent_v1_opportunities"
    __table_args__ = (
        CheckConstraint(
            "undervaluation_score >= 0 AND undervaluation_score <= 100",
            name="ck_ai_procurement_agent_v1_opp_score",
        ),
        CheckConstraint("discount_percent >= 0", name="ck_ai_procurement_agent_v1_opp_discount"),
        Index("ix_ai_procurement_agent_v1_opp_status", "status"),
        Index("ix_ai_procurement_agent_v1_opp_score", "undervaluation_score"),
        Index("ix_ai_procurement_agent_v1_opp_lot", "auction_lot_id"),
        Index("ix_ai_procurement_agent_v1_opp_vehicle", "vehicle_id"),
        Index("ix_ai_procurement_agent_v1_opp_make_model", "make", "model"),
    )

    auction_lot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_procurement_v1_auction_lots.id", ondelete="SET NULL"),
        nullable=True,
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_procurement_agent_v1_analyses.id", ondelete="SET NULL"),
        nullable=True,
    )
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str | None] = mapped_column(String(30), nullable=True)
    acquisition_price: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    estimated_market_value: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    undervaluation_score: Mapped[int] = mapped_column(Integer, nullable=False)
    repair_cost_estimate: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    sale_price_estimate: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    roi_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=ProcurementOpportunityStatus.OPEN.value,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ProcurementOpportunity {self.make} {self.model} "
            f"discount={self.discount_percent}% score={self.undervaluation_score}>"
        )
