# Fleet Management — registry, assignment, analytics, fuel, tires, profitability.

from __future__ import annotations

import time

from applications.auto_marketplace.fleet.models import FleetRegistry, FleetVehicle, FleetVehicleStatus
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class FleetEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create_fleet(self, fleet: FleetRegistry) -> FleetRegistry:
        if not fleet.name:
            raise ValidationError("name is required")
        return self._store.fleet_registries.save(fleet.fleet_id, fleet)

    def register_vehicle(self, vehicle: FleetVehicle) -> FleetVehicle:
        if not vehicle.fleet_id:
            raise ValidationError("fleet_id is required")
        if self._store.fleet_registries.get(vehicle.fleet_id) is None:
            raise NotFoundError("FleetRegistry", vehicle.fleet_id)
        return self._store.fleet_vehicles.save(vehicle.fleet_vehicle_id, vehicle)

    def get_vehicle(self, fleet_vehicle_id: str) -> FleetVehicle:
        item = self._store.fleet_vehicles.get(fleet_vehicle_id)
        if item is None:
            raise NotFoundError("FleetVehicle", fleet_vehicle_id)
        return item

    def assign_driver(self, fleet_vehicle_id: str, driver_id: str) -> FleetVehicle:
        vehicle = self.get_vehicle(fleet_vehicle_id)
        vehicle.assigned_driver_id = driver_id
        vehicle.status = FleetVehicleStatus.ASSIGNED
        return self._store.fleet_vehicles.save(fleet_vehicle_id, vehicle)

    def plan_maintenance(self, fleet_vehicle_id: str, *, due_mileage_km: int, note: str = "") -> dict:
        vehicle = self.get_vehicle(fleet_vehicle_id)
        plan = {
            "fleet_vehicle_id": fleet_vehicle_id,
            "due_mileage_km": due_mileage_km,
            "note": note or "Scheduled fleet maintenance",
            "at": time.time(),
        }
        self._store.fleet_maintenance_plans.save(f"{fleet_vehicle_id}:{due_mileage_km}", plan)
        if vehicle.mileage_km >= due_mileage_km:
            vehicle.status = FleetVehicleStatus.MAINTENANCE
            self._store.fleet_vehicles.save(fleet_vehicle_id, vehicle)
        return plan

    def record_fuel(self, fleet_vehicle_id: str, *, liters: float, cost: float, level_pct: float) -> FleetVehicle:
        vehicle = self.get_vehicle(fleet_vehicle_id)
        vehicle.fuel_level_pct = level_pct
        vehicle.costs["fuel"] = round(vehicle.costs.get("fuel", 0) + cost, 2)
        self._store.fleet_fuel_logs.save(
            f"{fleet_vehicle_id}:{time.time()}",
            {"fleet_vehicle_id": fleet_vehicle_id, "liters": liters, "cost": cost, "at": time.time()},
        )
        return self._store.fleet_vehicles.save(fleet_vehicle_id, vehicle)

    def update_tires(self, fleet_vehicle_id: str, wear_pct: float) -> FleetVehicle:
        vehicle = self.get_vehicle(fleet_vehicle_id)
        vehicle.tire_wear_pct = max(0.0, min(100.0, wear_pct))
        return self._store.fleet_vehicles.save(fleet_vehicle_id, vehicle)

    def record_accident(self, fleet_vehicle_id: str, description: str, cost: float = 0.0) -> FleetVehicle:
        vehicle = self.get_vehicle(fleet_vehicle_id)
        vehicle.accidents.append({"description": description, "cost": cost, "at": time.time()})
        vehicle.costs["other"] = round(vehicle.costs.get("other", 0) + cost, 2)
        return self._store.fleet_vehicles.save(fleet_vehicle_id, vehicle)

    def list_vehicles(self, *, fleet_id: str = "") -> list[FleetVehicle]:
        items = self._store.fleet_vehicles.list_all()
        if fleet_id:
            items = [v for v in items if v.fleet_id == fleet_id]
        return items

    def analytics(self, fleet_id: str = "") -> dict:
        vehicles = self.list_vehicles(fleet_id=fleet_id)
        total_cost = sum(sum(v.costs.values()) for v in vehicles)
        revenue = sum(v.revenue for v in vehicles)
        utilized = len([v for v in vehicles if v.status != FleetVehicleStatus.AVAILABLE])
        return {
            "vehicles": len(vehicles),
            "utilized": utilized,
            "utilization_pct": round(100 * utilized / len(vehicles), 1) if vehicles else 0.0,
            "total_cost": round(total_cost, 2),
            "revenue": round(revenue, 2),
            "profitability": round(revenue - total_cost, 2),
        }

    def metrics(self) -> dict:
        return {
            "fleets": self._store.fleet_registries.count(),
            "vehicles": self._store.fleet_vehicles.count(),
            "analytics": self.analytics(),
        }


fleet_engine = FleetEngine()
