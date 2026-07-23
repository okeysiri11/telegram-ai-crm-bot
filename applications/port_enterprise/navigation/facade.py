"""Navigation Suite facade — Sprint 15.1."""

from __future__ import annotations

from typing import Any

from applications.port_enterprise.config import DEFAULT_CONFIG
from applications.port_enterprise.navigation.radar_nav import (
    AINavigationIntelligence,
    MaritimeSafety,
    NavigationManagement,
    RadarIntelligence,
)
from applications.port_enterprise.navigation.services import NavigationDashboard, NavigationKnowledge
from applications.port_enterprise.navigation.vts_ais import AISIntegration, VesselTrafficService
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store


class NavigationSuite:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.vts = VesselTrafficService(self.store)
        self.ais = AISIntegration(self.store)
        self.radar = RadarIntelligence(self.store)
        self.navigation = NavigationManagement(self.store)
        self.safety = MaritimeSafety(self.store)
        self.ai = AINavigationIntelligence(self.store)
        self.dashboard = NavigationDashboard(self.store)
        self.knowledge = NavigationKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        center = self.vts.open_center(name="Odessa VTS", port_id="UAODS")
        self.vts.monitor_traffic(center_id=center["center_id"], vessel_count=28, density=0.55)
        self.vts.arrival_queue(center_id=center["center_id"], vessel_id="vsl_1", eta="2026-08-11T08:00:00Z")
        self.vts.departure_queue(center_id=center["center_id"], vessel_id="vsl_2", etd="2026-08-11T14:00:00Z")
        self.vts.navigation_assist(
            center_id=center["center_id"], vessel_id="vsl_1", advice="Reduce speed to 8 kn in fairway"
        )
        collision = self.vts.collision_watch(
            center_id=center["center_id"], vessel_a="vsl_1", vessel_b="vsl_3", cpa_nm=0.35
        )
        self.vts.restricted_area(center_id=center["center_id"], area="Dredging Zone", vessel_id="vsl_4", breached=False)

        receiver = self.ais.register_receiver(name="AIS Station North", station="UAODS-N")
        msg = self.ais.process_message(
            receiver_id=receiver["receiver_id"],
            mmsi="272123456",
            lat=46.49,
            lon=30.74,
            sog=9.5,
            cog=185.0,
        )
        self.ais.process_message(
            receiver_id=receiver["receiver_id"],
            mmsi="272123456",
            lat=46.485,
            lon=30.735,
            sog=9.2,
            cog=182.0,
        )
        eta = self.ais.eta_predict(mmsi="272123456", remaining_nm=12.0, sog=9.2)

        radar = self.radar.register_radar(name="Harbor Radar 1", coverage_nm=24)
        target = self.radar.detect_target(
            radar_id=radar["radar_id"], bearing=120.0, range_nm=4.2, object_class="vessel"
        )
        self.radar.blind_zone(radar_id=radar["radar_id"], sector="SW pier shadow", severity="low")
        self.radar.alert(radar_id=radar["radar_id"], message="Unidentified target near fairway", level="warning")

        route = self.navigation.create_route(
            name="Approach Alpha",
            waypoints=[{"lat": 46.45, "lon": 30.80}, {"lat": 46.48, "lon": 30.75}],
        )
        self.navigation.fairway(name="Main Fairway", depth_m=15.5)
        self.navigation.pilot_boarding(name="PBZ Outer", lat=46.42, lon=30.85)
        self.navigation.anchorage(name="Outer Anchorage", capacity=18)
        self.navigation.restriction(title="No entry", area="Military zone", reason="security")
        self.navigation.weather_overlay(area="Approaches", wind_kn=18, visibility_nm=4.0)
        self.navigation.sea_state(area="Approaches", douglas_scale=4)

        risk = self.safety.collision_risk(vessel_a="vsl_1", vessel_b="vsl_3", score=0.58)
        self.safety.warning(title="Fog bank", message="Visibility reduced in approaches", kind="navigation")
        emergency = self.safety.emergency(vessel_id="vsl_5", nature="engine_failure")
        self.safety.restricted_zone_alert(zone="Dredging Zone", vessel_id="vsl_4")
        self.safety.environmental_hazard(hazard="oil_sheen", severity="high")

        traffic = self.ai.predict_traffic(area="Approaches", horizon_hours=6)
        opt_route = self.ai.optimal_route(origin="PBZ Outer", destination="Berth A1")
        arrival = self.ai.arrival_optimization(vessel_id="vsl_1", requested_eta="2026-08-11T08:00:00Z")
        berth = self.ai.berth_recommendation(vessel_id="vsl_1", candidates=["Berth A1", "Berth A2"])
        self.ai.operational_risk(vessel_id="vsl_1", score=0.42)

        for rtype, key in (
            ("navigation", route["route_id"]),
            ("ais", receiver["receiver_id"]),
            ("radar", radar["radar_id"]),
            ("traffic", center["center_id"]),
            ("safety", risk["risk_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="vts")
        return {
            "bootstrap": True,
            "center_id": center["center_id"],
            "collision_watch_id": collision["watch_id"],
            "receiver_id": receiver["receiver_id"],
            "message_id": msg["message_id"],
            "eta_id": eta["eta_id"],
            "radar_id": radar["radar_id"],
            "target_id": target["target_id"],
            "route_id": route["route_id"],
            "risk_id": risk["risk_id"],
            "emergency_id": emergency["emergency_id"],
            "traffic_prediction_id": traffic["prediction_id"],
            "optimal_route_id": opt_route["route_id"],
            "arrival_optimization_id": arrival["optimization_id"],
            "berth_recommendation_id": berth["recommendation_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "vts": self.vts.status(),
            "ais": self.ais.status(),
            "radar": self.radar.status(),
            "navigation": self.navigation.status(),
            "safety": self.safety.status(),
            "ai": self.ai.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


navigation = NavigationSuite()
