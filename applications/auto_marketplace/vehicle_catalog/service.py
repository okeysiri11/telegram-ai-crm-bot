# VehicleCatalogService — enterprise catalog CRUD and bulk operations.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.specifications.models import InventoryVehicleStatus
from applications.auto_marketplace.vehicle_catalog.ai_integration import CatalogAIIntegration, catalog_ai
from applications.auto_marketplace.vehicle_catalog.duplicate_detector import DuplicateDetector, duplicate_detector
from applications.auto_marketplace.vehicle_catalog.events import VehicleAddedEvent, VehicleUpdatedEvent
from applications.auto_marketplace.vehicle_catalog.models import CatalogVehicle
from applications.auto_marketplace.vehicle_catalog.vin_validator import validate_vin


class VehicleCatalogService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        duplicates: DuplicateDetector | None = None,
        ai: CatalogAIIntegration | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._duplicates = duplicates or duplicate_detector
        self._ai = ai or catalog_ai

    def _sync_legacy(self, vehicle: CatalogVehicle) -> None:
        from applications.auto_marketplace.shared.models import Vehicle, VehicleSpecification, VehicleStatus

        status_map = {
            InventoryVehicleStatus.LISTED.value: VehicleStatus.LISTED,
            InventoryVehicleStatus.AVAILABLE.value: VehicleStatus.LISTED,
            InventoryVehicleStatus.RESERVED.value: VehicleStatus.RESERVED,
            InventoryVehicleStatus.SOLD.value: VehicleStatus.SOLD,
            InventoryVehicleStatus.ARCHIVED.value: VehicleStatus.ARCHIVED,
        }
        legacy = Vehicle(
            vehicle_id=vehicle.vehicle_id,
            dealer_id=vehicle.dealer_id,
            specification=VehicleSpecification(
                make=vehicle.brand,
                model=vehicle.model,
                year=vehicle.year,
                trim=vehicle.trim,
                mileage_km=vehicle.mileage_km,
                vin=vehicle.vin,
                transmission=vehicle.transmission.value,
                drivetrain=vehicle.drive_type.value,
                fuel_type=vehicle.fuel_type.value,
                color_exterior=vehicle.color_exterior.name,
            ),
            status=status_map.get(vehicle.status.value, VehicleStatus.DRAFT),
            price=vehicle.price,
            currency=vehicle.currency,
            description=vehicle.description,
        )
        self._store.vehicles.save(vehicle.vehicle_id, legacy)

    async def create(self, vehicle: CatalogVehicle, *, skip_vin_check: bool = False) -> CatalogVehicle:
        if vehicle.vin and not skip_vin_check:
            ok, msg = validate_vin(vehicle.vin)
            if not ok:
                raise ValidationError(msg)
        existing = self._store.catalog_vehicles.list_all()
        dupes = self._duplicates.find_duplicates(vehicle, existing)
        if dupes:
            vehicle.duplicate_of = dupes[0].vehicle_id
        vehicle.category = await self._ai.auto_categorize(vehicle)
        vehicle.tags = await self._ai.auto_tag(vehicle)
        vehicle.quality_score = await self._ai.quality_score(vehicle)
        if not vehicle.price:
            vehicle.price = await self._ai.price_estimate(vehicle)
        vehicle.updated_at = time.time()
        saved = self._store.catalog_vehicles.save(vehicle.vehicle_id, vehicle)
        self._sync_legacy(saved)
        await publish(VehicleAddedEvent(vehicle_id=saved.vehicle_id, vin=saved.vin, dealer_id=saved.dealer_id))
        return saved

    def get(self, vehicle_id: str) -> CatalogVehicle:
        vehicle = self._store.catalog_vehicles.get(vehicle_id)
        if vehicle is None:
            raise NotFoundError("CatalogVehicle", vehicle_id)
        return vehicle

    def list_vehicles(
        self,
        *,
        status: InventoryVehicleStatus | None = None,
        dealer_id: str | None = None,
        include_archived: bool = False,
    ) -> list[CatalogVehicle]:
        items = self._store.catalog_vehicles.list_all()
        if not include_archived:
            items = [v for v in items if v.status != InventoryVehicleStatus.ARCHIVED]
        if status:
            items = [v for v in items if v.status == status]
        if dealer_id:
            items = [v for v in items if v.dealer_id == dealer_id]
        return items

    async def update(self, vehicle_id: str, **updates: Any) -> CatalogVehicle:
        vehicle = self.get(vehicle_id)
        changed: dict[str, Any] = {}
        for key, value in updates.items():
            if hasattr(vehicle, key) and value is not None:
                setattr(vehicle, key, value)
                changed[key] = value
        if "vin" in changed and vehicle.vin:
            ok, msg = validate_vin(vehicle.vin)
            if not ok:
                raise ValidationError(msg)
        vehicle.updated_at = time.time()
        saved = self._store.catalog_vehicles.save(vehicle_id, vehicle)
        self._sync_legacy(saved)
        await publish(VehicleUpdatedEvent(vehicle_id=vehicle_id, fields=changed))
        return saved

    async def bulk_import(self, vehicles: list[CatalogVehicle]) -> dict[str, Any]:
        created = []
        errors = []
        for vehicle in vehicles:
            try:
                created.append(await self.create(vehicle, skip_vin_check=False))
            except ValidationError as exc:
                errors.append({"vin": vehicle.vin, "error": str(exc)})
        return {"created": len(created), "errors": errors, "items": [v.to_dict() for v in created]}

    async def bulk_update(self, updates: list[dict[str, Any]]) -> dict[str, Any]:
        updated = []
        for item in updates:
            vid = item.pop("vehicle_id", None)
            if not vid:
                continue
            updated.append(await self.update(vid, **item))
        return {"updated": len(updated), "items": [v.to_dict() for v in updated]}

    async def archive(self, vehicle_id: str) -> CatalogVehicle:
        vehicle = await self.update(vehicle_id, status=InventoryVehicleStatus.ARCHIVED)
        vehicle.archived_at = time.time()
        return self._store.catalog_vehicles.save(vehicle_id, vehicle)

    async def restore(self, vehicle_id: str) -> CatalogVehicle:
        vehicle = self.get(vehicle_id)
        vehicle.archived_at = None
        return await self.update(vehicle_id, status=InventoryVehicleStatus.AVAILABLE)

    def find_by_vin(self, vin: str) -> CatalogVehicle | None:
        normalized = vin.strip().upper()
        for vehicle in self._store.catalog_vehicles.list_all():
            if vehicle.vin.upper() == normalized:
                return vehicle
        return None

    def duplicate_check(self, vehicle_id: str) -> list[CatalogVehicle]:
        vehicle = self.get(vehicle_id)
        return self._duplicates.find_duplicates(vehicle, self._store.catalog_vehicles.list_all())


vehicle_catalog_service = VehicleCatalogService()
