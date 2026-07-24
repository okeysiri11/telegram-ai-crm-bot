"""Service catalog — Sprint 22.2."""

from __future__ import annotations

from typing import Any


class ServiceCatalog:
    def create(
        self,
        *,
        name: str,
        category: str,
        duration_min: int,
        price: float,
        materials: list[dict[str, Any]] | None = None,
        performers: list[str] | None = None,
        description: str = "",
        photos: list[str] | None = None,
    ) -> dict[str, Any]:
        if not name or not category:
            raise ValueError("service name and category are required")
        if duration_min <= 0 or price < 0:
            raise ValueError("invalid duration or price")
        return {
            "name": name.strip(),
            "category": category,
            "duration_min": duration_min,
            "price": price,
            "materials": list(materials or []),
            "performers": list(performers or []),
            "photos": list(photos or []),
            "description": description,
        }

    def seed(self) -> list[dict[str, Any]]:
        return [
            self.create(name="Haircut", category="hair", duration_min=45, price=40.0),
            self.create(name="Manicure", category="nails", duration_min=60, price=35.0),
            self.create(name="Facial", category="skin", duration_min=75, price=70.0),
        ]
