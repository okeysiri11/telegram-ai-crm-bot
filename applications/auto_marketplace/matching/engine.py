# Vehicle Matching Engine — similarity and preference matching.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class MatchingEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def _vehicles(self) -> list[Any]:
        items = self._store.vehicles.list_all()
        return items or self._store.catalog_vehicles.list_all()

    def similar(self, vehicle_id: str, *, limit: int = 5) -> list[dict]:
        source = self._store.vehicles.get(vehicle_id) or self._store.catalog_vehicles.get(vehicle_id)
        if source is None:
            return []
        spec = getattr(source, "specification", None)
        make = getattr(spec, "make", "") if spec else getattr(source, "brand", "")
        price = getattr(source, "price", 0) or 0
        results = []
        for vehicle in self._vehicles():
            vid = getattr(vehicle, "vehicle_id", "")
            if vid == vehicle_id:
                continue
            vspec = getattr(vehicle, "specification", None)
            vmake = getattr(vspec, "make", "") if vspec else getattr(vehicle, "brand", "")
            vprice = getattr(vehicle, "price", 0) or 0
            score = 50.0
            if vmake and make and vmake.lower() == make.lower():
                score += 30
            if price and abs(vprice - price) / max(price, 1) < 0.2:
                score += 20
            results.append({"vehicle_id": vid, "score": score, "vehicle": vehicle.to_dict() if hasattr(vehicle, "to_dict") else {}})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]

    def match_preferences(self, preferences: dict, *, limit: int = 5) -> list[dict]:
        budget = float(preferences.get("budget_max", 1_000_000) or 1_000_000)
        make = str(preferences.get("make", "")).lower()
        body = str(preferences.get("body", "")).lower()
        results = []
        for vehicle in self._vehicles():
            price = getattr(vehicle, "price", 0) or 0
            if price > budget:
                continue
            spec = getattr(vehicle, "specification", None)
            vmake = (getattr(spec, "make", "") if spec else "").lower()
            vbody = (getattr(spec, "body_type", "") if spec else "").lower()
            score = 40.0 + (30 if make and make == vmake else 0) + (20 if body and body in vbody else 0)
            if price <= budget * 0.9:
                score += 10
            vid = getattr(vehicle, "vehicle_id", "")
            results.append({"vehicle_id": vid, "score": score, "vehicle": vehicle.to_dict() if hasattr(vehicle, "to_dict") else {}})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]

    def metrics(self) -> dict:
        return {"catalog_size": len(self._vehicles())}


matching_engine = MatchingEngine()
