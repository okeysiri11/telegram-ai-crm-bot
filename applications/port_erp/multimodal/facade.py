# Logistics domain facade — shipping, forwarders, carriers, booking, multimodal.

from __future__ import annotations

from typing import Any

from applications.port_erp.booking.engine import BookingEngine, booking_engine
from applications.port_erp.carriers.engine import CarrierManagementEngine, carrier_management_engine
from applications.port_erp.fleet.coordination import FleetCoordinationEngine, fleet_coordination_engine
from applications.port_erp.forwarders.engine import FreightForwarderEngine, freight_forwarder_engine
from applications.port_erp.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.port_erp.multimodal.engine import MultimodalLogisticsEngine, multimodal_logistics_engine
from applications.port_erp.routes.engine import RouteOptimizationEngine, route_optimization_engine
from applications.port_erp.shipping_lines.engine import ShippingLineEngine, shipping_line_engine
from applications.port_erp.transport_orders.engine import TransportOrderEngine, transport_order_engine


class LogisticsDomainEngine:
    """Sprint 9.5 facade over shipping / forwarders / multimodal logistics."""

    def __init__(
        self,
        shipping: ShippingLineEngine | None = None,
        forwarders: FreightForwarderEngine | None = None,
        carriers: CarrierManagementEngine | None = None,
        routes: RouteOptimizationEngine | None = None,
        bookings: BookingEngine | None = None,
        transport: TransportOrderEngine | None = None,
        multimodal: MultimodalLogisticsEngine | None = None,
        fleet: FleetCoordinationEngine | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self.shipping = shipping or shipping_line_engine
        self.forwarders = forwarders or freight_forwarder_engine
        self.carriers = carriers or carrier_management_engine
        self.routes = routes or route_optimization_engine
        self.bookings = bookings or booking_engine
        self.transport = transport or transport_order_engine
        self.multimodal = multimodal or multimodal_logistics_engine
        self.fleet = fleet or fleet_coordination_engine
        self._platform = platform or platform_bridge

    def metrics(self) -> dict[str, Any]:
        return {
            "shipping_lines": len(self.shipping.list_lines()),
            "schedules": len(self.shipping.list_schedules()),
            "forwarders": len(self.forwarders.list_forwarders()),
            "carriers": len(self.carriers.list_carriers()),
            "contracts": len(self.carriers.list_contracts()),
            "hubs": len(self.routes.list_hubs()),
            "routes": len(self.routes.list_routes()),
            "bookings": len(self.bookings.list_bookings()),
            "transport_orders": len(self.transport.list_orders()),
            "fleet_assignments": len(self.fleet.list_assignments()),
            "consolidations": len(self.forwarders.list_consolidations()),
        }

    async def remember_snapshot(self) -> None:
        await self._platform.remember_context("logistics:snapshot", self.metrics())


logistics_domain_engine = LogisticsDomainEngine()
