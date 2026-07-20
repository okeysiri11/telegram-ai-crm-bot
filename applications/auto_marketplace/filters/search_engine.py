# SearchEngine — structured and AI semantic vehicle search.

from __future__ import annotations

import logging
from typing import Any

from applications.auto_marketplace.filters.criteria import VehicleSearchCriteria
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.specifications.models import InventoryVehicleStatus
from applications.auto_marketplace.vehicle_catalog.models import CatalogVehicle
from applications.auto_marketplace.vehicle_catalog.service import VehicleCatalogService, vehicle_catalog_service
from applications.auto_marketplace.vehicle_catalog.vin_validator import normalize_vin

logger = logging.getLogger(__name__)


class SearchEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        catalog: VehicleCatalogService | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._catalog = catalog or vehicle_catalog_service

    def _matches(self, vehicle: CatalogVehicle, criteria: VehicleSearchCriteria) -> bool:
        if vehicle.status == InventoryVehicleStatus.ARCHIVED:
            return False
        if criteria.vin:
            if normalize_vin(vehicle.vin) != normalize_vin(criteria.vin):
                return False
        if criteria.brand and criteria.brand.lower() not in vehicle.brand.lower():
            return False
        if criteria.model and criteria.model.lower() not in vehicle.model.lower():
            return False
        if criteria.year_min is not None and vehicle.year < criteria.year_min:
            return False
        if criteria.year_max is not None and vehicle.year > criteria.year_max:
            return False
        if criteria.mileage_min is not None and vehicle.mileage_km < criteria.mileage_min:
            return False
        if criteria.mileage_max is not None and vehicle.mileage_km > criteria.mileage_max:
            return False
        if criteria.price_min is not None and vehicle.price < criteria.price_min:
            return False
        if criteria.price_max is not None and vehicle.price > criteria.price_max:
            return False
        if criteria.fuel_type and vehicle.fuel_type != criteria.fuel_type:
            return False
        if criteria.transmission and vehicle.transmission != criteria.transmission:
            return False
        if criteria.dealer_id and vehicle.dealer_id != criteria.dealer_id:
            return False
        if criteria.warehouse_id and vehicle.warehouse_id != criteria.warehouse_id:
            return False
        if criteria.city and criteria.city.lower() not in vehicle.location.city.lower():
            return False
        if criteria.country and criteria.country.lower() not in vehicle.location.country.lower():
            return False
        if criteria.tags and not all(t in vehicle.tags for t in criteria.tags):
            return False
        if criteria.query:
            q = criteria.query.lower()
            haystack = f"{vehicle.brand} {vehicle.model} {vehicle.description} {' '.join(vehicle.tags)}".lower()
            if q not in haystack:
                return False
        return True

    async def _semantic_rank(self, vehicles: list[CatalogVehicle], query: str) -> list[CatalogVehicle]:
        if not query or not vehicles:
            return vehicles
        try:
            from platform_memory import memory_service

            for vehicle in vehicles:
                await memory_service.remember_semantic(
                    content=f"{vehicle.brand} {vehicle.model} {vehicle.description}",
                    metadata={"vehicle_id": vehicle.vehicle_id},
                )
            results = await memory_service.search_semantic(query=query, limit=len(vehicles))
            ranked_ids = [r.get("metadata", {}).get("vehicle_id") for r in results if isinstance(r, dict)]
            id_order = {vid: i for i, vid in enumerate(ranked_ids) if vid}
            return sorted(vehicles, key=lambda v: id_order.get(v.vehicle_id, 999))
        except Exception:
            logger.debug("semantic search fallback to text match")
            return vehicles

    async def search(self, criteria: VehicleSearchCriteria | None = None) -> list[dict[str, Any]]:
        criteria = criteria or VehicleSearchCriteria()
        if criteria.vin:
            vehicle = self._catalog.find_by_vin(criteria.vin)
            return [vehicle.to_dict()] if vehicle else []

        matched = [v for v in self._catalog.list_vehicles(include_archived=False) if self._matches(v, criteria)]
        if criteria.semantic and criteria.query:
            matched = await self._semantic_rank(matched, criteria.query)
        return [v.to_dict() for v in matched[: criteria.limit]]


search_engine = SearchEngine()
