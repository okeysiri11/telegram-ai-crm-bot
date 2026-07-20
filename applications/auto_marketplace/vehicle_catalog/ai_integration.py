# AI integration hooks for vehicle catalog.

from __future__ import annotations

import logging
from typing import Any

from applications.auto_marketplace.vehicle_catalog.models import CatalogVehicle

logger = logging.getLogger(__name__)


class CatalogAIIntegration:
    @staticmethod
    async def recommend_similar(vehicle: CatalogVehicle, *, limit: int = 5) -> list[dict[str, Any]]:
        try:
            from applications.auto_marketplace.filters.criteria import VehicleSearchCriteria
            from applications.auto_marketplace.filters.search_engine import search_engine

            criteria = VehicleSearchCriteria(
                brand=vehicle.brand,
                model=vehicle.model,
                limit=limit,
            )
            return await search_engine.search(criteria)
        except Exception:
            logger.debug("recommendation fallback")
            return []

    @staticmethod
    async def detect_duplicates_ai(vehicle: CatalogVehicle, candidates: list[CatalogVehicle]) -> list[str]:
        try:
            from platform_reasoning import reasoning_engine
            from platform_reasoning.models import ReasoningContext

            context = ReasoningContext(
                request="Detect duplicate vehicles",
                metadata={
                    "vehicle": vehicle.to_dict(),
                    "candidates": [c.to_dict() for c in candidates[:20]],
                },
            )
            result = await reasoning_engine.reason(context)
            if hasattr(result, "conclusion") and result.conclusion:
                ids = result.conclusion.get("duplicate_ids", [])
                return [str(i) for i in ids]
        except Exception:
            logger.debug("ai duplicate detection fallback")
        return []

    @staticmethod
    async def auto_categorize(vehicle: CatalogVehicle) -> str:
        body = vehicle.category
        if body:
            return body
        brand = vehicle.brand.lower()
        if "tesla" in brand or vehicle.fuel_type.value == "electric":
            return "electric"
        if vehicle.year >= 2023:
            return "new_arrival"
        if vehicle.mileage_km < 30000:
            return "low_mileage"
        return "standard"

    @staticmethod
    async def auto_tag(vehicle: CatalogVehicle) -> list[str]:
        tags = list(vehicle.tags)
        category = await CatalogAIIntegration.auto_categorize(vehicle)
        if category not in tags:
            tags.append(category)
        if vehicle.condition.value == "certified":
            tags.append("certified")
        if vehicle.price < 15000:
            tags.append("budget")
        return tags

    @staticmethod
    async def quality_score(vehicle: CatalogVehicle) -> float:
        score = 50.0
        if vehicle.media_ids:
            score += min(len(vehicle.media_ids) * 5, 20)
        if vehicle.description:
            score += 10
        if vehicle.features:
            score += min(len(vehicle.features) * 2, 10)
        if vehicle.vin:
            score += 5
        if vehicle.mileage_km < 50000:
            score += 5
        return min(score, 100.0)

    @staticmethod
    async def price_estimate(vehicle: CatalogVehicle) -> float:
        try:
            from applications.auto_marketplace.pricing.service import pricing_service

            from applications.auto_marketplace.shared.models import Vehicle, VehicleSpecification

            legacy = Vehicle(
                specification=VehicleSpecification(
                    make=vehicle.brand,
                    model=vehicle.model,
                    year=vehicle.year,
                    mileage_km=vehicle.mileage_km,
                    vin=vehicle.vin,
                ),
                price=vehicle.price,
            )
            return pricing_service.estimate_vehicle_price(legacy)
        except Exception:
            return vehicle.price


catalog_ai = CatalogAIIntegration()
