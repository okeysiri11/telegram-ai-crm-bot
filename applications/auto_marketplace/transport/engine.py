# Transport Engine — pickup, delivery, transfers + AI logistics assistants.

from __future__ import annotations

import time

from applications.auto_marketplace.carriers.engine import CarrierNetworkEngine, carrier_network_engine
from applications.auto_marketplace.customs.engine import CustomsEngine, customs_engine
from applications.auto_marketplace.delivery.logistics_engine import LogisticsDeliveryEngine, logistics_delivery_engine
from applications.auto_marketplace.dispatch.engine import DispatchEngine, dispatch_engine
from applications.auto_marketplace.documents.logistics_engine import LogisticsDocumentEngine, logistics_document_engine
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.tracking.engine import TrackingEngine, tracking_engine
from applications.auto_marketplace.transport.models import (
    ShipmentKind,
    ShipmentStatus,
    TransportMode,
    VehicleShipment,
)
from applications.auto_marketplace.route_optimizer.engine import RouteOptimizerEngine, route_optimizer_engine


class TransportEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        carriers: CarrierNetworkEngine | None = None,
        dispatch: DispatchEngine | None = None,
        tracking: TrackingEngine | None = None,
        routes: RouteOptimizerEngine | None = None,
        customs: CustomsEngine | None = None,
        documents: LogisticsDocumentEngine | None = None,
        delivery: LogisticsDeliveryEngine | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self.carriers = carriers or carrier_network_engine
        self.dispatch = dispatch or dispatch_engine
        self.tracking = tracking or tracking_engine
        self.routes = routes or route_optimizer_engine
        self.customs = customs or customs_engine
        self.documents = documents or logistics_document_engine
        self.delivery = delivery or logistics_delivery_engine

    def create(self, shipment: VehicleShipment) -> VehicleShipment:
        if not shipment.vehicle_id and not shipment.vin:
            raise ValidationError("vehicle_id or vin is required")
        if not shipment.origin or not shipment.destination:
            raise ValidationError("origin and destination are required")
        shipment.status = ShipmentStatus.DRAFT
        shipment.timeline.append({"event": "created", "at": time.time()})
        shipment.updated_at = time.time()
        return self._store.vehicle_shipments.save(shipment.shipment_id, shipment)

    def get(self, shipment_id: str) -> VehicleShipment:
        item = self._store.vehicle_shipments.get(shipment_id)
        if item is None:
            raise NotFoundError("VehicleShipment", shipment_id)
        return item

    def book(self, shipment_id: str) -> VehicleShipment:
        shipment = self.get(shipment_id)
        international = bool(shipment.origin_country and shipment.destination_country and shipment.origin_country != shipment.destination_country)
        route = self.routes.optimize(
            shipment_id=shipment_id,
            origin=shipment.origin,
            destination=shipment.destination,
            stops=shipment.stops,
            border_crossings=[f"{shipment.origin_country}->{shipment.destination_country}"] if international else [],
        )
        shipment.route_id = route.route_id
        shipment.cost = route.total_cost
        shipment.eta = time.time() + route.duration_hours * 3600
        if not shipment.pickup_at:
            shipment.pickup_at = time.time() + 3600
        docs = self.documents.packet(shipment_id, international=international)
        shipment.document_ids = [d.document_id for d in docs]
        track = self.tracking.start(shipment_id=shipment_id, eta=shipment.eta)
        shipment.tracking_id = track.tracking_id
        shipment.status = ShipmentStatus.BOOKED
        shipment.timeline.append({"event": "booked", "route_id": route.route_id, "at": time.time()})
        shipment.updated_at = time.time()
        return self._store.vehicle_shipments.save(shipment_id, shipment)

    def start_transit(self, shipment_id: str) -> VehicleShipment:
        shipment = self.get(shipment_id)
        shipment.status = ShipmentStatus.IN_TRANSIT
        shipment.timeline.append({"event": "in_transit", "at": time.time()})
        shipment.updated_at = time.time()
        if shipment.tracking_id:
            self.tracking.notify(shipment.tracking_id, "Shipment in transit")
        return self._store.vehicle_shipments.save(shipment_id, shipment)

    def list_shipments(self, *, status: str = "", kind: str = "") -> list[VehicleShipment]:
        items = self._store.vehicle_shipments.list_all()
        if status:
            items = [s for s in items if s.status.value == status]
        if kind:
            items = [s for s in items if s.kind.value == kind]
        return items

    # --- AI assistants ---
    def ai_carrier_recommendation(self, *, mode: str = "truck", country: str = "") -> list[dict]:
        return [c.to_dict() for c in self.carriers.recommend(mode=mode, country=country)[:5]]

    def ai_delivery_prediction(self, shipment_id: str) -> dict:
        shipment = self.get(shipment_id)
        eta_info = self.tracking.predict_eta(shipment.tracking_id) if shipment.tracking_id else {"eta": shipment.eta, "delay_risk": 0.2}
        return {
            "shipment_id": shipment_id,
            "predicted_delivery": eta_info.get("eta", shipment.eta),
            "delay_risk": eta_info.get("delay_risk", 0.2),
            "status": shipment.status.value,
            "ai_summary": "Delivery window based on route progress and historical delay risk",
        }

    def ai_delay_forecast(self, shipment_id: str) -> dict:
        pred = self.ai_delivery_prediction(shipment_id)
        risk = float(pred["delay_risk"])
        return {
            "shipment_id": shipment_id,
            "delay_probability": risk,
            "expected_delay_hours": round(risk * 6, 1),
            "risk_level": "high" if risk > 0.5 else "medium" if risk > 0.25 else "low",
        }

    def ai_risk_prediction(self, shipment_id: str) -> dict:
        shipment = self.get(shipment_id)
        factors = []
        score = 0.15
        if shipment.origin_country and shipment.destination_country and shipment.origin_country != shipment.destination_country:
            score += 0.25
            factors.append("cross_border")
        if shipment.mode in {TransportMode.SEA, TransportMode.AIR}:
            score += 0.1
            factors.append(shipment.mode.value)
        if shipment.status == ShipmentStatus.DELAYED:
            score += 0.4
            factors.append("already_delayed")
        return {"shipment_id": shipment_id, "risk_score": round(min(0.95, score), 2), "factors": factors}

    def metrics(self) -> dict:
        items = self._store.vehicle_shipments.list_all()
        return {
            "shipments": len(items),
            "in_transit": len([s for s in items if s.status == ShipmentStatus.IN_TRANSIT]),
            "kinds": [k.value for k in ShipmentKind],
            "modes": [m.value for m in TransportMode],
        }


transport_engine = TransportEngine()
