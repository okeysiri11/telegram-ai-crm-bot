# Shipping — carriers, routes, freight orders.

from __future__ import annotations

from applications.agro_marketplace.export.ai_integration import ExportAIIntegration, export_ai
from applications.agro_marketplace.export.models import Carrier, FreightOrder, RoutePlan
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class ShippingService:
    def __init__(
        self,
        store: AgroStore | None = None,
        ai: ExportAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self._ai = ai or export_ai

    def create_carrier(self, carrier: Carrier) -> Carrier:
        if not carrier.name:
            raise ValidationError("name is required")
        return self._store.carriers.save(carrier.carrier_id, carrier)

    def list_carriers(self, *, mode: str | None = None) -> list[Carrier]:
        items = self._store.carriers.list_all()
        if mode:
            items = [c for c in items if c.mode == mode]
        return items

    def get_carrier(self, carrier_id: str) -> Carrier:
        carrier = self._store.carriers.get(carrier_id)
        if carrier is None:
            raise NotFoundError("Carrier", carrier_id)
        return carrier

    def create_route(self, route: RoutePlan) -> RoutePlan:
        return self._store.route_plans.save(route.route_id, route)

    def list_routes(self) -> list[RoutePlan]:
        return self._store.route_plans.list_all()

    def get_route(self, route_id: str) -> RoutePlan:
        route = self._store.route_plans.get(route_id)
        if route is None:
            raise NotFoundError("RoutePlan", route_id)
        return route

    async def plan_route(
        self,
        *,
        origin_port_id: str,
        destination_port_id: str,
        estimated_days: int = 18,
        distance_nm: float = 0.0,
    ) -> RoutePlan:
        route = RoutePlan(
            origin_port_id=origin_port_id,
            destination_port_id=destination_port_id,
            estimated_days=estimated_days,
            distance_nm=distance_nm or max(500.0, estimated_days * 400),
        )
        saved = self.create_route(route)
        await self._ai.optimize_route(origin_port_id, destination_port_id, [saved])
        return saved

    def book_freight(self, freight: FreightOrder) -> FreightOrder:
        if freight.cost < 0:
            raise ValidationError("cost must be non-negative")
        return self._store.freight_orders.save(freight.freight_id, freight)

    def list_freight_orders(self) -> list[FreightOrder]:
        return self._store.freight_orders.list_all()

    async def recommend_carriers(self, destination_country: str, *, mode: str = "sea"):
        return await self._ai.recommend_carrier(
            destination_country,
            self.list_carriers(mode=mode),
            mode=mode,
        )


shipping_service = ShippingService()
