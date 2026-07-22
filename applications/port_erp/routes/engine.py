# Route Optimization Engine — hubs, multimodal legs, ETA/cost optimization.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.multimodal.events import RouteOptimizedEvent
from applications.port_erp.multimodal.models import (
    HubType,
    LogisticsRoute,
    RouteHub,
    RouteLeg,
    TransportMode,
)
from applications.port_erp.road.engine import (
    air_transport_engine,
    rail_transport_engine,
    road_transport_engine,
    sea_transport_engine,
)
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


_MODE_ENGINES = {
    TransportMode.ROAD: road_transport_engine,
    TransportMode.RAIL: rail_transport_engine,
    TransportMode.AIR: air_transport_engine,
    TransportMode.SEA: sea_transport_engine,
}


class RouteOptimizationEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def create_hub(self, hub: RouteHub) -> RouteHub:
        if not hub.name:
            raise ValidationError("name is required")
        return self._store.route_hubs.save(hub.hub_id, hub)

    def list_hubs(self, *, hub_type: HubType | None = None) -> list[RouteHub]:
        items = self._store.route_hubs.list_all()
        if hub_type:
            items = [h for h in items if h.hub_type == hub_type]
        return items

    def get_hub(self, hub_id: str) -> RouteHub:
        hub = self._store.route_hubs.get(hub_id)
        if hub is None:
            raise NotFoundError("RouteHub", hub_id)
        return hub

    def create_route(self, route: LogisticsRoute) -> LogisticsRoute:
        if not route.origin_hub_id or not route.destination_hub_id:
            raise ValidationError("origin_hub_id and destination_hub_id are required")
        self.get_hub(route.origin_hub_id)
        self.get_hub(route.destination_hub_id)
        self._recompute(route)
        return self._store.logistics_routes.save(route.route_id, route)

    def get_route(self, route_id: str) -> LogisticsRoute:
        route = self._store.logistics_routes.get(route_id)
        if route is None:
            raise NotFoundError("LogisticsRoute", route_id)
        return route

    def list_routes(self) -> list[LogisticsRoute]:
        return self._store.logistics_routes.list_all()

    def add_leg(self, route_id: str, leg: RouteLeg) -> LogisticsRoute:
        route = self.get_route(route_id)
        route.legs.append(leg)
        self._recompute(route)
        return self._store.logistics_routes.save(route_id, route)

    def build_leg(
        self,
        *,
        mode: TransportMode | str,
        from_hub_id: str,
        to_hub_id: str,
        distance_km: float = 0.0,
        duration_hours: float = 0.0,
        cost: float = 0.0,
        carrier_id: str = "",
    ) -> RouteLeg:
        mode_enum = TransportMode(mode) if isinstance(mode, str) else mode
        engine = _MODE_ENGINES.get(mode_enum)
        if engine is None:
            raise ValidationError(f"unsupported mode: {mode}")
        return engine.create_leg(
            from_hub_id=from_hub_id,
            to_hub_id=to_hub_id,
            distance_km=distance_km,
            duration_hours=duration_hours,
            cost=cost,
            carrier_id=carrier_id,
        )

    def _recompute(self, route: LogisticsRoute) -> None:
        route.total_distance_km = round(sum(leg.distance_km for leg in route.legs), 2)
        route.total_duration_hours = round(sum(leg.duration_hours for leg in route.legs), 2)
        route.total_cost = round(sum(leg.cost for leg in route.legs), 2)
        modes = {leg.mode for leg in route.legs}
        origin = self._store.route_hubs.get(route.origin_hub_id)
        dest = self._store.route_hubs.get(route.destination_hub_id)
        route.is_cross_border = bool(
            origin and dest and origin.country and dest.country and origin.country != dest.country
        )
        route.door_to_door = HubType.ORIGIN in (
            {origin.hub_type} if origin else set()
        ) or any(leg.mode == TransportMode.ROAD for leg in route.legs)
        if len(modes) > 1:
            route.name = route.name or "multimodal-route"

    async def optimize(self, route_id: str, *, optimize_for: str = "eta") -> LogisticsRoute:
        route = self.get_route(route_id)
        if not route.legs:
            raise ValidationError("route has no legs to optimize")
        if optimize_for == "cost":
            route.legs = sorted(route.legs, key=lambda leg: leg.cost)
            route.optimized_for = "cost"
        else:
            route.legs = sorted(route.legs, key=lambda leg: leg.duration_hours)
            route.optimized_for = "eta"
        self._recompute(route)
        saved = self._store.logistics_routes.save(route_id, route)
        await publish(
            RouteOptimizedEvent(
                route_id=route_id,
                optimized_for=saved.optimized_for,
                total_cost=saved.total_cost,
                total_duration_hours=saved.total_duration_hours,
            )
        )
        return saved


route_optimization_engine = RouteOptimizationEngine()
