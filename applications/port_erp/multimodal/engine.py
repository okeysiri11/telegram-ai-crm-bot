# Multimodal Logistics Engine — door-to-door, transfers, consolidation orchestration.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.booking.engine import BookingEngine, booking_engine
from applications.port_erp.forwarders.engine import FreightForwarderEngine, freight_forwarder_engine
from applications.port_erp.multimodal.events import ShipmentTransferredEvent
from applications.port_erp.multimodal.models import (
    ConsolidationBatch,
    LogisticsRoute,
    TransportMode,
    TransportOrder,
)
from applications.port_erp.routes.engine import RouteOptimizationEngine, route_optimization_engine
from applications.port_erp.shared.exceptions import ValidationError
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.transport_orders.engine import TransportOrderEngine, transport_order_engine


class MultimodalLogisticsEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        routes: RouteOptimizationEngine | None = None,
        bookings: BookingEngine | None = None,
        orders: TransportOrderEngine | None = None,
        forwarders: FreightForwarderEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._routes = routes or route_optimization_engine
        self._bookings = bookings or booking_engine
        self._orders = orders or transport_order_engine
        self._forwarders = forwarders or freight_forwarder_engine

    def plan_door_to_door(
        self,
        *,
        name: str,
        origin_hub_id: str,
        destination_hub_id: str,
        legs: list | None = None,
    ) -> LogisticsRoute:
        route = LogisticsRoute(
            name=name or "door-to-door",
            origin_hub_id=origin_hub_id,
            destination_hub_id=destination_hub_id,
            legs=list(legs or []),
            door_to_door=True,
        )
        return self._routes.create_route(route)

    async def transfer_mode(
        self,
        order_id: str,
        *,
        to_mode: TransportMode | str,
        hub_id: str = "",
    ) -> TransportOrder:
        order = self._orders.get(order_id)
        from_mode = order.mode.value
        mode = TransportMode(to_mode) if isinstance(to_mode, str) else to_mode
        order.mode = mode
        saved = self._store.transport_orders.save(order_id, order)
        await publish(
            ShipmentTransferredEvent(
                order_id=order_id,
                from_mode=from_mode,
                to_mode=mode.value,
                hub_id=hub_id,
            )
        )
        return saved

    def consolidate_freight(
        self,
        *,
        forwarder_id: str,
        route_id: str = "",
        booking_ids: list[str] | None = None,
        container_ids: list[str] | None = None,
    ) -> ConsolidationBatch:
        return self._forwarders.consolidate(
            forwarder_id=forwarder_id,
            route_id=route_id,
            booking_ids=booking_ids,
            container_ids=container_ids,
        )

    def route_container(
        self,
        *,
        container_id: str,
        route_id: str,
        booking_id: str = "",
        carrier_id: str = "",
    ) -> TransportOrder:
        if not container_id:
            raise ValidationError("container_id is required")
        route = self._routes.get_route(route_id)
        order = TransportOrder(
            booking_id=booking_id,
            carrier_id=carrier_id,
            route_id=route_id,
            container_id=container_id,
            mode=TransportMode.MULTIMODAL if len({leg.mode for leg in route.legs}) > 1 else (
                route.legs[0].mode if route.legs else TransportMode.SEA
            ),
            origin=route.origin_hub_id,
            destination=route.destination_hub_id,
        )
        return self._orders.create(order)


multimodal_logistics_engine = MultimodalLogisticsEngine()
