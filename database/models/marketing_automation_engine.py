# Marketing Automation Engine v1 — scheduled posts, repost rules, media processing.

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
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AutomationChannel(str, enum.Enum):
    TELEGRAM = "telegram"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"


class AutomationCampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ScheduledPostStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    QUEUED = "queued"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


AUTOMATION_CHANNELS = frozenset(c.value for c in AutomationChannel)
AUTOMATION_CAMPAIGN_STATUSES = frozenset(s.value for s in AutomationCampaignStatus)
SCHEDULED_POST_STATUSES = frozenset(s.value for s in ScheduledPostStatus)


class AutomationCampaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "marketing_automation_engine_v1_campaigns"
    __table_args__ = (
        Index("ix_marketing_automation_engine_v1_campaigns_status", "status"),
        Index("ix_marketing_automation_engine_v1_campaigns_car", "car_id"),
        Index("ix_marketing_automation_engine_v1_campaigns_owner", "owner_user_id"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    auto_marketing_campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=AutomationCampaignStatus.DRAFT.value,
        nullable=False,
    )
    channels: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<AutomationCampaign name={self.name} status={self.status}>"


class RepostRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "marketing_automation_engine_v1_repost_rules"
    __table_args__ = (
        Index("ix_marketing_automation_engine_v1_repost_campaign", "campaign_id"),
        Index("ix_marketing_automation_engine_v1_repost_active", "is_active"),
        Index("ix_marketing_automation_engine_v1_repost_next", "next_repost_at"),
    )

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketing_automation_engine_v1_campaigns.id", ondelete="CASCADE"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_media_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    channels: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    interval_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    max_reposts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    repost_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    watermark_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    optimize_images: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_reposted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_repost_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<RepostRule name={self.name} reposts={self.repost_count}/{self.max_reposts}>"


class ScheduledPost(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "marketing_automation_engine_v1_scheduled_posts"
    __table_args__ = (
        Index("ix_marketing_automation_engine_v1_posts_campaign", "campaign_id"),
        Index("ix_marketing_automation_engine_v1_posts_channel", "channel"),
        Index("ix_marketing_automation_engine_v1_posts_status", "status"),
        Index("ix_marketing_automation_engine_v1_posts_scheduled", "scheduled_at"),
        Index("ix_marketing_automation_engine_v1_posts_car", "car_id"),
    )

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketing_automation_engine_v1_campaigns.id", ondelete="SET NULL"),
        nullable=True,
    )
    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    repost_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketing_automation_engine_v1_repost_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    source_media_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    processed_media_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=ScheduledPostStatus.SCHEDULED.value,
        nullable=False,
    )
    publication_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    repost_generation: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    processing_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ScheduledPost channel={self.channel} "
            f"status={self.status} scheduled={self.scheduled_at}>"
        )


class ProcessedMedia(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "marketing_automation_engine_v1_processed_media"
    __table_args__ = (
        Index("ix_marketing_automation_engine_v1_media_post", "scheduled_post_id"),
    )

    scheduled_post_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketing_automation_engine_v1_scheduled_posts.id", ondelete="CASCADE"),
        nullable=True,
    )
    original_path: Mapped[str] = mapped_column(String(500), nullable=False)
    processed_path: Mapped[str] = mapped_column(String(500), nullable=False)
    watermark_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    optimized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    original_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<ProcessedMedia post={self.scheduled_post_id} optimized={self.optimized}>"
