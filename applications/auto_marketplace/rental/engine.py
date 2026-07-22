# Rental Engine — short/long/corporate rentals, pricing, returns, damage.

from __future__ import annotations

import time

from applications.auto_marketplace.fleet.models import (
    FleetVehicleStatus,
    RentalContract,
    RentalKind,
    RentalStatus,
)
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class RentalEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def price(self, *, kind: RentalKind = RentalKind.SHORT, days: int = 1, base_daily: float = 45.0) -> dict:
        if days <= 0:
            raise ValidationError("days must be positive")
        mult = 1.0 if kind == RentalKind.SHORT else 0.85 if kind == RentalKind.LONG else 0.75
        daily = round(base_daily * mult, 2)
        return {"kind": kind.value, "days": days, "daily_rate": daily, "total_price": round(daily * days, 2)}

    def availability(self, fleet_id: str = "") -> list[dict]:
        items = self._store.fleet_vehicles.list_all()
        if fleet_id:
            items = [v for v in items if v.fleet_id == fleet_id]
        return [
            {"fleet_vehicle_id": v.fleet_vehicle_id, "label": v.label, "status": v.status.value}
            for v in items
            if v.status == FleetVehicleStatus.AVAILABLE
        ]

    def reserve(self, rental: RentalContract) -> RentalContract:
        vehicle = self._store.fleet_vehicles.get(rental.fleet_vehicle_id)
        if vehicle is None:
            raise NotFoundError("FleetVehicle", rental.fleet_vehicle_id)
        if vehicle.status != FleetVehicleStatus.AVAILABLE:
            raise ValidationError("vehicle not available")
        if not rental.starts_at:
            rental.starts_at = time.time()
        if not rental.ends_at:
            rental.ends_at = rental.starts_at + 86400
        days = max(1, int((rental.ends_at - rental.starts_at) / 86400))
        priced = self.price(kind=rental.kind, days=days, base_daily=rental.daily_rate or 45.0)
        rental.daily_rate = priced["daily_rate"]
        rental.total_price = priced["total_price"]
        rental.contract_text = (
            f"Rental {rental.kind.value} for {rental.fleet_vehicle_id} "
            f"customer {rental.customer_id}: {days} day(s) @ {rental.daily_rate}"
        )
        rental.status = RentalStatus.RESERVED
        vehicle.status = FleetVehicleStatus.RENTED
        self._store.fleet_vehicles.save(vehicle.fleet_vehicle_id, vehicle)
        return self._store.rental_contracts.save(rental.rental_id, rental)

    def activate(self, rental_id: str) -> RentalContract:
        rental = self._get(rental_id)
        rental.status = RentalStatus.ACTIVE
        return self._store.rental_contracts.save(rental_id, rental)

    def return_vehicle(self, rental_id: str, *, damage: str = "", damage_cost: float = 0.0) -> RentalContract:
        rental = self._get(rental_id)
        if damage:
            rental.damage_reports.append({"description": damage, "cost": damage_cost, "at": time.time()})
        rental.status = RentalStatus.RETURNED
        vehicle = self._store.fleet_vehicles.get(rental.fleet_vehicle_id)
        if vehicle:
            vehicle.status = FleetVehicleStatus.AVAILABLE
            vehicle.revenue = round(vehicle.revenue + rental.total_price, 2)
            if damage_cost:
                vehicle.costs["other"] = round(vehicle.costs.get("other", 0) + damage_cost, 2)
            self._store.fleet_vehicles.save(vehicle.fleet_vehicle_id, vehicle)
        return self._store.rental_contracts.save(rental_id, rental)

    def _get(self, rental_id: str) -> RentalContract:
        item = self._store.rental_contracts.get(rental_id)
        if item is None:
            raise NotFoundError("RentalContract", rental_id)
        return item

    def list_rentals(self, *, customer_id: str = "") -> list[RentalContract]:
        items = self._store.rental_contracts.list_all()
        if customer_id:
            items = [r for r in items if r.customer_id == customer_id]
        return items

    def metrics(self) -> dict:
        return {"rentals": self._store.rental_contracts.count()}


rental_engine = RentalEngine()
