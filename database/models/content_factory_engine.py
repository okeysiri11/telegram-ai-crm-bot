# Content Factory Engine v1 — generated marketing and SEO content.

from __future__ import annotations

import enum
import uuid

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ContentType(str, enum.Enum):
    CAR_DESCRIPTION = "car_description"
    TELEGRAM_POST = "telegram_post"
    INSTAGRAM_POST = "instagram_post"
    TIKTOK_SCRIPT = "tiktok_script"
    FACEBOOK_AD = "facebook_ad"
    SEO_TEXT = "seo_text"


CONTENT_TYPES = frozenset(t.value for t in ContentType)


class ContentItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_factory_engine_v1_content_items"
    __table_args__ = (
        Index("ix_content_factory_engine_v1_items_car", "car_id"),
        Index("ix_content_factory_engine_v1_items_type", "content_type"),
        UniqueConstraint(
            "car_id",
            "content_type",
            "version",
            name="uq_content_factory_engine_v1_items_car_type_version",
        ),
    )

    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    content_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<ContentItem type={self.content_type} car={self.car_id}>"
