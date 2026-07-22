"""VIN Intelligence Suite facade — Sprint 13.1."""

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.config import DEFAULT_CONFIG
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.vin_intelligence.analysis import AIAnalysis
from applications.auto_marketplace.vin_intelligence.decoder import VINDecoder
from applications.auto_marketplace.vin_intelligence.history import VehicleHistory
from applications.auto_marketplace.vin_intelligence.passport import DigitalPassport
from applications.auto_marketplace.vin_intelligence.recommendations import AIRecommendations
from applications.auto_marketplace.vin_intelligence.services import (
    KnowledgeGraph,
    VINDashboard,
    VINIntegrations,
)


class VINIntelligenceSuite:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.decoder = VINDecoder(self.store)
        self.passport = DigitalPassport(self.store)
        self.analysis = AIAnalysis(self.store)
        self.history = VehicleHistory(self.store)
        self.recommendations = AIRecommendations(self.store)
        self.graph = KnowledgeGraph(self.store)
        self.integrations = VINIntegrations(self.store)
        self.dashboard = VINDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        vin = "WVWZZZ1JZXW000001"
        decoded = self.decoder.decode(vin)
        passport = self.passport.create(vin=vin, decode_id=decoded["decode_id"], title="Golf Digital Passport")
        self.passport.add_timeline_event(
            passport_id=passport["passport_id"],
            timeline="ownership",
            event={"owner": "Alex Buyer", "type": "purchase"},
        )
        self.passport.add_timeline_event(
            passport_id=passport["passport_id"],
            timeline="mileage",
            event={"odometer": 45000, "unit": "km"},
        )
        self.passport.add_timeline_event(
            passport_id=passport["passport_id"],
            timeline="maintenance",
            event={"service": "oil_change", "shop": "Prime Motors"},
        )
        self.history.add(vin=vin, history_type="import", detail={"origin": "DE"}, source="customs")
        self.history.add(vin=vin, history_type="registration", detail={"country": "DE"}, source="gov")
        self.history.add(vin=vin, history_type="service", detail={"job": "inspection"}, source="dealer")
        fraud = self.analysis.detect_fraud(vin=vin, listing_price=18500, claimed_mileage=45000)
        value = self.analysis.market_value(vin=vin, mileage=45000, base_price=20000)
        scores = self.recommendations.score(
            vin=vin,
            fraud_score=float(fraud.get("fraud_score") or 0),
            accident_prob=0.15,
            market_value=float(value.get("estimate") or 0),
            mileage=45000,
        )
        self.graph.upsert_node(graph="vehicle", node_id=vin, label="VW Golf", props={"year": 2020})
        self.graph.upsert_node(graph="dealer", node_id="prime", label="Prime Motors")
        self.graph.link(graph="vehicle", source=vin, target="prime", relation="listed_by")
        self.integrations.connect(channel="vin_providers", endpoint="https://vin.example/api")
        self.integrations.connect(channel="government_registries", endpoint="https://gov.example/vin")
        board = self.dashboard.render(dashboard_type="passport")
        return {
            "bootstrap": True,
            "vin": vin,
            "decode_id": decoded["decode_id"],
            "passport_id": passport["passport_id"],
            "fraud_analysis_id": fraud["analysis_id"],
            "recommendation_id": scores["recommendation_id"],
            "dashboard_id": board["dashboard_id"],
            "enterprise_foundation": DEFAULT_CONFIG.enterprise_foundation,
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "decoder": self.decoder.status(),
            "passport": self.passport.status(),
            "analysis": self.analysis.status(),
            "history": self.history.status(),
            "recommendations": self.recommendations.status(),
            "graph": self.graph.status(),
            "integrations": self.integrations.status(),
            "dashboard": self.dashboard.status(),
        }


vin_intelligence = VINIntelligenceSuite()
