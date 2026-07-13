# Sales Pipeline Automation Engine v1 — stages, reminders, tasks, inactivity alerts.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class PipelineStage(str, enum.Enum):
    NEW_LEAD = "new_lead"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    INSPECTION_SCHEDULED = "inspection_scheduled"
    NEGOTIATION = "negotiation"
    RESERVED = "reserved"
    SOLD = "sold"


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    CANCELLED = "cancelled"


class FollowUpStatus(str, enum.Enum):
    OPEN = "open"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InactivityAlertStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


PIPELINE_STAGES = frozenset(s.value for s in PipelineStage)
REMINDER_STATUSES = frozenset(s.value for s in ReminderStatus)
FOLLOW_UP_STATUSES = frozenset(s.value for s in FollowUpStatus)
INACTIVITY_STATUSES = frozenset(s.value for s in InactivityAlertStatus)

STAGE_LABELS = {
    PipelineStage.NEW_LEAD.value: "New Lead",
    PipelineStage.CONTACTED.value: "Contacted",
    PipelineStage.INTERESTED.value: "Interested",
    PipelineStage.INSPECTION_SCHEDULED.value: "Inspection Scheduled",
    PipelineStage.NEGOTIATION.value: "Negotiation",
    PipelineStage.RESERVED.value: "Reserved",
    PipelineStage.SOLD.value: "Sold",
}


class PipelineLead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sales_pipeline_automation_engine_v1_pipeline_leads"
    __table_args__ = (
        Index("ix_sales_pipeline_automation_engine_v1_pl_stage", "stage"),
        Index("ix_sales_pipeline_automation_engine_v1_pl_lead", "automation_lead_id"),
        Index("ix_sales_pipeline_automation_engine_v1_pl_manager", "assigned_manager_id"),
        Index("ix_sales_pipeline_automation_engine_v1_pl_activity", "last_activity_at"),
    )

    automation_lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_automation_engine_v1_leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    stage: Mapped[str] = mapped_column(
        String(40),
        default=PipelineStage.NEW_LEAD.value,
        nullable=False,
    )
    assigned_manager_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_follow_up_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<PipelineLead id={self.id} stage={self.stage}>"


class StageTransition(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "sales_pipeline_automation_engine_v1_stage_transitions"
    __table_args__ = (
        Index("ix_sales_pipeline_automation_engine_v1_st_pl", "pipeline_lead_id"),
        Index("ix_sales_pipeline_automation_engine_v1_st_to", "to_stage"),
    )

    pipeline_lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sales_pipeline_automation_engine_v1_pipeline_leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_stage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    to_stage: Mapped[str] = mapped_column(String(40), nullable=False)
    changed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<StageTransition {self.from_stage}->{self.to_stage}>"


class PipelineReminder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sales_pipeline_automation_engine_v1_reminders"
    __table_args__ = (
        Index("ix_sales_pipeline_automation_engine_v1_rem_pl", "pipeline_lead_id"),
        Index("ix_sales_pipeline_automation_engine_v1_rem_due", "due_at"),
        Index("ix_sales_pipeline_automation_engine_v1_rem_status", "status"),
    )

    pipeline_lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sales_pipeline_automation_engine_v1_pipeline_leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    reminder_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=ReminderStatus.PENDING.value,
        nullable=False,
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<PipelineReminder type={self.reminder_type} due={self.due_at}>"


class FollowUpTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sales_pipeline_automation_engine_v1_follow_up_tasks"
    __table_args__ = (
        Index("ix_sales_pipeline_automation_engine_v1_task_pl", "pipeline_lead_id"),
        Index("ix_sales_pipeline_automation_engine_v1_task_due", "due_at"),
        Index("ix_sales_pipeline_automation_engine_v1_task_status", "status"),
    )

    pipeline_lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sales_pipeline_automation_engine_v1_pipeline_leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    assigned_to: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        default=FollowUpStatus.OPEN.value,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<FollowUpTask title={self.title} status={self.status}>"


class InactivityAlert(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sales_pipeline_automation_engine_v1_inactivity_alerts"
    __table_args__ = (
        Index("ix_sales_pipeline_automation_engine_v1_alert_pl", "pipeline_lead_id"),
        Index("ix_sales_pipeline_automation_engine_v1_alert_status", "status"),
    )

    pipeline_lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sales_pipeline_automation_engine_v1_pipeline_leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    inactive_days: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=InactivityAlertStatus.OPEN.value,
        nullable=False,
    )
    alerted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<InactivityAlert days={self.inactive_days} status={self.status}>"
