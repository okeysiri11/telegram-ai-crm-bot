# Geofence Engine — port/terminal/berth/yard/gate/rail zones.

from __future__ import annotations

import math

from events.publisher import publish

from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import GeofenceType, TrackAssetType
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.tracking.events import EnteredGeofenceEvent, ExitedGeofenceEvent
from applications.port_erp.tracking.models import Geofence, Position, TimelineEvent
from applications.port_erp.timeline.engine import TimelineEngine, timeline_engine


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class GeofenceEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        timeline: TimelineEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._timeline = timeline or timeline_engine

    def create(self, fence: Geofence) -> Geofence:
        if not fence.name:
            raise ValidationError("name is required")
        if fence.radius_m <= 0:
            raise ValidationError("radius_m must be positive")
        return self._store.geofences.save(fence.geofence_id, fence)

    def get(self, geofence_id: str) -> Geofence:
        fence = self._store.geofences.get(geofence_id)
        if fence is None:
            raise NotFoundError("Geofence", geofence_id)
        return fence

    def list_geofences(self, *, fence_type: GeofenceType | None = None) -> list[Geofence]:
        items = self._store.geofences.list_all()
        if fence_type:
            items = [f for f in items if f.fence_type == fence_type]
        return items

    def contains(self, fence: Geofence, position: Position) -> bool:
        return _haversine_m(fence.center_lat, fence.center_lon, position.latitude, position.longitude) <= fence.radius_m

    async def evaluate(
        self,
        *,
        asset_type: TrackAssetType | str,
        asset_id: str,
        position: Position,
    ) -> list[dict]:
        asset_type_value = asset_type.value if isinstance(asset_type, TrackAssetType) else asset_type
        results = []
        for fence in self.list_geofences():
            if not fence.is_active:
                continue
            key = f"{fence.geofence_id}:{asset_type_value}:{asset_id}"
            inside = self.contains(fence, position)
            was_inside = bool(self._store.geofence_occupancy.get(key))
            if inside and not was_inside:
                self._store.geofence_occupancy.save(key, True)
                await publish(
                    EnteredGeofenceEvent(
                        geofence_id=fence.geofence_id,
                        asset_type=asset_type_value,
                        asset_id=asset_id,
                        fence_type=fence.fence_type.value,
                    )
                )
                self._timeline.record(
                    TimelineEvent(
                        asset_type=asset_type_value,
                        asset_id=asset_id,
                        event_type="entered_geofence",
                        title=f"Entered {fence.name}",
                        location=fence.name,
                        metadata={"geofence_id": fence.geofence_id},
                    )
                )
                results.append({"geofence_id": fence.geofence_id, "action": "entered"})
            elif not inside and was_inside:
                self._store.geofence_occupancy.delete(key)
                await publish(
                    ExitedGeofenceEvent(
                        geofence_id=fence.geofence_id,
                        asset_type=asset_type_value,
                        asset_id=asset_id,
                        fence_type=fence.fence_type.value,
                    )
                )
                results.append({"geofence_id": fence.geofence_id, "action": "exited"})
        return results


geofence_engine = GeofenceEngine()
