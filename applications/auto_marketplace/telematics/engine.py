# Telematics — GPS, OBD, fuel, mileage, behavior, EV battery, diagnostics.

from __future__ import annotations

from applications.auto_marketplace.fleet.models import TelematicsReading
from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class TelematicsEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def ingest(self, reading: TelematicsReading) -> TelematicsReading:
        if not reading.fleet_vehicle_id:
            raise ValidationError("fleet_vehicle_id is required")
        vehicle = self._store.fleet_vehicles.get(reading.fleet_vehicle_id)
        if vehicle:
            vehicle.mileage_km = max(vehicle.mileage_km, reading.mileage_km)
            if reading.fuel_l_per_100km:
                vehicle.fuel_level_pct = max(0.0, vehicle.fuel_level_pct - 0.5)
            self._store.fleet_vehicles.save(vehicle.fleet_vehicle_id, vehicle)
        return self._store.telematics_readings.save(reading.reading_id, reading)

    def latest(self, fleet_vehicle_id: str) -> TelematicsReading | None:
        items = [r for r in self._store.telematics_readings.list_all() if r.fleet_vehicle_id == fleet_vehicle_id]
        if not items:
            return None
        return sorted(items, key=lambda r: r.created_at)[-1]

    def live_map(self, fleet_id: str = "") -> list[dict]:
        vehicles = self._store.fleet_vehicles.list_all()
        if fleet_id:
            vehicles = [v for v in vehicles if v.fleet_id == fleet_id]
        out = []
        for v in vehicles:
            reading = self.latest(v.fleet_vehicle_id)
            out.append(
                {
                    "fleet_vehicle_id": v.fleet_vehicle_id,
                    "label": v.label,
                    "lat": reading.lat if reading else 0.0,
                    "lon": reading.lon if reading else 0.0,
                    "status": v.status.value,
                }
            )
        return out

    def metrics(self) -> dict:
        return {"readings": self._store.telematics_readings.count()}


telematics_engine = TelematicsEngine()
