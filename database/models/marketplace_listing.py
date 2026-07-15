# Marketplace vehicle listings generated from client listing requests.

from __future__ import annotations

import enum
import uuid

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MarketplaceListingStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SOLD = "SOLD"
    ARCHIVED = "ARCHIVED"


class MarketplaceListing(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "marketplace_listings"
    __table_args__ = (
        Index("ix_marketplace_listings_seller", "seller_telegram_id"),
        Index("ix_marketplace_listings_status", "status"),
        Index("ix_marketplace_listings_brand_model", "brand", "model"),
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default=MarketplaceListingStatus.ACTIVE.value,
        nullable=False,
    )
    seller_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    seller_username: Mapped[str | None] = mapped_column(String(255), nullable=True)

    brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    fuel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    engine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transmission: Mapped[str | None] = mapped_column(String(64), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_file_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    listing_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    client_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("client_requests.id", ondelete="SET NULL"),
        nullable=True,
    )
