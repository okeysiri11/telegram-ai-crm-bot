"""Freight Marketplace facade — Sprint 15.6."""

from __future__ import annotations

from typing import Any

from applications.port_enterprise.config import DEFAULT_CONFIG
from applications.port_enterprise.freight_marketplace.marketplace import (
    CarrierManagement,
    FreightExchange,
    FreightMarketplace,
)
from applications.port_enterprise.freight_marketplace.services import (
    AILogisticsMarketplace,
    GlobalLogisticsNetwork,
    MarketplaceDashboard,
    MarketplaceKnowledge,
    ShipmentCollaboration,
)
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store


class FreightMarketplaceSuite:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.marketplace = FreightMarketplace(self.store)
        self.carriers = CarrierManagement(self.store)
        self.exchange = FreightExchange(self.store)
        self.network = GlobalLogisticsNetwork(self.store)
        self.collaboration = ShipmentCollaboration(self.store)
        self.ai = AILogisticsMarketplace(self.store)
        self.dashboard = MarketplaceDashboard(self.store)
        self.knowledge = MarketplaceKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        listing = self.marketplace.list_cargo(
            title="40HC Odessa to Istanbul",
            origin="Odessa",
            destination="Istanbul",
            teu=1.0,
            price=850,
        )
        self.marketplace.available_freight(corridor="Odessa-Istanbul", capacity_teu=200)
        req = self.marketplace.transport_request(
            shipper="Black Sea Shipper",
            origin="Odessa",
            destination="Istanbul",
            teu=2.0,
        )

        sea = self.carriers.register(name="Black Sea Line", carrier_type="shipping", country="UA", scac="BSL1")
        self.carriers.register(name="Rail UA", carrier_type="rail", country="UA")
        self.carriers.register(name="Truck Fleet Co", carrier_type="truck", country="UA")
        self.carriers.register(name="Sky Cargo", carrier_type="air", country="TR")
        self.carriers.register(name="Forward Pro", carrier_type="forwarder", country="UA")
        self.carriers.register(name="Customs Clear LLC", carrier_type="customs_broker", country="UA")
        self.carriers.rate(sea["carrier_id"], score=4.6, comment="Reliable")

        match = self.marketplace.instant_match(
            request_id=req["request_id"], carrier_id=sea["carrier_id"], score=0.93
        )
        self.marketplace.search(query="Odessa", mode="sea")
        analytics = self.marketplace.analytics(period="monthly")

        spot = self.exchange.spot(corridor="Odessa-Istanbul", teu=5.0, ask_price=900)
        self.exchange.contract(
            shipper="Black Sea Shipper",
            carrier_id=sea["carrier_id"],
            corridor="Odessa-Istanbul",
            rate=800,
        )
        tender = self.exchange.tender(title="Q3 Sea Tender", corridor="Odessa-Istanbul", teu=100)
        self.exchange.bid(tender_id=tender["tender_id"], carrier_id=sea["carrier_id"], price=780)
        self.exchange.auction(spot_id=spot["spot_id"], start_price=850)
        self.exchange.negotiate(subject_ref=spot["spot_id"], offer=860, counter=840)
        booking = self.exchange.book(
            shipper="Black Sea Shipper",
            carrier_id=sea["carrier_id"],
            origin="Odessa",
            destination="Istanbul",
            price=820,
        )

        partner = self.network.register_partner(name="Global Logistics Hub", country="TR", role="3pl")
        self.network.register_port_node(name="Port of Odessa", unlocode="UAODS")
        self.network.register_warehouse_node(name="CFS Network Node", region="South")
        self.network.register_distribution_node(name="Central DC Node", region="Central")
        corridor = self.network.register_corridor(name="Black Sea Corridor", modes=["sea", "rail", "truck"])
        route = self.network.register_route(origin="Odessa", destination="Istanbul", mode="sea")
        self.network.partner_performance(partner_id=partner["partner_id"], otif_pct=96.5, score=4.7)

        ws = self.collaboration.workspace(shipment_ref=booking["booking_id"], title="Booking Workspace")
        self.collaboration.customer_portal(customer="Black Sea Shipper", workspace_id=ws["workspace_id"])
        self.collaboration.carrier_portal(carrier_id=sea["carrier_id"], workspace_id=ws["workspace_id"])
        self.collaboration.share_document(workspace_id=ws["workspace_id"], title="BL Draft", doc_type="bl")
        self.collaboration.notify(workspace_id=ws["workspace_id"], message="Carrier confirmed")
        self.collaboration.collaborate(
            workspace_id=ws["workspace_id"], actor="shipper", note="Ready to load"
        )

        rec = self.ai.recommend_carrier(origin="Odessa", destination="Istanbul", mode="sea")
        self.ai.match_freight(request_id=req["request_id"], carrier_id=sea["carrier_id"])
        self.ai.dynamic_pricing(corridor="Odessa-Istanbul", baseline=800)
        self.ai.capacity_predict(corridor="Odessa-Istanbul", teu=500)
        demand = self.ai.demand_forecast(corridor="Odessa-Istanbul", days=30, baseline=1200)
        self.ai.optimize_route(origin="Odessa", destination="Istanbul", mode="multimodal")
        self.ai.optimize_cost(booking_ref=booking["booking_id"], baseline_cost=820)
        fraud = self.ai.fraud_detect(subject_ref=booking["booking_id"], anomaly_score=0.12)

        for rtype, key in (
            ("marketplace", listing["listing_id"]),
            ("carrier", sea["carrier_id"]),
            ("freight", booking["booking_id"]),
            ("partner", partner["partner_id"]),
            ("global", corridor["corridor_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="marketplace")
        return {
            "bootstrap": True,
            "listing_id": listing["listing_id"],
            "request_id": req["request_id"],
            "match_id": match["match_id"],
            "carrier_id": sea["carrier_id"],
            "spot_id": spot["spot_id"],
            "tender_id": tender["tender_id"],
            "booking_id": booking["booking_id"],
            "partner_id": partner["partner_id"],
            "corridor_id": corridor["corridor_id"],
            "route_id": route["route_id"],
            "workspace_id": ws["workspace_id"],
            "analytics_id": analytics["analytics_id"],
            "recommendation_id": rec["recommendation_id"],
            "demand_id": demand["forecast_id"],
            "fraud_id": fraud["detection_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "marketplace": self.marketplace.status(),
            "carriers": self.carriers.status(),
            "exchange": self.exchange.status(),
            "network": self.network.status(),
            "collaboration": self.collaboration.status(),
            "ai": self.ai.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


freight_marketplace = FreightMarketplaceSuite()
