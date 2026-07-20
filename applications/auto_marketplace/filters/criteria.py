# Search filter criteria.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from applications.auto_marketplace.specifications.models import FuelType, Transmission


@dataclass
class VehicleSearchCriteria:
    query: str = ""
    vin: str = ""
    brand: str = ""
    model: str = ""
    year_min: int | None = None
    year_max: int | None = None
    mileage_min: int | None = None
    mileage_max: int | None = None
    price_min: float | None = None
    price_max: float | None = None
    fuel_type: FuelType | None = None
    transmission: Transmission | None = None
    city: str = ""
    country: str = ""
    dealer_id: str = ""
    warehouse_id: str = ""
    tags: list[str] = field(default_factory=list)
    semantic: bool = False
    limit: int = 50

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "vin": self.vin,
            "brand": self.brand,
            "model": self.model,
            "year_min": self.year_min,
            "year_max": self.year_max,
            "mileage_min": self.mileage_min,
            "mileage_max": self.mileage_max,
            "price_min": self.price_min,
            "price_max": self.price_max,
            "fuel_type": self.fuel_type.value if self.fuel_type else None,
            "transmission": self.transmission.value if self.transmission else None,
            "city": self.city,
            "country": self.country,
            "dealer_id": self.dealer_id,
            "warehouse_id": self.warehouse_id,
            "tags": list(self.tags),
            "semantic": self.semantic,
            "limit": self.limit,
        }
