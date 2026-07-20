# Customer garage and service history.

from __future__ import annotations

from applications.auto_marketplace.authentication.models import GarageVehicle
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class GarageService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def add_vehicle(self, user_id: str, *, vin: str = "", make: str = "", model: str = "", year: int = 0, vehicle_id: str = "") -> GarageVehicle:
        gv = GarageVehicle(user_id=user_id, vin=vin, make=make, model=model, year=year, vehicle_id=vehicle_id)
        return self._store.garage_vehicles.save(gv.garage_id, gv)

    def list_vehicles(self, user_id: str) -> list[GarageVehicle]:
        return [g for g in self._store.garage_vehicles.list_all() if g.user_id == user_id]

    def add_service_record(self, garage_id: str, record: dict) -> GarageVehicle:
        gv = self._store.garage_vehicles.get(garage_id)
        if gv is None:
            raise ValueError(f"Garage vehicle not found: {garage_id}")
        gv.service_records.append(record)
        return self._store.garage_vehicles.save(garage_id, gv)

    def service_history(self, user_id: str) -> list[dict]:
        records: list[dict] = []
        for gv in self.list_vehicles(user_id):
            for rec in gv.service_records:
                records.append({**rec, "garage_id": gv.garage_id, "vehicle": f"{gv.make} {gv.model}"})
        for sh in self._store.service_history.list_all():
            records.append(sh.to_dict() if hasattr(sh, "to_dict") else {"record": str(sh)})
        return records


garage_service = GarageService()
