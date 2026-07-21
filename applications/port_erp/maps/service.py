# Maps service — map layers for live tracking visualization.

from __future__ import annotations

from applications.port_erp.geofence.engine import GeofenceEngine, geofence_engine
from applications.port_erp.tracking.live import LivePositionEngine, live_position_engine


class MapsService:
    def __init__(
        self,
        live: LivePositionEngine | None = None,
        geofences: GeofenceEngine | None = None,
    ) -> None:
        self._live = live or live_position_engine
        self._geofences = geofences or geofence_engine

    def viewport(self, *, center_lat: float = 0.0, center_lon: float = 0.0, zoom: int = 10) -> dict:
        return {
            "center": {"latitude": center_lat, "longitude": center_lon},
            "zoom": zoom,
            "assets": [p.to_dict() for p in self._live.list_live()],
            "geofences": [g.to_dict() for g in self._geofences.list_geofences()],
            "layers": ["vessels", "containers", "trucks", "rail", "geofences"],
        }


maps_service = MapsService()
