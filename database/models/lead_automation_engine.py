# Lead Automation Engine v1 — automated lead intake, scoring, and assignment.

from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
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


class AutomationLeadSource(str, enum.Enum):
    TELEGRAM = "telegram"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    WEBSITE = "website"
    MANUAL = "manual"


class AutomationLeadStatus(str, enum.Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    QUALIFIED = "qualified"
    DUPLICATE = "duplicate"
    CONVERTED = "converted"
    CLOSED = "closed"


AUTOMATION_LEAD_SOURCES = frozenset(s.value for s in AutomationLeadSource)
AUTOMATION_LEAD_STATUSES = frozenset(s.value for s in AutomationLeadStatus)
OPEN_LEAD_STATUSES = frozenset({
    AutomationLeadStatus.NEW.value,
    AutomationLeadStatus.ASSIGNED.value,
    AutomationLeadStatus.QUALIFIED.value,
})


class AutomationLead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lead_automation_engine_v1_leads"
    __table_args__ = (
        Index("ix_lead_automation_engine_v1_leads_source", "source"),
        Index("ix_lead_automation_engine_v1_leads_status", "status"),
        Index("ix_lead_automation_engine_v1_leads_manager", "assigned_manager_id"),
        Index("ix_lead_automation_engine_v1_leads_car", "car_id"),
        Index("ix_lead_automation_engine_v1_leads_phone", "phone_normalized"),
        Index("ix_lead_automation_engine_v1_leads_email", "email_normalized"),
        Index("ix_lead_automation_engine_v1_leads_telegram", "telegram_user_id"),
        Index("ix_lead_automation_engine_v1_leads_score", "score"),
        Index("ix_lead_automation_engine_v1_leads_duplicate", "is_duplicate"),
    )

    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone_normalized: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_normalized: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_manager_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=AutomationLeadStatus.NEW.value,
        nullable=False,
    )
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_automation_engine_v1_leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    budget: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    source_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scoring_factors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AutomationLead id={self.id} name={self.customer_name} "
            f"source={self.source} score={self.score}>"
        )


class LeadSourceEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lead_automation_engine_v1_source_events"
    __table_args__ = (
        Index("ix_lead_automation_engine_v1_events_lead", "lead_id"),
        Index("ix_lead_automation_engine_v1_events_source", "source"),
        Index("ix_lead_automation_engine_v1_events_type", "event_type"),
    )

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_automation_engine_v1_leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<LeadSourceEvent lead={self.lead_id} "
            f"source={self.source} type={self.event_type}>"
        )
