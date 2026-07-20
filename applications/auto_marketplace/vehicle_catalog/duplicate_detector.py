# Duplicate vehicle detection.

from __future__ import annotations

from applications.auto_marketplace.vehicle_catalog.models import CatalogVehicle
from applications.auto_marketplace.vehicle_catalog.vin_validator import normalize_vin


class DuplicateDetector:
    def find_duplicates(
        self,
        vehicle: CatalogVehicle,
        existing: list[CatalogVehicle],
    ) -> list[CatalogVehicle]:
        matches: list[CatalogVehicle] = []
        vin = normalize_vin(vehicle.vin)
        for item in existing:
            if item.vehicle_id == vehicle.vehicle_id:
                continue
            if vin and normalize_vin(item.vin) == vin:
                matches.append(item)
                continue
            if (
                item.brand.lower() == vehicle.brand.lower()
                and item.model.lower() == vehicle.model.lower()
                and item.year == vehicle.year
                and item.mileage_km == vehicle.mileage_km
                and item.dealer_id == vehicle.dealer_id
            ):
                matches.append(item)
        return matches

    def is_duplicate(self, vehicle: CatalogVehicle, existing: list[CatalogVehicle]) -> bool:
        return bool(self.find_duplicates(vehicle, existing))


duplicate_detector = DuplicateDetector()
