# Marketplace inventory catalog.

from __future__ import annotations

import enum
import uuid

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class InventoryStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    ARCHIVED = "ARCHIVED"


class MarketplaceInventory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory"
    __table_args__ = (
        Index("ix_inventory_status", "status"),
        Index("ix_inventory_seller", "seller_id"),
        Index("ix_inventory_brand_model", "brand", "model"),
        Index("ix_inventory_year", "year"),
        Index("ix_inventory_price", "price"),
        Index("ix_inventory_city", "city"),
        Index("ix_inventory_fuel", "fuel"),
    )

    brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True, default="USD")
    photos: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True)
    seller_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        default=InventoryStatus.DRAFT.value,
        nullable=False,
    )
    fuel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transmission: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    engine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    marketplace_listing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketplace_listings.id", ondelete="SET NULL"),
        nullable=True,
    )
