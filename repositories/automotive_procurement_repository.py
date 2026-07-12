# Automotive Procurement Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_procurement import (
    AuctionLot,
    AuctionLotStatus,
    PurchaseOrder,
    PurchaseOrderStatus,
    SupplierOffer,
    SupplierOfferStatus,
    VehicleSource,
    VehicleSourceType,
)


class PurchaseOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        order_number: str,
        source: str,
        make: str,
        model: str,
        year: int,
        created_by: int | None = None,
        vehicle_id: uuid.UUID | None = None,
        partner_id: uuid.UUID | None = None,
        status: str = PurchaseOrderStatus.DRAFT.value,
        vin: str | None = None,
        target_price: Decimal | None = None,
        agreed_price: Decimal | None = None,
        currency: str = "USD",
        notes: str | None = None,
        **extra: Any,
    ) -> PurchaseOrder:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if source not in {s.value for s in VehicleSourceType}:
            raise ValueError(f"Invalid source: {source}")
        if status not in {s.value for s in PurchaseOrderStatus}:
            raise ValueError(f"Invalid status: {status}")
        if year < 1900:
            raise ValueError("year must be >= 1900")

        order = PurchaseOrder(
            order_number=order_number,
            source=source,
            make=make,
            model=model,
            year=year,
            created_by=created_by,
            vehicle_id=vehicle_id,
            partner_id=partner_id,
            status=status,
            vin=vin,
            target_price=target_price,
            agreed_price=agreed_price,
            currency=currency,
            notes=notes,
        )
        self._session.add(order)
        await self._session.flush()
        return order

    async def get_by_id(self, order_id: uuid.UUID) -> PurchaseOrder | None:
        result = await self._session.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_order_number(self, order_number: str) -> PurchaseOrder | None:
        result = await self._session.execute(
            select(PurchaseOrder).where(PurchaseOrder.order_number == order_number)
        )
        return result.scalar_one_or_none()

    async def list_by_status(self, status: str, *, limit: int = 100) -> list[PurchaseOrder]:
        result = await self._session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.status == status)
            .order_by(PurchaseOrder.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_all(self, *, limit: int = 100) -> list[PurchaseOrder]:
        result = await self._session.execute(
            select(PurchaseOrder)
            .order_by(PurchaseOrder.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_fields(
        self,
        order_id: uuid.UUID,
        **fields: Any,
    ) -> PurchaseOrder | None:
        order = await self.get_by_id(order_id)
        if order is None:
            return None
        allowed = {
            "vehicle_id", "partner_id", "vin", "target_price", "agreed_price",
            "currency", "notes", "make", "model", "year",
        }
        for key, value in fields.items():
            if key not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(order, key, value)
        order.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return order

    async def update_status(
        self,
        order_id: uuid.UUID,
        status: str,
    ) -> PurchaseOrder | None:
        order = await self.get_by_id(order_id)
        if order is None:
            return None
        if status not in {s.value for s in PurchaseOrderStatus}:
            raise ValueError(f"Invalid status: {status}")
        order.status = status
        order.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return order


class SupplierOfferRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        source: str,
        make: str,
        model: str,
        year: int,
        offer_price: Decimal,
        purchase_order_id: uuid.UUID | None = None,
        partner_id: uuid.UUID | None = None,
        status: str = SupplierOfferStatus.PENDING.value,
        vin: str | None = None,
        currency: str = "USD",
        valid_until: datetime | None = None,
        notes: str | None = None,
        **extra: Any,
    ) -> SupplierOffer:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if source not in {s.value for s in VehicleSourceType}:
            raise ValueError(f"Invalid source: {source}")
        if status not in {s.value for s in SupplierOfferStatus}:
            raise ValueError(f"Invalid status: {status}")

        offer = SupplierOffer(
            source=source,
            make=make,
            model=model,
            year=year,
            offer_price=offer_price,
            purchase_order_id=purchase_order_id,
            partner_id=partner_id,
            status=status,
            vin=vin,
            currency=currency,
            valid_until=valid_until,
            notes=notes,
        )
        self._session.add(offer)
        await self._session.flush()
        return offer

    async def get_by_id(self, offer_id: uuid.UUID) -> SupplierOffer | None:
        result = await self._session.execute(
            select(SupplierOffer).where(SupplierOffer.id == offer_id)
        )
        return result.scalar_one_or_none()

    async def list_by_purchase_order(
        self,
        purchase_order_id: uuid.UUID,
    ) -> list[SupplierOffer]:
        result = await self._session.execute(
            select(SupplierOffer)
            .where(SupplierOffer.purchase_order_id == purchase_order_id)
            .order_by(SupplierOffer.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_pending(self, *, limit: int = 100) -> list[SupplierOffer]:
        result = await self._session.execute(
            select(SupplierOffer)
            .where(SupplierOffer.status == SupplierOfferStatus.PENDING.value)
            .order_by(SupplierOffer.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        offer_id: uuid.UUID,
        status: str,
    ) -> SupplierOffer | None:
        offer = await self.get_by_id(offer_id)
        if offer is None:
            return None
        if status not in {s.value for s in SupplierOfferStatus}:
            raise ValueError(f"Invalid status: {status}")
        offer.status = status
        offer.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return offer


class AuctionLotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        source: str,
        lot_number: str,
        make: str,
        model: str,
        year: int,
        purchase_order_id: uuid.UUID | None = None,
        external_lot_id: str | None = None,
        status: str = AuctionLotStatus.WATCHING.value,
        vin: str | None = None,
        mileage: int | None = None,
        yard_location: str | None = None,
        current_bid: Decimal | None = None,
        buy_now_price: Decimal | None = None,
        currency: str = "USD",
        auction_date: datetime | None = None,
        notes: str | None = None,
        **extra: Any,
    ) -> AuctionLot:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        auction_sources = {
            VehicleSourceType.COPART.value,
            VehicleSourceType.IAAI.value,
            VehicleSourceType.MANHEIM.value,
        }
        if source not in auction_sources:
            raise ValueError(f"Invalid auction source: {source}")
        if status not in {s.value for s in AuctionLotStatus}:
            raise ValueError(f"Invalid status: {status}")
        if year < 1900:
            raise ValueError("year must be >= 1900")

        lot = AuctionLot(
            source=source,
            lot_number=lot_number,
            make=make,
            model=model,
            year=year,
            purchase_order_id=purchase_order_id,
            external_lot_id=external_lot_id,
            status=status,
            vin=vin,
            mileage=mileage,
            yard_location=yard_location,
            current_bid=current_bid,
            buy_now_price=buy_now_price,
            currency=currency,
            auction_date=auction_date,
            notes=notes,
        )
        self._session.add(lot)
        await self._session.flush()
        return lot

    async def get_by_id(self, lot_id: uuid.UUID) -> AuctionLot | None:
        result = await self._session.execute(
            select(AuctionLot).where(AuctionLot.id == lot_id)
        )
        return result.scalar_one_or_none()

    async def list_by_status(self, status: str, *, limit: int = 100) -> list[AuctionLot]:
        result = await self._session.execute(
            select(AuctionLot)
            .where(AuctionLot.status == status)
            .order_by(AuctionLot.auction_date.asc().nullslast())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_source(self, source: str, *, limit: int = 100) -> list[AuctionLot]:
        result = await self._session.execute(
            select(AuctionLot)
            .where(AuctionLot.source == source)
            .order_by(AuctionLot.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_fields(
        self,
        lot_id: uuid.UUID,
        **fields: Any,
    ) -> AuctionLot | None:
        lot = await self.get_by_id(lot_id)
        if lot is None:
            return None
        allowed = {
            "current_bid", "buy_now_price", "winning_bid", "vin", "mileage",
            "yard_location", "auction_date", "notes", "purchase_order_id",
        }
        for key, value in fields.items():
            if key not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(lot, key, value)
        lot.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return lot

    async def update_status(
        self,
        lot_id: uuid.UUID,
        status: str,
        *,
        winning_bid: Decimal | None = None,
    ) -> AuctionLot | None:
        lot = await self.get_by_id(lot_id)
        if lot is None:
            return None
        if status not in {s.value for s in AuctionLotStatus}:
            raise ValueError(f"Invalid status: {status}")
        lot.status = status
        if winning_bid is not None:
            lot.winning_bid = winning_bid
        lot.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return lot


class VehicleSourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        vehicle_id: uuid.UUID,
        source: str,
        purchase_order_id: uuid.UUID | None = None,
        supplier_offer_id: uuid.UUID | None = None,
        auction_lot_id: uuid.UUID | None = None,
        external_reference: str | None = None,
        acquired_at: datetime | None = None,
        notes: str | None = None,
        **extra: Any,
    ) -> VehicleSource:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if source not in {s.value for s in VehicleSourceType}:
            raise ValueError(f"Invalid source: {source}")

        record = VehicleSource(
            vehicle_id=vehicle_id,
            source=source,
            purchase_order_id=purchase_order_id,
            supplier_offer_id=supplier_offer_id,
            auction_lot_id=auction_lot_id,
            external_reference=external_reference,
            acquired_at=acquired_at or datetime.now(timezone.utc),
            notes=notes,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_id(self, source_id: uuid.UUID) -> VehicleSource | None:
        result = await self._session.execute(
            select(VehicleSource).where(VehicleSource.id == source_id)
        )
        return result.scalar_one_or_none()

    async def get_by_vehicle(self, vehicle_id: uuid.UUID) -> VehicleSource | None:
        result = await self._session.execute(
            select(VehicleSource)
            .where(VehicleSource.vehicle_id == vehicle_id)
            .order_by(VehicleSource.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_source(self, source: str, *, limit: int = 100) -> list[VehicleSource]:
        result = await self._session.execute(
            select(VehicleSource)
            .where(VehicleSource.source == source)
            .order_by(VehicleSource.acquired_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
