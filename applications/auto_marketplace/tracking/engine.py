# Shipment Tracking — GPS, ETA, geofencing, timeline, notifications.

from __future__ import annotations

import time

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transport.models import TrackingSession


class TrackingEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def start(self, *, shipment_id: str, eta: float = 0.0) -> TrackingSession:
        if not shipment_id:
            raise ValidationError("shipment_id is required")
        session = TrackingSession(shipment_id=shipment_id, status="tracking", eta=eta or (time.time() + 86400))
        session.notifications.append({"event": "tracking_started", "at": time.time()})
        return self._store.tracking_sessions.save(session.tracking_id, session)

    def get(self, tracking_id: str) -> TrackingSession:
        item = self._store.tracking_sessions.get(tracking_id)
        if item is None:
            raise NotFoundError("TrackingSession", tracking_id)
        return item

    def update_gps(self, tracking_id: str, *, lat: float, lon: float, status: str = "in_transit") -> TrackingSession:
        session = self.get(tracking_id)
        session.lat = lat
        session.lon = lon
        session.status = status
        session.updated_at = time.time()
        session.route_history.append({"lat": lat, "lon": lon, "at": time.time(), "status": status})
        for fence in session.geofences:
            if abs(fence.get("lat", 0) - lat) < fence.get("radius_deg", 0.05) and abs(
                fence.get("lon", 0) - lon
            ) < fence.get("radius_deg", 0.05):
                session.notifications.append(
                    {"event": "geofence_enter", "fence": fence.get("name", ""), "at": time.time()}
                )
        # crude ETA shrink
        remaining = max(0.0, session.eta - time.time())
        session.eta = time.time() + remaining * 0.98
        return self._store.tracking_sessions.save(tracking_id, session)

    def add_geofence(self, tracking_id: str, *, name: str, lat: float, lon: float, radius_deg: float = 0.05) -> TrackingSession:
        session = self.get(tracking_id)
        session.geofences.append({"name": name, "lat": lat, "lon": lon, "radius_deg": radius_deg})
        return self._store.tracking_sessions.save(tracking_id, session)

    def predict_eta(self, tracking_id: str) -> dict:
        session = self.get(tracking_id)
        delay_risk = 0.1 if len(session.route_history) < 2 else min(0.8, 0.05 * len(session.route_history))
        return {
            "tracking_id": tracking_id,
            "eta": session.eta,
            "eta_hours": max(0.0, round((session.eta - time.time()) / 3600, 2)),
            "delay_risk": round(delay_risk, 2),
            "status": session.status,
        }

    def timeline(self, tracking_id: str) -> list[dict]:
        session = self.get(tracking_id)
        return list(session.route_history) + list(session.notifications)

    def notify(self, tracking_id: str, message: str) -> TrackingSession:
        session = self.get(tracking_id)
        session.notifications.append({"event": "notify", "message": message, "at": time.time()})
        return self._store.tracking_sessions.save(tracking_id, session)

    def for_shipment(self, shipment_id: str) -> TrackingSession | None:
        for s in self._store.tracking_sessions.list_all():
            if s.shipment_id == shipment_id:
                return s
        return None

    def metrics(self) -> dict:
        return {"tracking_sessions": self._store.tracking_sessions.count()}


tracking_engine = TrackingEngine()
