# AIS Tracking Engine — vessel positions via AIS-style updates.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.shared.models import TrackAssetType
from applications.port_erp.tracking.events import VesselPositionUpdatedEvent
from applications.port_erp.tracking.live import LivePositionEngine, live_position_engine
from applications.port_erp.vessels.service import VesselRegistry, vessel_registry


class AISTrackingEngine:
    def __init__(
        self,
        live: LivePositionEngine | None = None,
        vessels: VesselRegistry | None = None,
    ) -> None:
        self._live = live or live_position_engine
        self._vessels = vessels or vessel_registry

    async def update_vessel_position(
        self,
        vessel_id: str,
        *,
        latitude: float,
        longitude: float,
        speed_knots: float = 0.0,
        heading_deg: float = 0.0,
        destination: str = "",
        last_checkpoint: str = "",
        eta: float | None = None,
        etd: float | None = None,
    ):
        self._vessels.get(vessel_id)
        live = await self._live.update(
            asset_type=TrackAssetType.VESSEL,
            asset_id=vessel_id,
            latitude=latitude,
            longitude=longitude,
            speed_knots=speed_knots,
            heading_deg=heading_deg,
            destination=destination,
            last_checkpoint=last_checkpoint,
            source="ais",
            eta=eta,
            etd=etd,
        )
        await publish(
            VesselPositionUpdatedEvent(
                vessel_id=vessel_id,
                latitude=latitude,
                longitude=longitude,
                speed_knots=speed_knots,
                heading_deg=heading_deg,
            )
        )
        return live

    def get_position(self, vessel_id: str):
        return self._live.get_live(TrackAssetType.VESSEL, vessel_id)

    def list_positions(self):
        return self._live.list_live(asset_type=TrackAssetType.VESSEL)


ais_tracking_engine = AISTrackingEngine()
