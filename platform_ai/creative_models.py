"""Creative Factory models — Sprint 36.9 (extends platform_ai SoR)."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class CreativeType(str, Enum):
    LANDING_PAGE = "landing_page"
    ADVERTISEMENT = "advertisement"
    SOCIAL_POST = "social_post"
    BLOG_ARTICLE = "blog_article"
    EMAIL_CAMPAIGN = "email_campaign"
    SALES_PROPOSAL = "sales_proposal"
    COMMERCIAL_OFFER = "commercial_offer"
    PRESENTATION = "presentation"
    PDF_DOCUMENT = "pdf_document"
    MARKETING_REPORT = "marketing_report"


class MediaModality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    VOICE = "voice"
    STT = "speech_to_text"
    TTS = "text_to_speech"


class PublishChannel(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TELEGRAM = "telegram"
    LINKEDIN = "linkedin"
    X = "x"
    YOUTUBE = "youtube"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AssetStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class BrandProfile:
    brand_id: str
    name: str
    logos: list[str] = field(default_factory=list)
    colors: dict[str, str] = field(default_factory=dict)
    typography: dict[str, str] = field(default_factory=dict)
    tone_of_voice: str = "professional"
    templates: list[str] = field(default_factory=list)
    assets: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CreativeTemplate:
    template_id: str
    name: str
    creative_type: CreativeType | str
    prompt: str
    brand_id: str | None = None
    channels: list[str] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.creative_type, str):
            self.creative_type = CreativeType(self.creative_type)

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "creative_type": self.creative_type.value if isinstance(self.creative_type, CreativeType) else self.creative_type,
            "prompt": self.prompt,
            "brand_id": self.brand_id,
            "channels": list(self.channels),
            "variables": list(self.variables),
            "metadata": dict(self.metadata),
        }


@dataclass
class CreativeProject:
    project_id: str
    name: str
    brand_id: str | None = None
    status: str = "active"
    asset_ids: list[str] = field(default_factory=list)
    campaign_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CreativeAsset:
    asset_id: str
    title: str
    creative_type: CreativeType | str
    content: str = ""
    modality: MediaModality | str = MediaModality.TEXT
    project_id: str | None = None
    brand_id: str | None = None
    template_id: str | None = None
    status: AssetStatus | str = AssetStatus.DRAFT
    version: int = 1
    media_url: str | None = None
    prompt: str = ""
    provider_id: str | None = None
    tags: list[str] = field(default_factory=list)
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if isinstance(self.creative_type, str):
            self.creative_type = CreativeType(self.creative_type)
        if isinstance(self.modality, str):
            self.modality = MediaModality(self.modality)
        if isinstance(self.status, str):
            self.status = AssetStatus(self.status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "title": self.title,
            "creative_type": self.creative_type.value if isinstance(self.creative_type, CreativeType) else self.creative_type,
            "content": self.content,
            "modality": self.modality.value if isinstance(self.modality, MediaModality) else self.modality,
            "project_id": self.project_id,
            "brand_id": self.brand_id,
            "template_id": self.template_id,
            "status": self.status.value if isinstance(self.status, AssetStatus) else self.status,
            "version": self.version,
            "media_url": self.media_url,
            "prompt": self.prompt,
            "provider_id": self.provider_id,
            "tags": list(self.tags),
            "embedding": list(self.embedding[:8]),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class MediaItem:
    media_id: str
    title: str
    modality: MediaModality | str
    url: str
    prompt: str = ""
    tags: list[str] = field(default_factory=list)
    version: int = 1
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if isinstance(self.modality, str):
            self.modality = MediaModality(self.modality)

    def to_dict(self) -> dict[str, Any]:
        return {
            "media_id": self.media_id,
            "title": self.title,
            "modality": self.modality.value if isinstance(self.modality, MediaModality) else self.modality,
            "url": self.url,
            "prompt": self.prompt,
            "tags": list(self.tags),
            "version": self.version,
            "embedding": list(self.embedding[:8]),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class Campaign:
    campaign_id: str
    name: str
    objective: str
    audience: str
    channels: list[str] = field(default_factory=list)
    budget: float = 0.0
    creative_ids: list[str] = field(default_factory=list)
    schedule_at: float | None = None
    status: CampaignStatus | str = CampaignStatus.DRAFT
    brand_id: str | None = None
    project_id: str | None = None
    analytics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if isinstance(self.status, str):
            self.status = CampaignStatus(self.status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "objective": self.objective,
            "audience": self.audience,
            "channels": list(self.channels),
            "budget": self.budget,
            "creative_ids": list(self.creative_ids),
            "schedule_at": self.schedule_at,
            "status": self.status.value if isinstance(self.status, CampaignStatus) else self.status,
            "brand_id": self.brand_id,
            "project_id": self.project_id,
            "analytics": dict(self.analytics),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class PublishJob:
    job_id: str
    channel: PublishChannel | str
    asset_id: str
    campaign_id: str | None = None
    status: str = "queued"
    scheduled_at: float | None = None
    published_at: float | None = None
    external_id: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.channel, str):
            self.channel = PublishChannel(self.channel)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "channel": self.channel.value if isinstance(self.channel, PublishChannel) else self.channel,
            "asset_id": self.asset_id,
            "campaign_id": self.campaign_id,
            "status": self.status,
            "scheduled_at": self.scheduled_at,
            "published_at": self.published_at,
            "external_id": self.external_id,
            "error": self.error,
        }


@dataclass
class HistoryEntry:
    history_id: str
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
