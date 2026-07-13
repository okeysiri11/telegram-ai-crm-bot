# Auto Marketing Engine v1 — campaigns, templates, media, and publication queues.

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


class MarketingChannel(str, enum.Enum):
    TELEGRAM = "telegram"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PublicationStatus(str, enum.Enum):
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MediaType(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"


MARKETING_CHANNELS = frozenset(c.value for c in MarketingChannel)
CAMPAIGN_STATUSES = frozenset(s.value for s in CampaignStatus)
PUBLICATION_STATUSES = frozenset(s.value for s in PublicationStatus)
MEDIA_TYPES = frozenset(t.value for t in MediaType)


class MarketingCampaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auto_marketing_engine_v1_campaigns"
    __table_args__ = (
        Index("ix_auto_marketing_engine_v1_campaigns_status", "status"),
        Index("ix_auto_marketing_engine_v1_campaigns_car", "car_id"),
        Index("ix_auto_marketing_engine_v1_campaigns_owner", "owner_user_id"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=CampaignStatus.DRAFT.value,
        nullable=False,
    )
    channels: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<MarketingCampaign name={self.name} status={self.status}>"


class MarketingPostTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auto_marketing_engine_v1_post_templates"
    __table_args__ = (
        UniqueConstraint("code", name="uq_auto_marketing_engine_v1_templates_code"),
        Index("ix_auto_marketing_engine_v1_templates_channel", "channel"),
        Index("ix_auto_marketing_engine_v1_templates_active", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    default_variables: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<MarketingPostTemplate code={self.code} channel={self.channel}>"


class MarketingMediaAsset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auto_marketing_engine_v1_media_assets"
    __table_args__ = (
        Index("ix_auto_marketing_engine_v1_media_campaign", "campaign_id"),
        Index("ix_auto_marketing_engine_v1_media_car", "car_id"),
        Index("ix_auto_marketing_engine_v1_media_type", "media_type"),
    )

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auto_marketing_engine_v1_campaigns.id", ondelete="SET NULL"),
        nullable=True,
    )
    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    media_type: Mapped[str] = mapped_column(String(30), nullable=False)
    telegram_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    public_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    uploaded_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<MarketingMediaAsset file={self.file_name} type={self.media_type}>"


class MarketingPublication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auto_marketing_engine_v1_publications"
    __table_args__ = (
        Index("ix_auto_marketing_engine_v1_pub_campaign", "campaign_id"),
        Index("ix_auto_marketing_engine_v1_pub_channel", "channel"),
        Index("ix_auto_marketing_engine_v1_pub_status", "status"),
        Index("ix_auto_marketing_engine_v1_pub_scheduled", "scheduled_at"),
        Index("ix_auto_marketing_engine_v1_pub_car", "car_id"),
    )

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auto_marketing_engine_v1_campaigns.id", ondelete="SET NULL"),
        nullable=True,
    )
    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auto_marketing_engine_v1_post_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_asset_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        default=PublicationStatus.QUEUED.value,
        nullable=False,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    target_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<MarketingPublication channel={self.channel} "
            f"status={self.status}>"
        )
