# InventoryService — stock, reservations, inspections, auctions.

from __future__ import annotations

from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.models import (
    Auction,
    Inspection,
    Reservation,
    ServiceHistory,
    VehicleStatus,
    Warranty,
)
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class InventoryService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def reserve_vehicle(self, reservation: Reservation) -> Reservation:
        vehicle = self._store.vehicles.get(reservation.vehicle_id)
        if vehicle:
            vehicle.status = VehicleStatus.RESERVED
            self._store.vehicles.save(vehicle.vehicle_id, vehicle)
        return self._store.reservations.save(reservation.reservation_id, reservation)

    def get_reservation(self, reservation_id: str) -> Reservation:
        item = self._store.reservations.get(reservation_id)
        if item is None:
            raise NotFoundError("Reservation", reservation_id)
        return item

    def add_inspection(self, inspection: Inspection) -> Inspection:
        return self._store.inspections.save(inspection.inspection_id, inspection)

    def create_auction(self, auction: Auction) -> Auction:
        return self._store.auctions.save(auction.auction_id, auction)

    def add_service_record(self, record: ServiceHistory) -> ServiceHistory:
        return self._store.service_history.save(record.record_id, record)

    def add_warranty(self, warranty: Warranty) -> Warranty:
        return self._store.warranties.save(warranty.warranty_id, warranty)

    def stock_summary(self) -> dict:
        if self._store.catalog_vehicles.count():
            from applications.auto_marketplace.inventory_engine.service import inventory_engine

            return inventory_engine.stock_summary()
        vehicles = self._store.vehicles.list_all()
        by_status: dict[str, int] = {}
        for v in vehicles:
            by_status[v.status.value] = by_status.get(v.status.value, 0) + 1
        return {"total": len(vehicles), "by_status": by_status}


inventory_service = InventoryService()
