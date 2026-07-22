# Vehicles Engine — Sprint 10.1 vehicle domain surface.

from __future__ import annotations

import time

from applications.auto_marketplace.catalog.service import CatalogService, catalog_service
from applications.auto_marketplace.foundation.models import (
    CatalogCategory,
    Configuration,
    Generation,
    VIN,
    VehicleBrand,
    VehicleModel,
)
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.models import Vehicle, VehicleStatus
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class VehiclesEngine:
    """Vehicle lifecycle and taxonomy for Auto Marketplace foundation."""

    def __init__(
        self,
        store: MarketplaceStore | None = None,
        catalog: CatalogService | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._catalog = catalog or catalog_service

    def categories(self) -> list[str]:
        return [c.value for c in CatalogCategory]

    def create(self, vehicle: Vehicle) -> Vehicle:
        return self._catalog.create_vehicle(vehicle)

    def get(self, vehicle_id: str) -> Vehicle:
        return self._catalog.get_vehicle(vehicle_id)

    def list_vehicles(self, *, status: VehicleStatus | None = None, category: str | None = None) -> list[Vehicle]:
        items = self._catalog.list_vehicles(status=status)
        if category:
            items = [
                v
                for v in items
                if (getattr(v, "category", None) or getattr(v.specification, "body_type", "") or "").lower()
                == category.lower()
                or category.lower() in (v.description or "").lower()
                or category.lower() in " ".join(v.features or []).lower()
            ]
        return items

    def publish(self, vehicle_id: str) -> Vehicle:
        return self._catalog.publish_vehicle(vehicle_id)

    def register_brand(self, brand: VehicleBrand) -> VehicleBrand:
        if not brand.name:
            raise ValidationError("brand name is required")
        return self._store.vehicle_brands.save(brand.brand_id, brand)

    def register_model(self, model: VehicleModel) -> VehicleModel:
        if not model.name or not model.brand_id:
            raise ValidationError("model name and brand_id are required")
        return self._store.vehicle_models.save(model.model_id, model)

    def register_generation(self, generation: Generation) -> Generation:
        return self._store.vehicle_generations.save(generation.generation_id, generation)

    def register_configuration(self, configuration: Configuration) -> Configuration:
        return self._store.vehicle_configurations.save(configuration.configuration_id, configuration)

    def list_brands(self) -> list[VehicleBrand]:
        return self._store.vehicle_brands.list_all()

    def list_models(self, brand_id: str | None = None) -> list[VehicleModel]:
        items = self._store.vehicle_models.list_all()
        if brand_id:
            items = [m for m in items if m.brand_id == brand_id]
        return items

    def parse_vin(self, vin: str) -> VIN:
        cleaned = (vin or "").strip().upper().replace(" ", "")
        if len(cleaned) != 17 or any(ch in cleaned for ch in "IOQ"):
            return VIN(vin=cleaned, valid=False, detail="VIN must be 17 chars without I/O/Q")
        return VIN(
            vin=cleaned,
            valid=True,
            wmi=cleaned[:3],
            vds=cleaned[3:9],
            vis=cleaned[9:],
            detail="ok",
        )

    def metrics(self) -> dict:
        return {
            "vehicles": self._store.vehicles.count(),
            "brands": self._store.vehicle_brands.count(),
            "models": self._store.vehicle_models.count(),
            "generations": self._store.vehicle_generations.count(),
            "configurations": self._store.vehicle_configurations.count(),
            "categories": self.categories(),
        }


vehicles_engine = VehiclesEngine()
