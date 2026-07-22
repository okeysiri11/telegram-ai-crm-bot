# Service History — unified vehicle service timeline.

from __future__ import annotations

from applications.auto_marketplace.service_centers.models import VehicleServiceRecord
from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ServiceHistoryEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def add(self, record: VehicleServiceRecord) -> VehicleServiceRecord:
        if not record.vehicle_id and not record.vin:
            raise ValidationError("vehicle_id or vin is required")
        return self._store.vehicle_service_records.save(record.record_id, record)

    def for_vehicle(self, *, vehicle_id: str = "", vin: str = "") -> list[VehicleServiceRecord]:
        items = self._store.vehicle_service_records.list_all()
        if vehicle_id:
            items = [r for r in items if r.vehicle_id == vehicle_id]
        if vin:
            items = [r for r in items if r.vin.upper() == vin.upper()]
        return sorted(items, key=lambda r: r.created_at)

    def complete_history(self, vehicle_id: str) -> dict:
        records = self.for_vehicle(vehicle_id=vehicle_id)
        by_kind: dict[str, list] = {}
        for r in records:
            by_kind.setdefault(r.kind, []).append(r.to_dict())
        return {
            "vehicle_id": vehicle_id,
            "total": len(records),
            "maintenance": by_kind.get("maintenance", []),
            "repairs": by_kind.get("repair", []),
            "parts": by_kind.get("parts", []),
            "invoices": by_kind.get("invoice", []),
            "warranty": by_kind.get("warranty", []),
            "all": [r.to_dict() for r in records],
        }

    def metrics(self) -> dict:
        return {"vehicle_service_records": self._store.vehicle_service_records.count()}


service_history_engine = ServiceHistoryEngine()
