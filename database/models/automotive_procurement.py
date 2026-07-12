# Automotive Procurement Engine v1 — purchase orders, offers, auctions, sources.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

import database.models.automotive_inventory  # noqa: F401
import database.models.partner_engine  # noqa: F401


class VehicleSourceType(str, enum.Enum):
    COPART = "COPART"
    IAAI = "IAAI"
    MANHEIM = "MANHEIM"
    LOCAL_DEALER = "LOCAL_DEALER"
    PRIVATE_SELLER = "PRIVATE_SELLER"


class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    ORDERED = "ORDERED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class SupplierOfferStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class AuctionLotStatus(str, enum.Enum):
    WATCHING = "WATCHING"
    BIDDING = "BIDDING"
    WON = "WON"
    LOST = "LOST"
    CANCELLED = "CANCELLED"


class PurchaseOrder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_procurement_v1_purchase_orders"
    __table_args__ = (
        UniqueConstraint(
            "order_number",
            name="uq_automotive_procurement_v1_purchase_orders_order_number",
        ),
        CheckConstraint("year >= 1900", name="ck_automotive_procurement_v1_po_year"),
        Index("ix_automotive_procurement_v1_po_status", "status"),
        Index("ix_automotive_procurement_v1_po_source", "source"),
        Index("ix_automotive_procurement_v1_po_vehicle_id", "vehicle_id"),
        Index("ix_automotive_procurement_v1_po_partner_id", "partner_id"),
    )

    order_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=PurchaseOrderStatus.DRAFT.value,
        nullable=False,
    )
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    vin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    agreed_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<PurchaseOrder id={self.id} number={self.order_number} "
            f"status={self.status}>"
        )


class SupplierOffer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_procurement_v1_suppliers_offers"
    __table_args__ = (
        Index("ix_automotive_procurement_v1_offers_status", "status"),
        Index("ix_automotive_procurement_v1_offers_source", "source"),
        Index("ix_automotive_procurement_v1_offers_po_id", "purchase_order_id"),
        Index("ix_automotive_procurement_v1_offers_partner_id", "partner_id"),
    )

    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "automotive_procurement_v1_purchase_orders.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="SET NULL"),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=SupplierOfferStatus.PENDING.value,
        nullable=False,
    )
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    vin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    offer_price: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<SupplierOffer id={self.id} {self.make} {self.model} "
            f"status={self.status}>"
        )


class AuctionLot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_procurement_v1_auction_lots"
    __table_args__ = (
        CheckConstraint("year >= 1900", name="ck_automotive_procurement_v1_lot_year"),
        Index("ix_automotive_procurement_v1_lots_status", "status"),
        Index("ix_automotive_procurement_v1_lots_source", "source"),
        Index("ix_automotive_procurement_v1_lots_po_id", "purchase_order_id"),
        Index("ix_automotive_procurement_v1_lots_auction_date", "auction_date"),
    )

    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "automotive_procurement_v1_purchase_orders.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    lot_number: Mapped[str] = mapped_column(String(100), nullable=False)
    external_lot_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=AuctionLotStatus.WATCHING.value,
        nullable=False,
    )
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    vin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    yard_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_bid: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    buy_now_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    winning_bid: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    auction_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AuctionLot id={self.id} lot={self.lot_number} "
            f"source={self.source} status={self.status}>"
        )


class VehicleSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_procurement_v1_vehicle_sources"
    __table_args__ = (
        Index("ix_automotive_procurement_v1_vs_source", "source"),
        Index("ix_automotive_procurement_v1_vs_vehicle_id", "vehicle_id"),
        Index("ix_automotive_procurement_v1_vs_po_id", "purchase_order_id"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "automotive_procurement_v1_purchase_orders.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    supplier_offer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "automotive_procurement_v1_suppliers_offers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    auction_lot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "automotive_procurement_v1_auction_lots.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<VehicleSource id={self.id} vehicle={self.vehicle_id} "
            f"source={self.source}>"
        )
