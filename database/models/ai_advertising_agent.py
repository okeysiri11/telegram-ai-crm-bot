# AI Advertising Agent v1 — ad generation, targeting, budget, bids, monitoring.

from __future__ import annotations

import enum
import uuid
from decimal import Decimal
from datetime import datetime

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
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

import database.models.auto_marketing_engine  # noqa: F401


class AdvertisingCampaignStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AdvertisingActionType(str, enum.Enum):
    AD_GENERATION = "AD_GENERATION"
    AUDIENCE_TARGETING = "AUDIENCE_TARGETING"
    BUDGET_ALLOCATION = "BUDGET_ALLOCATION"
    BID_OPTIMIZATION = "BID_OPTIMIZATION"
    CAMPAIGN_MONITORING = "CAMPAIGN_MONITORING"


class AdvertisingChannel(str, enum.Enum):
    TELEGRAM = "telegram"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"


ADVERTISING_CAMPAIGN_STATUSES = frozenset(s.value for s in AdvertisingCampaignStatus)
ADVERTISING_ACTION_TYPES = frozenset(t.value for t in AdvertisingActionType)
ADVERTISING_CHANNELS = frozenset(c.value for c in AdvertisingChannel)


class AdvertisingAgentCampaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_advertising_agent_v1_campaigns"
    __table_args__ = (
        CheckConstraint("budget_total >= 0", name="ck_ai_advertising_agent_v1_budget_total"),
        CheckConstraint("budget_spent >= 0", name="ck_ai_advertising_agent_v1_budget_spent"),
        Index("ix_ai_advertising_agent_v1_campaigns_tenant", "tenant_id"),
        Index("ix_ai_advertising_agent_v1_campaigns_company", "company_id"),
        Index("ix_ai_advertising_agent_v1_campaigns_status", "status"),
        Index("ix_ai_advertising_agent_v1_campaigns_car", "car_id"),
        Index("ix_ai_advertising_agent_v1_campaigns_marketing", "marketing_campaign_id"),
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
    marketing_campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auto_marketing_engine_v1_campaigns.id", ondelete="SET NULL"),
        nullable=True,
    )
    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=AdvertisingCampaignStatus.DRAFT.value,
        nullable=False,
    )
    channels: Mapped[list] = mapped_column(JSONB, nullable=False)
    budget_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    budget_allocated: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    budget_spent: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    daily_budget: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    audience_profile: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    bid_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ad_creative: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    performance_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_monitored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AdvertisingAgentCampaign tenant={self.tenant_id} name={self.name}>"


class AdvertisingAgentAction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_advertising_agent_v1_actions"
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_ai_advertising_agent_v1_action_confidence",
        ),
        Index("ix_ai_advertising_agent_v1_actions_campaign", "campaign_id"),
        Index("ix_ai_advertising_agent_v1_actions_tenant", "tenant_id"),
        Index("ix_ai_advertising_agent_v1_actions_type", "action_type"),
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_advertising_agent_v1_campaigns.id", ondelete="CASCADE"),
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
    action_type: Mapped[str] = mapped_column(String(40), nullable=False)
    input_context: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<AdvertisingAgentAction campaign={self.campaign_id} type={self.action_type}>"
