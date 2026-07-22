"""AI Vehicle Assistant — Sprint 13.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

CAPABILITIES = [
    "vin_decoder",
    "market_price",
    "damage_prediction",
    "fraud_detection",
    "maintenance_prediction",
    "vehicle_history",
    "purchase_advisor",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIVehicleAssistant:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.capabilities = list(CAPABILITIES)

    def _save(self, capability: str, payload: dict[str, Any]) -> dict[str, Any]:
        rid = _id("eaai")
        result = {"result_id": rid, "capability": capability, **payload, "at": _now()}
        return self.store.ea_ai_results.save(rid, result)

    def decode_vin(self, vin: str) -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        if len(vin) < 11:
            raise ValidationError("VIN must be at least 11 characters")
        cached = self.store.ea_vins.get(vin)
        return self._save(
            "vin_decoder",
            {
                "vin": vin,
                "make": (cached or {}).get("make") or "Unknown",
                "model": (cached or {}).get("model") or "Unknown",
                "year": (cached or {}).get("year"),
                "wmi": vin[:3],
                "decoded": True,
            },
        )

    def estimate_price(
        self,
        *,
        vehicle_id: str = "",
        make: str = "",
        model: str = "",
        year: int | None = None,
        mileage: int = 0,
    ) -> dict[str, Any]:
        vehicle = None
        if vehicle_id:
            vehicle = self.store.ea_vehicles.get(vehicle_id)
            if vehicle is None:
                raise NotFoundError("vehicle", vehicle_id)
            make = vehicle.get("make", make)
            model = vehicle.get("model", model)
            year = vehicle.get("year") or year
            base = float(vehicle.get("price") or 15000)
        else:
            base = 18000.0
        adj = max(0.4, 1.0 - (mileage / 300000.0))
        return self._save(
            "market_price",
            {
                "vehicle_id": vehicle_id,
                "make": make,
                "model": model,
                "year": year,
                "mileage": mileage,
                "estimate": round(base * adj, 2),
                "currency": "USD",
            },
        )

    def predict_damage(self, *, vehicle_id: str, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.store.ea_vehicles.get(vehicle_id) is None:
            raise NotFoundError("vehicle", vehicle_id)
        signals = signals or {}
        score = float(signals.get("impact_score", 0.2))
        return self._save(
            "damage_prediction",
            {
                "vehicle_id": vehicle_id,
                "risk": "high" if score > 0.7 else "medium" if score > 0.35 else "low",
                "score": score,
                "signals": signals,
            },
        )

    def detect_fraud(self, *, vehicle_id: str = "", vin: str = "", listing_price: float = 0.0) -> dict[str, Any]:
        flags: list[str] = []
        if vin and len(vin) < 17:
            flags.append("short_vin")
        if listing_price and listing_price < 1000:
            flags.append("suspicious_price")
        vehicle = self.store.ea_vehicles.get(vehicle_id) if vehicle_id else None
        if vehicle and listing_price and float(vehicle.get("price") or 0) > 0:
            if listing_price < float(vehicle["price"]) * 0.4:
                flags.append("below_market")
        return self._save(
            "fraud_detection",
            {
                "vehicle_id": vehicle_id,
                "vin": vin,
                "listing_price": listing_price,
                "fraudulent": bool(flags),
                "flags": flags,
            },
        )

    def predict_maintenance(self, *, vehicle_id: str, mileage: int = 0) -> dict[str, Any]:
        if self.store.ea_vehicles.get(vehicle_id) is None:
            raise NotFoundError("vehicle", vehicle_id)
        due = []
        if mileage >= 10000:
            due.append("oil_change")
        if mileage >= 40000:
            due.append("timing_belt")
        if mileage >= 80000:
            due.append("major_service")
        return self._save(
            "maintenance_prediction",
            {"vehicle_id": vehicle_id, "mileage": mileage, "due": due or ["inspection"]},
        )

    def vehicle_history(self, *, vin: str) -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        if not vin:
            raise ValidationError("vin required")
        return self._save(
            "vehicle_history",
            {
                "vin": vin,
                "owners": 1,
                "accidents": 0,
                "title_clean": True,
                "service_records": 2,
            },
        )

    def purchase_advisor(
        self,
        *,
        budget: float,
        vehicle_type: str = "car",
        preferences: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        candidates = [
            v
            for v in self.store.ea_vehicles.list_all()
            if v.get("vehicle_type") == vehicle_type and float(v.get("price") or 0) <= float(budget)
        ]
        candidates.sort(key=lambda v: float(v.get("price") or 0), reverse=True)
        top = candidates[:3]
        return self._save(
            "purchase_advisor",
            {
                "budget": budget,
                "vehicle_type": vehicle_type,
                "preferences": preferences or {},
                "recommendations": [v["vehicle_id"] for v in top],
                "advice": "Prefer lower-mileage listings within budget." if top else "No matching inventory; widen budget or type.",
            },
        )

    def run(self, *, capability: str, **kwargs: Any) -> dict[str, Any]:
        mapping = {
            "vin_decoder": lambda: self.decode_vin(kwargs.get("vin", "")),
            "market_price": lambda: self.estimate_price(
                vehicle_id=kwargs.get("vehicle_id", ""),
                make=kwargs.get("make", ""),
                model=kwargs.get("model", ""),
                year=kwargs.get("year"),
                mileage=int(kwargs.get("mileage", 0) or 0),
            ),
            "damage_prediction": lambda: self.predict_damage(
                vehicle_id=kwargs.get("vehicle_id", ""),
                signals=kwargs.get("signals"),
            ),
            "fraud_detection": lambda: self.detect_fraud(
                vehicle_id=kwargs.get("vehicle_id", ""),
                vin=kwargs.get("vin", ""),
                listing_price=float(kwargs.get("listing_price", 0) or 0),
            ),
            "maintenance_prediction": lambda: self.predict_maintenance(
                vehicle_id=kwargs.get("vehicle_id", ""),
                mileage=int(kwargs.get("mileage", 0) or 0),
            ),
            "vehicle_history": lambda: self.vehicle_history(vin=kwargs.get("vin", "")),
            "purchase_advisor": lambda: self.purchase_advisor(
                budget=float(kwargs.get("budget", 0) or 0),
                vehicle_type=kwargs.get("vehicle_type", "car"),
                preferences=kwargs.get("preferences"),
            ),
        }
        if capability not in mapping:
            raise ValidationError(f"capability must be one of {self.capabilities}")
        return mapping[capability]()

    def status(self) -> dict[str, Any]:
        return {"results": self.store.ea_ai_results.count(), "capabilities": self.capabilities}
