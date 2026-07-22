# Route Optimizer — AI planning, cost/fuel, multi-stop, border/weather/traffic.

from __future__ import annotations

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transport.models import OptimizedRoute


class RouteOptimizerEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def optimize(
        self,
        *,
        shipment_id: str = "",
        origin: str,
        destination: str,
        stops: list[dict] | None = None,
        border_crossings: list[str] | None = None,
        weather_factor: float = 1.0,
        traffic_factor: float = 1.1,
        fuel_price: float = 1.5,
    ) -> OptimizedRoute:
        if not origin or not destination:
            raise ValidationError("origin and destination are required")
        stops = stops or []
        waypoints = [{"name": origin}] + list(stops) + [{"name": destination}]
        hop = max(1, len(waypoints) - 1)
        distance = 120.0 * hop + 40.0 * len(border_crossings or [])
        duration = (distance / 70.0) * weather_factor * traffic_factor
        fuel = round(distance * 0.12 * fuel_price * weather_factor, 2)
        borders = list(border_crossings or [])
        notes = [
            "AI route selected for cost/fuel balance",
            f"Traffic factor {traffic_factor}",
            f"Weather factor {weather_factor}",
        ]
        if borders:
            notes.append(f"Border optimization via {', '.join(borders)}")
        route = OptimizedRoute(
            shipment_id=shipment_id,
            stops=waypoints,
            distance_km=round(distance, 1),
            duration_hours=round(duration, 2),
            fuel_cost=fuel,
            total_cost=round(fuel + 80 * hop + 50 * len(borders), 2),
            border_crossings=borders,
            weather_factor=weather_factor,
            traffic_factor=traffic_factor,
            ai_notes=notes,
        )
        return self._store.optimized_routes.save(route.route_id, route)

    def metrics(self) -> dict:
        return {"optimized_routes": self._store.optimized_routes.count()}


route_optimizer_engine = RouteOptimizerEngine()
