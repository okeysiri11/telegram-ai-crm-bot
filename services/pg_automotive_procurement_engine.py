# Automotive Procurement Engine v1 — purchase orders, offers, auctions, sources.

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from config import OWNER_ID
from database.models.automotive_procurement import (
    AuctionLotStatus,
    PurchaseOrderStatus,
    SupplierOfferStatus,
    VehicleSourceType,
)
from database.session import get_session
from repositories.automotive_inventory_repository import VehicleRepository
from repositories.automotive_procurement_repository import (
    AuctionLotRepository,
    PurchaseOrderRepository,
    SupplierOfferRepository,
    VehicleSourceRepository,
)
from repositories.user_role_repository import UserRoleRepository

PROCUREMENT_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})


class AutomotiveProcurementEngineError(Exception):
    pass


class AutomotiveProcurementEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in PROCUREMENT_ROLES for role in roles)

    @staticmethod
    def _purchase_order_snapshot(order) -> dict[str, Any]:
        return {
            "id": str(order.id),
            "order_number": order.order_number,
            "vehicle_id": str(order.vehicle_id) if order.vehicle_id else None,
            "partner_id": str(order.partner_id) if order.partner_id else None,
            "source": order.source,
            "status": order.status,
            "make": order.make,
            "model": order.model,
            "year": order.year,
            "vin": order.vin,
            "target_price": str(order.target_price) if order.target_price else None,
            "agreed_price": str(order.agreed_price) if order.agreed_price else None,
            "currency": order.currency,
            "notes": order.notes,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
        }

    @staticmethod
    def _supplier_offer_snapshot(offer) -> dict[str, Any]:
        return {
            "id": str(offer.id),
            "purchase_order_id": (
                str(offer.purchase_order_id) if offer.purchase_order_id else None
            ),
            "partner_id": str(offer.partner_id) if offer.partner_id else None,
            "source": offer.source,
            "status": offer.status,
            "make": offer.make,
            "model": offer.model,
            "year": offer.year,
            "vin": offer.vin,
            "offer_price": str(offer.offer_price),
            "currency": offer.currency,
            "valid_until": offer.valid_until.isoformat() if offer.valid_until else None,
            "notes": offer.notes,
            "created_at": offer.created_at.isoformat(),
            "updated_at": offer.updated_at.isoformat(),
        }

    @staticmethod
    def _auction_lot_snapshot(lot) -> dict[str, Any]:
        return {
            "id": str(lot.id),
            "purchase_order_id": (
                str(lot.purchase_order_id) if lot.purchase_order_id else None
            ),
            "source": lot.source,
            "lot_number": lot.lot_number,
            "external_lot_id": lot.external_lot_id,
            "status": lot.status,
            "make": lot.make,
            "model": lot.model,
            "year": lot.year,
            "vin": lot.vin,
            "mileage": lot.mileage,
            "yard_location": lot.yard_location,
            "current_bid": str(lot.current_bid) if lot.current_bid else None,
            "buy_now_price": str(lot.buy_now_price) if lot.buy_now_price else None,
            "winning_bid": str(lot.winning_bid) if lot.winning_bid else None,
            "currency": lot.currency,
            "auction_date": lot.auction_date.isoformat() if lot.auction_date else None,
            "notes": lot.notes,
            "created_at": lot.created_at.isoformat(),
            "updated_at": lot.updated_at.isoformat(),
        }

    @staticmethod
    def _vehicle_source_snapshot(record) -> dict[str, Any]:
        return {
            "id": str(record.id),
            "vehicle_id": str(record.vehicle_id),
            "purchase_order_id": (
                str(record.purchase_order_id) if record.purchase_order_id else None
            ),
            "supplier_offer_id": (
                str(record.supplier_offer_id) if record.supplier_offer_id else None
            ),
            "auction_lot_id": (
                str(record.auction_lot_id) if record.auction_lot_id else None
            ),
            "source": record.source,
            "external_reference": record.external_reference,
            "acquired_at": record.acquired_at.isoformat(),
            "notes": record.notes,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }

    @staticmethod
    async def create_purchase_order(
        actor_id: int,
        *,
        order_number: str,
        source: str,
        make: str,
        model: str,
        year: int,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveProcurementEngineV1.user_can_access(actor_id):
            raise AutomotiveProcurementEngineError("Access denied")
        if source not in {s.value for s in VehicleSourceType}:
            raise AutomotiveProcurementEngineError(f"Invalid source: {source}")

        async with get_session() as session:
            repo = PurchaseOrderRepository(session)
            if await repo.get_by_order_number(order_number):
                raise AutomotiveProcurementEngineError(
                    f"Purchase order already exists: {order_number}"
                )

            order = await repo.create(
                order_number=order_number,
                source=source,
                make=make,
                model=model,
                year=year,
                created_by=actor_id,
                **fields,
            )
            return AutomotiveProcurementEngineV1._purchase_order_snapshot(order)

    @staticmethod
    async def update_purchase_order(
        actor_id: int,
        order_id: uuid.UUID,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveProcurementEngineV1.user_can_access(actor_id):
            raise AutomotiveProcurementEngineError("Access denied")

        async with get_session() as session:
            order = await PurchaseOrderRepository(session).update_fields(order_id, **fields)
            if order is None:
                raise AutomotiveProcurementEngineError(f"Purchase order not found: {order_id}")
            return AutomotiveProcurementEngineV1._purchase_order_snapshot(order)

    @staticmethod
    async def update_purchase_order_status(
        actor_id: int,
        order_id: uuid.UUID,
        status: str,
    ) -> dict[str, Any]:
        if not await AutomotiveProcurementEngineV1.user_can_access(actor_id):
            raise AutomotiveProcurementEngineError("Access denied")
        if status not in {s.value for s in PurchaseOrderStatus}:
            raise AutomotiveProcurementEngineError(f"Invalid status: {status}")

        async with get_session() as session:
            order = await PurchaseOrderRepository(session).update_status(order_id, status)
            if order is None:
                raise AutomotiveProcurementEngineError(f"Purchase order not found: {order_id}")
            return AutomotiveProcurementEngineV1._purchase_order_snapshot(order)

    @staticmethod
    async def create_supplier_offer(
        actor_id: int,
        *,
        source: str,
        make: str,
        model: str,
        year: int,
        offer_price: Decimal,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveProcurementEngineV1.user_can_access(actor_id):
            raise AutomotiveProcurementEngineError("Access denied")
        if source not in {s.value for s in VehicleSourceType}:
            raise AutomotiveProcurementEngineError(f"Invalid source: {source}")

        async with get_session() as session:
            offer = await SupplierOfferRepository(session).create(
                source=source,
                make=make,
                model=model,
                year=year,
                offer_price=offer_price,
                **fields,
            )
            return AutomotiveProcurementEngineV1._supplier_offer_snapshot(offer)

    @staticmethod
    async def update_supplier_offer_status(
        actor_id: int,
        offer_id: uuid.UUID,
        status: str,
    ) -> dict[str, Any]:
        if not await AutomotiveProcurementEngineV1.user_can_access(actor_id):
            raise AutomotiveProcurementEngineError("Access denied")
        if status not in {s.value for s in SupplierOfferStatus}:
            raise AutomotiveProcurementEngineError(f"Invalid status: {status}")

        async with get_session() as session:
            offer = await SupplierOfferRepository(session).update_status(offer_id, status)
            if offer is None:
                raise AutomotiveProcurementEngineError(f"Supplier offer not found: {offer_id}")
            return AutomotiveProcurementEngineV1._supplier_offer_snapshot(offer)

    @staticmethod
    async def create_auction_lot(
        actor_id: int,
        *,
        source: str,
        lot_number: str,
        make: str,
        model: str,
        year: int,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveProcurementEngineV1.user_can_access(actor_id):
            raise AutomotiveProcurementEngineError("Access denied")

        async with get_session() as session:
            lot = await AuctionLotRepository(session).create(
                source=source,
                lot_number=lot_number,
                make=make,
                model=model,
                year=year,
                **fields,
            )
            return AutomotiveProcurementEngineV1._auction_lot_snapshot(lot)

    @staticmethod
    async def update_auction_lot(
        actor_id: int,
        lot_id: uuid.UUID,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveProcurementEngineV1.user_can_access(actor_id):
            raise AutomotiveProcurementEngineError("Access denied")

        async with get_session() as session:
            lot = await AuctionLotRepository(session).update_fields(lot_id, **fields)
            if lot is None:
                raise AutomotiveProcurementEngineError(f"Auction lot not found: {lot_id}")
            return AutomotiveProcurementEngineV1._auction_lot_snapshot(lot)

    @staticmethod
    async def update_auction_lot_status(
        actor_id: int,
        lot_id: uuid.UUID,
        status: str,
        *,
        winning_bid: Decimal | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveProcurementEngineV1.user_can_access(actor_id):
            raise AutomotiveProcurementEngineError("Access denied")
        if status not in {s.value for s in AuctionLotStatus}:
            raise AutomotiveProcurementEngineError(f"Invalid status: {status}")

        async with get_session() as session:
            lot = await AuctionLotRepository(session).update_status(
                lot_id,
                status,
                winning_bid=winning_bid,
            )
            if lot is None:
                raise AutomotiveProcurementEngineError(f"Auction lot not found: {lot_id}")
            return AutomotiveProcurementEngineV1._auction_lot_snapshot(lot)

    @staticmethod
    async def record_vehicle_source(
        actor_id: int,
        *,
        vehicle_id: uuid.UUID,
        source: str,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveProcurementEngineV1.user_can_access(actor_id):
            raise AutomotiveProcurementEngineError("Access denied")
        if source not in {s.value for s in VehicleSourceType}:
            raise AutomotiveProcurementEngineError(f"Invalid source: {source}")

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveProcurementEngineError(f"Vehicle not found: {vehicle_id}")

            record = await VehicleSourceRepository(session).create(
                vehicle_id=vehicle_id,
                source=source,
                **fields,
            )
            return AutomotiveProcurementEngineV1._vehicle_source_snapshot(record)

    @staticmethod
    async def get_purchase_order(
        actor_id: int,
        order_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveProcurementEngineV1.user_can_access(actor_id):
            raise AutomotiveProcurementEngineError("Access denied")

        async with get_session() as session:
            order = await PurchaseOrderRepository(session).get_by_id(order_id)
            if order is None:
                raise AutomotiveProcurementEngineError(f"Purchase order not found: {order_id}")

            offers = await SupplierOfferRepository(session).list_by_purchase_order(order_id)

            return {
                "order": AutomotiveProcurementEngineV1._purchase_order_snapshot(order),
                "offers": [
                    AutomotiveProcurementEngineV1._supplier_offer_snapshot(o)
                    for o in offers
                ],
            }

    @staticmethod
    async def list_purchase_orders(
        actor_id: int,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveProcurementEngineV1.user_can_access(actor_id):
            raise AutomotiveProcurementEngineError("Access denied")

        async with get_session() as session:
            repo = PurchaseOrderRepository(session)
            if status:
                orders = await repo.list_by_status(status, limit=limit)
            else:
                orders = await repo.list_all(limit=limit)

            return [
                AutomotiveProcurementEngineV1._purchase_order_snapshot(o)
                for o in orders
            ]

    @staticmethod
    async def list_auction_lots(
        actor_id: int,
        *,
        source: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveProcurementEngineV1.user_can_access(actor_id):
            raise AutomotiveProcurementEngineError("Access denied")

        async with get_session() as session:
            repo = AuctionLotRepository(session)
            if status:
                lots = await repo.list_by_status(status, limit=limit)
            elif source:
                lots = await repo.list_by_source(source, limit=limit)
            else:
                lots = await repo.list_by_status(AuctionLotStatus.WATCHING.value, limit=limit)

            return [
                AutomotiveProcurementEngineV1._auction_lot_snapshot(lot)
                for lot in lots
            ]
