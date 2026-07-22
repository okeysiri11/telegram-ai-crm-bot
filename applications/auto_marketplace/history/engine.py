# Vehicle History Engine — ownership, mileage, claims, theft/lien.

from __future__ import annotations

import time

from applications.auto_marketplace.marketplace.models import VehicleHistoryRecord
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class HistoryEngine:
    """Aggregate vehicle history by VIN."""

    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def get_or_create(self, *, vin: str, vehicle_id: str = "") -> VehicleHistoryRecord:
        vin = (vin or "").strip().upper()
        if not vin:
            raise ValidationError("vin is required")
        existing = self._store.vehicle_histories.get(vin)
        if existing:
            return existing
        record = VehicleHistoryRecord(vin=vin, vehicle_id=vehicle_id)
        return self._store.vehicle_histories.save(vin, record)

    def get(self, vin: str) -> VehicleHistoryRecord:
        record = self._store.vehicle_histories.get((vin or "").strip().upper())
        if record is None:
            raise NotFoundError("VehicleHistory", vin)
        return record

    def add_ownership(self, vin: str, owner: str, *, from_date: str = "", to_date: str = "") -> VehicleHistoryRecord:
        record = self.get_or_create(vin=vin)
        record.ownership.append({"owner": owner, "from": from_date, "to": to_date, "at": time.time()})
        record.updated_at = time.time()
        return self._store.vehicle_histories.save(record.vin, record)

    def add_registration(self, vin: str, region: str, plate: str = "") -> VehicleHistoryRecord:
        record = self.get_or_create(vin=vin)
        record.registrations.append({"region": region, "plate": plate, "at": time.time()})
        record.updated_at = time.time()
        return self._store.vehicle_histories.save(record.vin, record)

    def add_mileage(self, vin: str, mileage_km: int, *, source: str = "odometer") -> VehicleHistoryRecord:
        record = self.get_or_create(vin=vin)
        record.mileage.append({"mileage_km": mileage_km, "source": source, "at": time.time()})
        record.updated_at = time.time()
        return self._store.vehicle_histories.save(record.vin, record)

    def add_claim(self, vin: str, amount: float, *, description: str = "") -> VehicleHistoryRecord:
        record = self.get_or_create(vin=vin)
        record.insurance_claims.append({"amount": amount, "description": description, "at": time.time()})
        record.updated_at = time.time()
        return self._store.vehicle_histories.save(record.vin, record)

    def add_accident(self, vin: str, severity: str, *, description: str = "") -> VehicleHistoryRecord:
        record = self.get_or_create(vin=vin)
        record.accidents.append({"severity": severity, "description": description, "at": time.time()})
        record.updated_at = time.time()
        return self._store.vehicle_histories.save(record.vin, record)

    def add_repair(self, vin: str, description: str, *, cost: float = 0.0) -> VehicleHistoryRecord:
        record = self.get_or_create(vin=vin)
        record.repairs.append({"description": description, "cost": cost, "at": time.time()})
        record.updated_at = time.time()
        return self._store.vehicle_histories.save(record.vin, record)

    def add_service(self, vin: str, description: str, *, mileage_km: int = 0) -> VehicleHistoryRecord:
        record = self.get_or_create(vin=vin)
        record.service_records.append({"description": description, "mileage_km": mileage_km, "at": time.time()})
        record.updated_at = time.time()
        return self._store.vehicle_histories.save(record.vin, record)

    def add_import_export(self, vin: str, direction: str, country: str) -> VehicleHistoryRecord:
        record = self.get_or_create(vin=vin)
        record.import_export.append({"direction": direction, "country": country, "at": time.time()})
        record.updated_at = time.time()
        return self._store.vehicle_histories.save(record.vin, record)

    def set_theft_status(self, vin: str, status: str) -> VehicleHistoryRecord:
        record = self.get_or_create(vin=vin)
        record.theft_status = status
        record.updated_at = time.time()
        return self._store.vehicle_histories.save(record.vin, record)

    def set_lien_status(self, vin: str, status: str) -> VehicleHistoryRecord:
        record = self.get_or_create(vin=vin)
        record.lien_status = status
        record.updated_at = time.time()
        return self._store.vehicle_histories.save(record.vin, record)

    def add_inspection(self, vin: str, score: float, *, findings: list[str] | None = None) -> VehicleHistoryRecord:
        record = self.get_or_create(vin=vin)
        record.inspections.append({"score": score, "findings": findings or [], "at": time.time()})
        record.updated_at = time.time()
        return self._store.vehicle_histories.save(record.vin, record)

    def summary(self, vin: str) -> dict:
        record = self.get(vin)
        return {
            "vin": record.vin,
            "owners": len(record.ownership),
            "accidents": len(record.accidents),
            "claims": len(record.insurance_claims),
            "theft_status": record.theft_status,
            "lien_status": record.lien_status,
            "latest_mileage": record.mileage[-1]["mileage_km"] if record.mileage else None,
        }

    def metrics(self) -> dict:
        return {"vehicle_histories": self._store.vehicle_histories.count()}


history_engine = HistoryEngine()
