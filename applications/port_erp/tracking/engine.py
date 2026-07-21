# Live Tracking Engine — facade for AIS, container, GPS, fleet, geofence, ETA, timeline.

from __future__ import annotations

from typing import Any

from applications.port_erp.ais.engine import AISTrackingEngine, ais_tracking_engine
from applications.port_erp.containers.tracking import ContainerTrackingEngine, container_tracking_engine
from applications.port_erp.fleet.engine import FleetTrackingEngine, fleet_tracking_engine
from applications.port_erp.geofence.engine import GeofenceEngine, geofence_engine
from applications.port_erp.gps.engine import TruckGPSEngine, truck_gps_engine
from applications.port_erp.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.port_erp.maps.service import MapsService, maps_service
from applications.port_erp.timeline.engine import TimelineEngine, timeline_engine
from applications.port_erp.tracking.live import (
    ETAEngine,
    LivePositionEngine,
    RouteMonitoringEngine,
    eta_engine,
    live_position_engine,
    route_monitoring_engine,
)


class LiveTrackingEngine:
    def __init__(
        self,
        ais: AISTrackingEngine | None = None,
        containers: ContainerTrackingEngine | None = None,
        trucks: TruckGPSEngine | None = None,
        fleet: FleetTrackingEngine | None = None,
        geofences: GeofenceEngine | None = None,
        live: LivePositionEngine | None = None,
        routes: RouteMonitoringEngine | None = None,
        eta: ETAEngine | None = None,
        timeline: TimelineEngine | None = None,
        maps: MapsService | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self.ais = ais or ais_tracking_engine
        self.containers = containers or container_tracking_engine
        self.trucks = trucks or truck_gps_engine
        self.fleet = fleet or fleet_tracking_engine
        self.geofences = geofences or geofence_engine
        self.live = live or live_position_engine
        self.routes = routes or route_monitoring_engine
        self.eta = eta or eta_engine
        self.timeline = timeline or timeline_engine
        self.maps = maps or maps_service
        self._platform = platform or platform_bridge

    def metrics(self) -> dict[str, Any]:
        return {
            "live_positions": len(self.live.list_live()),
            "vessels": len(self.ais.list_positions()),
            "trucks": len(self.trucks.list_trucks()),
            "geofences": len(self.geofences.list_geofences()),
            "timeline_events": len(self.timeline.recent(limit=10000)),
            "container_statuses": self.containers.statuses(),
        }

    async def remember_snapshot(self) -> None:
        await self._platform.remember_context("tracking:snapshot", self.metrics())


live_tracking_engine = LiveTrackingEngine()
