# Live Position + Route Monitoring + ETA engines.

from __future__ import annotations

import math
import time

from events.publisher import publish

from applications.port_erp.geofence.engine import GeofenceEngine, geofence_engine
from applications.port_erp.shared.models import TrackAssetType
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.tracking.events import (
    ArrivalPredictedEvent,
    DelayDetectedEvent,
    ETAChangedEvent,
    ETDChangedEvent,
)
from applications.port_erp.tracking.models import (
    ETAPrediction,
    LivePosition,
    Position,
    RouteHistory,
    RoutePoint,
    TimelineEvent,
)
from applications.port_erp.timeline.engine import TimelineEngine, timeline_engine


def _haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r_km = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    km = 2 * r_km * math.asin(math.sqrt(a))
    return km / 1.852


class LivePositionEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        geofences: GeofenceEngine | None = None,
        timeline: TimelineEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._geofences = geofences or geofence_engine
        self._timeline = timeline or timeline_engine

    def _route_key(self, asset_type: str, asset_id: str) -> str:
        return f"{asset_type}:{asset_id}"

    def get_live(self, asset_type: TrackAssetType | str, asset_id: str) -> LivePosition | None:
        key = self._route_key(
            asset_type.value if isinstance(asset_type, TrackAssetType) else asset_type,
            asset_id,
        )
        return self._store.live_positions.get(key)

    def list_live(self, *, asset_type: TrackAssetType | None = None) -> list[LivePosition]:
        items = self._store.live_positions.list_all()
        if asset_type:
            items = [p for p in items if p.asset_type == asset_type]
        return items

    async def update(
        self,
        *,
        asset_type: TrackAssetType | str,
        asset_id: str,
        latitude: float,
        longitude: float,
        speed_knots: float = 0.0,
        heading_deg: float = 0.0,
        destination: str = "",
        last_checkpoint: str = "",
        source: str = "live",
        eta: float | None = None,
        etd: float | None = None,
    ) -> LivePosition:
        asset_type_enum = TrackAssetType(asset_type) if isinstance(asset_type, str) else asset_type
        key = self._route_key(asset_type_enum.value, asset_id)
        previous = self._store.live_positions.get(key)
        position = Position(
            latitude=latitude,
            longitude=longitude,
            speed_knots=speed_knots,
            heading_deg=heading_deg,
        )
        live = LivePosition(
            position_id=previous.position_id if previous else key,
            asset_type=asset_type_enum,
            asset_id=asset_id,
            position=position,
            destination=destination or (previous.destination if previous else ""),
            last_checkpoint=last_checkpoint or (previous.last_checkpoint if previous else ""),
            eta=eta if eta is not None else (previous.eta if previous else 0.0),
            etd=etd if etd is not None else (previous.etd if previous else 0.0),
            source=source,
        )
        if previous and eta is not None and abs(eta - previous.eta) > 60:
            await publish(
                ETAChangedEvent(
                    asset_type=asset_type_enum.value,
                    asset_id=asset_id,
                    eta=eta,
                    previous_eta=previous.eta,
                )
            )
        if previous and etd is not None and abs(etd - previous.etd) > 60:
            await publish(
                ETDChangedEvent(
                    asset_type=asset_type_enum.value,
                    asset_id=asset_id,
                    etd=etd,
                    previous_etd=previous.etd,
                )
            )
        saved = self._store.live_positions.save(key, live)
        self._append_route(asset_type_enum, asset_id, position, last_checkpoint)
        await self._geofences.evaluate(
            asset_type=asset_type_enum,
            asset_id=asset_id,
            position=position,
        )
        self._timeline.record(
            TimelineEvent(
                asset_type=asset_type_enum.value,
                asset_id=asset_id,
                event_type="position_updated",
                title="Position updated",
                location=last_checkpoint or destination,
                metadata={"lat": latitude, "lon": longitude, "speed": speed_knots},
            )
        )
        return saved

    def _append_route(
        self,
        asset_type: TrackAssetType,
        asset_id: str,
        position: Position,
        checkpoint: str,
    ) -> RouteHistory:
        key = self._route_key(asset_type.value, asset_id)
        history = self._store.route_histories.get(key)
        if history is None:
            history = RouteHistory(route_id=key, asset_type=asset_type, asset_id=asset_id, points=[])
        history.points.append(
            RoutePoint(
                latitude=position.latitude,
                longitude=position.longitude,
                recorded_at=position.recorded_at,
                speed_knots=position.speed_knots,
                checkpoint=checkpoint,
            )
        )
        return self._store.route_histories.save(key, history)

    def route_history(self, asset_type: TrackAssetType | str, asset_id: str) -> RouteHistory | None:
        key = self._route_key(
            asset_type.value if isinstance(asset_type, TrackAssetType) else asset_type,
            asset_id,
        )
        return self._store.route_histories.get(key)


class RouteMonitoringEngine:
    def __init__(self, live: LivePositionEngine | None = None) -> None:
        self._live = live or live_position_engine

    def summary(self, asset_type: str, asset_id: str) -> dict:
        live = self._live.get_live(asset_type, asset_id)
        history = self._live.route_history(asset_type, asset_id)
        return {
            "asset_type": asset_type,
            "asset_id": asset_id,
            "live": live.to_dict() if live else None,
            "points": len(history.points) if history else 0,
            "speed_knots": live.position.speed_knots if live else 0.0,
            "heading_deg": live.position.heading_deg if live else 0.0,
            "destination": live.destination if live else "",
            "last_checkpoint": live.last_checkpoint if live else "",
        }


class ETAEngine:
    def __init__(self, store: PortStore | None = None, live: LivePositionEngine | None = None) -> None:
        self._store = store or port_store
        self._live = live or live_position_engine

    async def predict_arrival(
        self,
        *,
        asset_type: str,
        asset_id: str,
        dest_lat: float,
        dest_lon: float,
        destination: str = "",
        planned_eta: float = 0.0,
    ) -> ETAPrediction:
        live = self._live.get_live(asset_type, asset_id)
        if live is None:
            eta = planned_eta or (time.time() + 86400)
            pred = ETAPrediction(
                asset_type=asset_type,
                asset_id=asset_id,
                eta=eta,
                confidence=0.3,
                destination=destination,
                method="planned_only",
            )
            return self._store.eta_predictions.save(pred.prediction_id, pred)

        distance_nm = _haversine_nm(
            live.position.latitude,
            live.position.longitude,
            dest_lat,
            dest_lon,
        )
        speed = live.position.speed_knots or 12.0
        hours = distance_nm / speed if speed > 0 else 24.0
        eta = time.time() + hours * 3600
        delay = 0.0
        if planned_eta:
            delay = max(0.0, (eta - planned_eta) / 60.0)
        pred = ETAPrediction(
            asset_type=asset_type,
            asset_id=asset_id,
            eta=eta,
            etd=live.etd,
            confidence=0.75 if live.position.speed_knots else 0.5,
            delay_minutes=round(delay, 1),
            destination=destination or live.destination,
        )
        saved = self._store.eta_predictions.save(pred.prediction_id, pred)
        await self._live.update(
            asset_type=asset_type,
            asset_id=asset_id,
            latitude=live.position.latitude,
            longitude=live.position.longitude,
            speed_knots=live.position.speed_knots,
            heading_deg=live.position.heading_deg,
            destination=saved.destination,
            last_checkpoint=live.last_checkpoint,
            source=live.source,
            eta=saved.eta,
            etd=live.etd,
        )
        await publish(
            ArrivalPredictedEvent(
                asset_type=asset_type,
                asset_id=asset_id,
                eta=saved.eta,
                confidence=saved.confidence,
                destination=saved.destination,
            )
        )
        if saved.delay_minutes >= 30:
            await publish(
                DelayDetectedEvent(
                    asset_type=asset_type,
                    asset_id=asset_id,
                    delay_minutes=saved.delay_minutes,
                    reason="eta_behind_plan",
                )
            )
        return saved

    def calculate_etd(self, *, asset_type: str, asset_id: str, hours_from_now: float = 6.0) -> float:
        return time.time() + hours_from_now * 3600


live_position_engine = LivePositionEngine()
route_monitoring_engine = RouteMonitoringEngine(live=live_position_engine)
eta_engine = ETAEngine(live=live_position_engine)
