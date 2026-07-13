# Dealer Portal Engine v1 — dealer dashboard, metrics, recommendations.

from __future__ import annotations

import enum
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RecommendationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISMISSED = "DISMISSED"
    APPLIED = "APPLIED"


class RecommendationPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DealerPortalSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "dealer_portal_engine_v1_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "snapshot_date",
            name="uq_dealer_portal_engine_v1_snapshots_tenant_date",
        ),
        Index("ix_dealer_portal_engine_v1_snapshots_tenant", "tenant_id"),
        Index("ix_dealer_portal_engine_v1_snapshots_date", "snapshot_date"),
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
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    widgets: Mapped[dict] = mapped_column(JSONB, nullable=False)
    sections: Mapped[dict] = mapped_column(JSONB, nullable=False)

    def __repr__(self) -> str:
        return f"<DealerPortalSnapshot tenant={self.tenant_id} date={self.snapshot_date}>"


class DealerPortalRecommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "dealer_portal_engine_v1_recommendations"
    __table_args__ = (
        Index("ix_dealer_portal_engine_v1_reco_tenant", "tenant_id"),
        Index("ix_dealer_portal_engine_v1_reco_status", "status"),
        Index("ix_dealer_portal_engine_v1_reco_priority", "priority"),
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
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(20),
        default=RecommendationPriority.MEDIUM.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=RecommendationStatus.ACTIVE.value,
        nullable=False,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<DealerPortalRecommendation tenant={self.tenant_id} title={self.title}>"
