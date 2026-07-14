# Marketing Analytics v1 — source attribution, CPL, conversion, ROI.

from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MarketingSourceKey(str, enum.Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TELEGRAM = "telegram"
    GOOGLE = "google"
    REFERRAL = "referral"
    BORODA_CARS = "boroda_cars"
    OTHER = "other"


MARKETING_SOURCE_DISPLAY = {
    MarketingSourceKey.FACEBOOK.value: "Facebook",
    MarketingSourceKey.INSTAGRAM.value: "Instagram",
    MarketingSourceKey.TIKTOK.value: "TikTok",
    MarketingSourceKey.TELEGRAM.value: "Telegram",
    MarketingSourceKey.GOOGLE.value: "Google",
    MarketingSourceKey.REFERRAL.value: "Referral",
    MarketingSourceKey.BORODA_CARS.value: "Boroda Cars",
    MarketingSourceKey.OTHER.value: "Other",
}


class MarketingAnalyticsV1SourceCost(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "marketing_analytics_v1_source_costs"
    __table_args__ = (
        UniqueConstraint("source_key", name="uq_marketing_analytics_v1_source_key"),
        Index("ix_marketing_analytics_v1_costs_key", "source_key"),
    )

    source_key: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    cost_per_lead: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
