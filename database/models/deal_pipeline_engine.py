# Deal Pipeline Engine v2 — stages, history, tasks, comments, SLA.

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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

import database.models.ai_sales_agent  # noqa: F401
import database.models.car  # noqa: F401


class DealPipelineStageCode(str, enum.Enum):
    NEW_LEAD = "NEW_LEAD"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    VIEWING = "VIEWING"
    NEGOTIATION = "NEGOTIATION"
    RESERVED = "RESERVED"
    DOCUMENTS = "DOCUMENTS"
    PAYMENT = "PAYMENT"
    DELIVERED = "DELIVERED"
    LOST = "LOST"


class DealTaskStatus(str, enum.Enum):
    OPEN = "OPEN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    OVERDUE = "OVERDUE"


class DealStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    WON = "WON"
    LOST = "LOST"


DEAL_PIPELINE_STAGE_CODES = frozenset(s.value for s in DealPipelineStageCode)
DEAL_TASK_STATUSES = frozenset(s.value for s in DealTaskStatus)
DEAL_STATUSES = frozenset(s.value for s in DealStatus)

DEFAULT_STAGE_SLA_HOURS: dict[str, int] = {
    DealPipelineStageCode.NEW_LEAD.value: 24,
    DealPipelineStageCode.CONTACTED.value: 48,
    DealPipelineStageCode.QUALIFIED.value: 72,
    DealPipelineStageCode.VIEWING.value: 48,
    DealPipelineStageCode.NEGOTIATION.value: 72,
    DealPipelineStageCode.RESERVED.value: 48,
    DealPipelineStageCode.DOCUMENTS.value: 72,
    DealPipelineStageCode.PAYMENT.value: 48,
    DealPipelineStageCode.DELIVERED.value: 0,
    DealPipelineStageCode.LOST.value: 0,
}

DEFAULT_STAGE_ORDER: dict[str, int] = {
    DealPipelineStageCode.NEW_LEAD.value: 1,
    DealPipelineStageCode.CONTACTED.value: 2,
    DealPipelineStageCode.QUALIFIED.value: 3,
    DealPipelineStageCode.VIEWING.value: 4,
    DealPipelineStageCode.NEGOTIATION.value: 5,
    DealPipelineStageCode.RESERVED.value: 6,
    DealPipelineStageCode.DOCUMENTS.value: 7,
    DealPipelineStageCode.PAYMENT.value: 8,
    DealPipelineStageCode.DELIVERED.value: 9,
    DealPipelineStageCode.LOST.value: 99,
}


class PipelineDeal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "deal_pipeline_engine_v2_deals"
    __table_args__ = (
        Index("ix_deal_pipeline_engine_v2_deals_tenant", "tenant_id"),
        Index("ix_deal_pipeline_engine_v2_deals_stage", "current_stage"),
        Index("ix_deal_pipeline_engine_v2_deals_manager", "assigned_manager_id"),
        Index("ix_deal_pipeline_engine_v2_deals_sales_lead", "sales_lead_id"),
        Index("ix_deal_pipeline_engine_v2_deals_sla", "sla_due_at"),
        Index("ix_deal_pipeline_engine_v2_deals_status", "status"),
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
    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    current_stage: Mapped[str] = mapped_column(
        String(40),
        default=DealPipelineStageCode.NEW_LEAD.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=DealStatus.ACTIVE.value,
        nullable=False,
    )
    assigned_manager_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    deal_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<PipelineDeal id={self.id} stage={self.current_stage}>"


class DealStage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "deal_pipeline_engine_v2_deal_stages"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "stage_code",
            name="uq_deal_pipeline_engine_v2_stages_tenant_code",
        ),
        CheckConstraint("sort_order >= 0", name="ck_deal_pipeline_engine_v2_stages_order"),
        CheckConstraint("sla_hours >= 0", name="ck_deal_pipeline_engine_v2_stages_sla"),
        Index("ix_deal_pipeline_engine_v2_stages_tenant", "tenant_id"),
        Index("ix_deal_pipeline_engine_v2_stages_code", "stage_code"),
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
    stage_code: Mapped[str] = mapped_column(String(40), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    sla_hours: Mapped[int] = mapped_column(Integer, default=48, nullable=False)
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allowed_next_stages: Mapped[list] = mapped_column(JSONB, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<DealStage tenant={self.tenant_id} code={self.stage_code}>"


class DealStageHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "deal_pipeline_engine_v2_deal_stage_history"
    __table_args__ = (
        Index("ix_deal_pipeline_engine_v2_history_deal", "deal_id"),
        Index("ix_deal_pipeline_engine_v2_history_to", "to_stage"),
        Index("ix_deal_pipeline_engine_v2_history_tenant", "tenant_id"),
    )

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_pipeline_engine_v2_deals.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_stage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    to_stage: Mapped[str] = mapped_column(String(40), nullable=False)
    changed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    validation_passed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<DealStageHistory deal={self.deal_id} {self.from_stage}->{self.to_stage}>"


class DealTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "deal_pipeline_engine_v2_deal_tasks"
    __table_args__ = (
        Index("ix_deal_pipeline_engine_v2_tasks_deal", "deal_id"),
        Index("ix_deal_pipeline_engine_v2_tasks_status", "status"),
        Index("ix_deal_pipeline_engine_v2_tasks_due", "due_at"),
        Index("ix_deal_pipeline_engine_v2_tasks_assignee", "assigned_to"),
    )

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_pipeline_engine_v2_deals.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=DealTaskStatus.OPEN.value,
        nullable=False,
    )
    assigned_to: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_created: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<DealTask deal={self.deal_id} title={self.title}>"


class DealComment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "deal_pipeline_engine_v2_deal_comments"
    __table_args__ = (
        Index("ix_deal_pipeline_engine_v2_comments_deal", "deal_id"),
        Index("ix_deal_pipeline_engine_v2_comments_tenant", "tenant_id"),
    )

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_pipeline_engine_v2_deals.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<DealComment deal={self.deal_id}>"
