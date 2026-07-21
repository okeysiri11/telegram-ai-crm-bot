# Truck GPS Engine + Fleet Tracking Engine + rail abstraction.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import TrackAssetType
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.tracking.events import TruckPositionUpdatedEvent
from applications.port_erp.tracking.live import LivePositionEngine, live_position_engine
from applications.port_erp.tracking.models import TruckTrack


class TruckGPSEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        live: LivePositionEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._live = live or live_position_engine

    def register_truck(self, truck: TruckTrack) -> TruckTrack:
        if not truck.plate_number:
            raise ValidationError("plate_number is required")
        return self._store.truck_tracks.save(truck.truck_id, truck)

    def get_truck(self, truck_id: str) -> TruckTrack:
        truck = self._store.truck_tracks.get(truck_id)
        if truck is None:
            raise NotFoundError("TruckTrack", truck_id)
        return truck

    def list_trucks(self) -> list[TruckTrack]:
        return self._store.truck_tracks.list_all()

    async def update_position(
        self,
        truck_id: str,
        *,
        latitude: float,
        longitude: float,
        speed_knots: float = 0.0,
        last_checkpoint: str = "",
        destination: str = "",
    ):
        self.get_truck(truck_id)
        live = await self._live.update(
            asset_type=TrackAssetType.TRUCK,
            asset_id=truck_id,
            latitude=latitude,
            longitude=longitude,
            speed_knots=speed_knots,
            destination=destination,
            last_checkpoint=last_checkpoint,
            source="truck_gps",
        )
        await publish(
            TruckPositionUpdatedEvent(
                truck_id=truck_id,
                latitude=latitude,
                longitude=longitude,
                speed_knots=speed_knots,
            )
        )
        return live


class FleetTrackingEngine:
    """Unified fleet view across vessels, trucks, and rail abstractions."""

    def __init__(
        self,
        store: PortStore | None = None,
        live: LivePositionEngine | None = None,
        trucks: TruckGPSEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._live = live or live_position_engine
        self._trucks = trucks or truck_gps_engine

    def snapshot(self) -> dict:
        return {
            "vessels": [p.to_dict() for p in self._live.list_live(asset_type=TrackAssetType.VESSEL)],
            "containers": [p.to_dict() for p in self._live.list_live(asset_type=TrackAssetType.CONTAINER)],
            "trucks": [p.to_dict() for p in self._live.list_live(asset_type=TrackAssetType.TRUCK)],
            "rail": [p.to_dict() for p in self._live.list_live(asset_type=TrackAssetType.RAIL)],
            "registered_trucks": [t.to_dict() for t in self._trucks.list_trucks()],
        }

    async def update_rail_position(
        self,
        rail_id: str,
        *,
        latitude: float,
        longitude: float,
        speed_knots: float = 0.0,
        destination: str = "",
        last_checkpoint: str = "",
    ):
        """Rail tracking abstraction — same live position pipeline."""
        return await self._live.update(
            asset_type=TrackAssetType.RAIL,
            asset_id=rail_id,
            latitude=latitude,
            longitude=longitude,
            speed_knots=speed_knots,
            destination=destination,
            last_checkpoint=last_checkpoint,
            source="rail",
        )


truck_gps_engine = TruckGPSEngine()
fleet_tracking_engine = FleetTrackingEngine(trucks=truck_gps_engine)
