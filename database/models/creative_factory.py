"""Creative Factory ORM — Sprint 36.9."""

from __future__ import annotations

from sqlalchemy import Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class CreativeProjectRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_projects"
    __table_args__ = (
        UniqueConstraint("project_key", name="uq_creative_projects_project_key"),
        Index("ix_creative_projects_brand_id", "brand_id"),
    )

    project_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    brand_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    asset_ids_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    campaign_ids_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class CreativeAssetRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_assets"
    __table_args__ = (
        UniqueConstraint("asset_key", name="uq_creative_assets_asset_key"),
        Index("ix_creative_assets_type", "creative_type"),
        Index("ix_creative_assets_status", "status"),
        Index("ix_creative_assets_project_id", "project_id"),
    )

    asset_key: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    creative_type: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    modality: Mapped[str] = mapped_column(String(64), nullable=False, default="text")
    project_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    brand_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    template_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    media_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provider_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    asset_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    tags_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    embedding_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class CreativeTemplateRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_templates"
    __table_args__ = (
        UniqueConstraint("template_key", name="uq_creative_templates_template_key"),
        Index("ix_creative_templates_type", "creative_type"),
    )

    template_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    creative_type: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    brand_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    channels_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    variables_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class CampaignRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "campaigns"
    __table_args__ = (
        UniqueConstraint("campaign_key", name="uq_campaigns_campaign_key"),
        Index("ix_campaigns_status", "status"),
        Index("ix_campaigns_brand_id", "brand_id"),
    )

    campaign_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    objective: Mapped[str] = mapped_column(String(128), nullable=False, default="awareness")
    audience: Mapped[str] = mapped_column(String(256), nullable=False, default="general")
    channels_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    budget: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    creative_ids_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    schedule_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    brand_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    project_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    analytics_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class CampaignChannelRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "campaign_channels"
    __table_args__ = (
        Index("ix_campaign_channels_campaign_key", "campaign_key"),
        UniqueConstraint("campaign_key", "channel", name="uq_campaign_channels_campaign_channel"),
    )

    campaign_key: Mapped[str] = mapped_column(String(128), nullable=False)
    channel: Mapped[str] = mapped_column(String(64), nullable=False)
    budget_share: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    settings_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class MediaLibraryRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "media_library"
    __table_args__ = (
        UniqueConstraint("media_key", name="uq_media_library_media_key"),
        Index("ix_media_library_modality", "modality"),
    )

    media_key: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    modality: Mapped[str] = mapped_column(String(64), nullable=False, default="image")
    url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    embedding_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    media_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class BrandProfileRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "brand_profiles"
    __table_args__ = (UniqueConstraint("brand_key", name="uq_brand_profiles_brand_key"),)

    brand_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    logos_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    colors_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    typography_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    tone_of_voice: Mapped[str] = mapped_column(String(256), nullable=False, default="professional")
    templates_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    assets_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class CreativeHistoryRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_history"
    __table_args__ = (
        Index("ix_creative_history_entity", "entity_type", "entity_id"),
        Index("ix_creative_history_action", "action"),
    )

    history_key: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
