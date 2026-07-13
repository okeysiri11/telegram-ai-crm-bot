# Cross Posting Engine v1 — multi-channel scheduled posting and analytics.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

import database.models.channel_integration_engine  # noqa: F401
import database.models.car  # noqa: F401


class PostingChannelType(str, enum.Enum):
    TELEGRAM = "TELEGRAM"
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"
    TIKTOK = "TIKTOK"


class PostingJobStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    DUPLICATE = "DUPLICATE"


class PostingResultStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


POSTING_CHANNEL_TYPES = frozenset(c.value for c in PostingChannelType)
POSTING_JOB_STATUSES = frozenset(s.value for s in PostingJobStatus)
POSTING_RESULT_STATUSES = frozenset(s.value for s in PostingResultStatus)


class PostingChannel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cross_posting_engine_v1_posting_channels"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "channel_type",
            "external_id",
            name="uq_cross_posting_engine_v1_channels_tenant_type_ext",
        ),
        Index("ix_cross_posting_engine_v1_channels_tenant", "tenant_id"),
        Index("ix_cross_posting_engine_v1_channels_type", "channel_type"),
        Index("ix_cross_posting_engine_v1_channels_active", "is_active"),
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
    channel_integration_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channel_integration_engine_v1_channels.id", ondelete="SET NULL"),
        nullable=True,
    )
    channel_type: Mapped[str] = mapped_column(String(30), nullable=False)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<PostingChannel type={self.channel_type} name={self.display_name}>"


class PostingTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cross_posting_engine_v1_posting_templates"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "code",
            name="uq_cross_posting_engine_v1_templates_tenant_code",
        ),
        Index("ix_cross_posting_engine_v1_templates_tenant", "tenant_id"),
        Index("ix_cross_posting_engine_v1_templates_channel", "channel_type"),
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
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(30), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    default_variables: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<PostingTemplate code={self.code} channel={self.channel_type}>"


class PostingJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cross_posting_engine_v1_posting_jobs"
    __table_args__ = (
        Index("ix_cross_posting_engine_v1_jobs_tenant", "tenant_id"),
        Index("ix_cross_posting_engine_v1_jobs_status", "status"),
        Index("ix_cross_posting_engine_v1_jobs_scheduled", "scheduled_at"),
        Index("ix_cross_posting_engine_v1_jobs_hash", "content_hash"),
        Index("ix_cross_posting_engine_v1_jobs_channel", "channel_id"),
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
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cross_posting_engine_v1_posting_channels.id", ondelete="CASCADE"),
        nullable=False,
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cross_posting_engine_v1_posting_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=PostingJobStatus.DRAFT.value,
        nullable=False,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_repost: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cross_posting_engine_v1_posting_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<PostingJob id={self.id} status={self.status}>"


class PostingResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cross_posting_engine_v1_posting_results"
    __table_args__ = (
        Index("ix_cross_posting_engine_v1_results_job", "job_id"),
        Index("ix_cross_posting_engine_v1_results_tenant", "tenant_id"),
        Index("ix_cross_posting_engine_v1_results_status", "status"),
        Index("ix_cross_posting_engine_v1_results_external", "external_post_id"),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cross_posting_engine_v1_posting_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shares: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    analytics_collected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<PostingResult job={self.job_id} status={self.status}>"
