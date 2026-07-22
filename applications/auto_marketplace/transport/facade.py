# Logistics domain facade — Sprint 10.6.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.carriers.engine import CarrierNetworkEngine, carrier_network_engine
from applications.auto_marketplace.customs.engine import CustomsEngine, customs_engine
from applications.auto_marketplace.dispatch.engine import DispatchEngine, dispatch_engine
from applications.auto_marketplace.documents.logistics_engine import LogisticsDocumentEngine, logistics_document_engine
from applications.auto_marketplace.fleet_transport.engine import FleetTransportEngine, fleet_transport_engine
from applications.auto_marketplace.import_export.engine import ImportExportEngine, import_export_engine
from applications.auto_marketplace.international.engine import InternationalEngine, international_engine
from applications.auto_marketplace.route_optimizer.engine import RouteOptimizerEngine, route_optimizer_engine
from applications.auto_marketplace.tracking.engine import TrackingEngine, tracking_engine
from applications.auto_marketplace.transport.engine import TransportEngine, transport_engine
from applications.auto_marketplace.vehicle_shipping.engine import VehicleShippingEngine, vehicle_shipping_engine
from applications.auto_marketplace.delivery.logistics_engine import LogisticsDeliveryEngine, logistics_delivery_engine


class LogisticsDomainEngine:
    """Sprint 10.6 — transport, tracking, customs, import/export, fleet logistics."""

    def __init__(
        self,
        transport: TransportEngine | None = None,
        carriers: CarrierNetworkEngine | None = None,
        tracking: TrackingEngine | None = None,
        routes: RouteOptimizerEngine | None = None,
        customs: CustomsEngine | None = None,
        import_export: ImportExportEngine | None = None,
        international: InternationalEngine | None = None,
        fleet: FleetTransportEngine | None = None,
        documents: LogisticsDocumentEngine | None = None,
        shipping: VehicleShippingEngine | None = None,
        dispatch: DispatchEngine | None = None,
        delivery: LogisticsDeliveryEngine | None = None,
    ) -> None:
        self.transport = transport or transport_engine
        self.carriers = carriers or carrier_network_engine
        self.tracking = tracking or tracking_engine
        self.routes = routes or route_optimizer_engine
        self.customs = customs or customs_engine
        self.import_export = import_export or import_export_engine
        self.international = international or international_engine
        self.fleet = fleet or fleet_transport_engine
        self.documents = documents or logistics_document_engine
        self.shipping = shipping or vehicle_shipping_engine
        self.dispatch = dispatch or dispatch_engine
        self.delivery = delivery or logistics_delivery_engine

    def metrics(self) -> dict[str, Any]:
        return {
            "transport": self.transport.metrics(),
            "carriers": self.carriers.metrics(),
            "tracking": self.tracking.metrics(),
            "routes": self.routes.metrics(),
            "customs": self.customs.metrics(),
            "import_export": self.import_export.metrics(),
            "international": self.international.metrics(),
            "fleet": self.fleet.metrics(),
            "documents": self.documents.metrics(),
            "shipping": self.shipping.metrics(),
            "dispatch": self.dispatch.metrics(),
            "delivery": self.delivery.metrics(),
        }


logistics_domain_engine = LogisticsDomainEngine()
