# AI Operations — predictive maintenance, optimization, forecasting, risk.

from __future__ import annotations

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class AIOperationsEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def predictive_maintenance(self, fleet_vehicle_id: str) -> dict:
        vehicle = self._store.fleet_vehicles.get(fleet_vehicle_id)
        mileage = vehicle.mileage_km if vehicle else 0
        tire = vehicle.tire_wear_pct if vehicle else 0
        risk = min(0.95, mileage / 200000 + tire / 200)
        return {
            "fleet_vehicle_id": fleet_vehicle_id,
            "maintenance_probability": round(risk, 2),
            "recommendation": "schedule_service" if risk > 0.45 else "monitor",
            "drivers": ["mileage", "tire_wear"],
        }

    def fleet_optimization(self, fleet_id: str = "") -> dict:
        vehicles = self._store.fleet_vehicles.list_all()
        if fleet_id:
            vehicles = [v for v in vehicles if v.fleet_id == fleet_id]
        available = len([v for v in vehicles if v.status.value == "available"])
        return {
            "fleet_id": fleet_id,
            "suggested_pool_size": max(1, available),
            "idle_vehicles": available,
            "action": "rebalance_assignments" if available > 3 else "maintain",
        }

    def demand_forecast(self, days: int = 7) -> dict:
        rentals = self._store.rental_contracts.count()
        bookings = self._store.mobility_bookings.count()
        base = max(1, rentals + bookings)
        return {"days": days, "forecasted_demand": base * days // 7 + 2, "confidence": 0.72}

    def pricing_optimization(self, *, base_daily: float = 45.0, utilization_pct: float = 50.0) -> dict:
        adj = 1.15 if utilization_pct > 70 else 0.9 if utilization_pct < 30 else 1.0
        return {"base_daily": base_daily, "optimized_daily": round(base_daily * adj, 2), "factor": adj}

    def utilization_prediction(self, fleet_id: str = "") -> dict:
        vehicles = self._store.fleet_vehicles.list_all()
        if fleet_id:
            vehicles = [v for v in vehicles if v.fleet_id == fleet_id]
        if not vehicles:
            return {"predicted_utilization_pct": 0.0}
        used = len([v for v in vehicles if v.status.value != "available"])
        return {"predicted_utilization_pct": round(min(95.0, 100 * used / len(vehicles) + 5), 1)}

    def risk_scoring(self, fleet_vehicle_id: str) -> dict:
        vehicle = self._store.fleet_vehicles.get(fleet_vehicle_id)
        score = 0.2
        factors = []
        if vehicle:
            if vehicle.accidents:
                score += 0.3
                factors.append("accidents")
            if vehicle.tire_wear_pct > 70:
                score += 0.2
                factors.append("tires")
            if vehicle.fuel_level_pct < 15:
                score += 0.1
                factors.append("low_fuel")
        return {"fleet_vehicle_id": fleet_vehicle_id, "risk_score": round(min(0.95, score), 2), "factors": factors}

    def driver_recommendations(self, *, min_rating: float = 3.5) -> list[dict]:
        from applications.auto_marketplace.drivers.engine import driver_engine

        return [d.to_dict() for d in driver_engine.recommend(min_rating=min_rating)[:5]]

    def metrics(self) -> dict:
        return {"ai_operations": "1.0"}


ai_operations_engine = AIOperationsEngine()
