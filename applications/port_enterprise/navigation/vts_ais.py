"""VTS control center and AIS integration."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class VesselTrafficService:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def open_center(self, *, name: str, port_id: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("VTS center name required")
        cid = _id("nav_vts")
        return self.store.nav_vts_centers.save(
            cid,
            {
                "center_id": cid,
                "name": name,
                "port_id": port_id,
                "status": "active",
                "created_at": _now(),
            },
        )

    def monitor_traffic(self, *, center_id: str, vessel_count: int = 0, density: float = 0.0) -> dict[str, Any]:
        if self.store.nav_vts_centers.get(center_id) is None:
            raise NotFoundError("vts_center", center_id)
        mid = _id("nav_mon")
        level = "high" if density >= 0.7 else "medium" if density >= 0.4 else "low"
        return self.store.nav_traffic.save(
            mid,
            {
                "monitor_id": mid,
                "center_id": center_id,
                "vessel_count": int(vessel_count),
                "density": float(density),
                "density_level": level,
                "at": _now(),
            },
        )

    def arrival_queue(self, *, center_id: str, vessel_id: str, eta: str = "") -> dict[str, Any]:
        if self.store.nav_vts_centers.get(center_id) is None:
            raise NotFoundError("vts_center", center_id)
        qid = _id("nav_aq")
        return self.store.nav_arrival_q.save(
            qid,
            {
                "queue_id": qid,
                "center_id": center_id,
                "vessel_id": vessel_id,
                "eta": eta,
                "status": "queued",
                "at": _now(),
            },
        )

    def departure_queue(self, *, center_id: str, vessel_id: str, etd: str = "") -> dict[str, Any]:
        if self.store.nav_vts_centers.get(center_id) is None:
            raise NotFoundError("vts_center", center_id)
        qid = _id("nav_dq")
        return self.store.nav_departure_q.save(
            qid,
            {
                "queue_id": qid,
                "center_id": center_id,
                "vessel_id": vessel_id,
                "etd": etd,
                "status": "queued",
                "at": _now(),
            },
        )

    def navigation_assist(self, *, center_id: str, vessel_id: str, advice: str) -> dict[str, Any]:
        if self.store.nav_vts_centers.get(center_id) is None:
            raise NotFoundError("vts_center", center_id)
        aid = _id("nav_asst")
        return self.store.nav_assistance.save(
            aid,
            {
                "assist_id": aid,
                "center_id": center_id,
                "vessel_id": vessel_id,
                "advice": advice,
                "at": _now(),
            },
        )

    def collision_watch(self, *, center_id: str, vessel_a: str, vessel_b: str, cpa_nm: float) -> dict[str, Any]:
        if self.store.nav_vts_centers.get(center_id) is None:
            raise NotFoundError("vts_center", center_id)
        wid = _id("nav_col")
        risk = "critical" if cpa_nm < 0.25 else "elevated" if cpa_nm < 0.5 else "normal"
        return self.store.nav_collision.save(
            wid,
            {
                "watch_id": wid,
                "center_id": center_id,
                "vessel_a": vessel_a,
                "vessel_b": vessel_b,
                "cpa_nm": float(cpa_nm),
                "risk": risk,
                "prevention": risk != "normal",
                "at": _now(),
            },
        )

    def restricted_area(self, *, center_id: str, area: str, vessel_id: str = "", breached: bool = False) -> dict[str, Any]:
        if self.store.nav_vts_centers.get(center_id) is None:
            raise NotFoundError("vts_center", center_id)
        rid = _id("nav_ra")
        return self.store.nav_restricted.save(
            rid,
            {
                "monitor_id": rid,
                "center_id": center_id,
                "area": area,
                "vessel_id": vessel_id,
                "breached": bool(breached),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "centers": self.store.nav_vts_centers.count(),
            "traffic_snapshots": self.store.nav_traffic.count(),
            "arrival_queue": self.store.nav_arrival_q.count(),
            "departure_queue": self.store.nav_departure_q.count(),
            "collision_watches": self.store.nav_collision.count(),
        }


class AISIntegration:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_receiver(self, *, name: str, station: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("receiver name required")
        rid = _id("nav_aisr")
        return self.store.nav_ais_receivers.save(
            rid, {"receiver_id": rid, "name": name, "station": station, "created_at": _now()}
        )

    def process_message(
        self,
        *,
        receiver_id: str,
        mmsi: str,
        lat: float,
        lon: float,
        sog: float = 0.0,
        cog: float = 0.0,
        msg_type: int = 1,
    ) -> dict[str, Any]:
        if self.store.nav_ais_receivers.get(receiver_id) is None:
            raise NotFoundError("ais_receiver", receiver_id)
        if not mmsi:
            raise ValidationError("mmsi required")
        mid = _id("nav_aism")
        msg = self.store.nav_ais_messages.save(
            mid,
            {
                "message_id": mid,
                "receiver_id": receiver_id,
                "mmsi": mmsi,
                "lat": float(lat),
                "lon": float(lon),
                "sog": float(sog),
                "cog": float(cog),
                "msg_type": int(msg_type),
                "at": _now(),
            },
        )
        tid = _id("nav_track")
        self.store.nav_ais_tracks.save(
            tid,
            {
                "track_id": tid,
                "mmsi": mmsi,
                "lat": float(lat),
                "lon": float(lon),
                "sog": float(sog),
                "cog": float(cog),
                "message_id": mid,
                "at": _now(),
            },
        )
        hid = _id("nav_pos")
        self.store.nav_ais_history.save(
            hid,
            {"history_id": hid, "mmsi": mmsi, "lat": float(lat), "lon": float(lon), "at": _now()},
        )
        return msg

    def eta_predict(self, *, mmsi: str, remaining_nm: float, sog: float) -> dict[str, Any]:
        if not mmsi:
            raise ValidationError("mmsi required")
        hours = round(remaining_nm / max(sog, 0.1), 2)
        eid = _id("nav_eta")
        return self.store.nav_ais_eta.save(
            eid,
            {
                "eta_id": eid,
                "mmsi": mmsi,
                "remaining_nm": float(remaining_nm),
                "sog": float(sog),
                "eta_hours": hours,
                "at": _now(),
            },
        )

    def route_history(self, mmsi: str) -> dict[str, Any]:
        points = [h for h in self.store.nav_ais_history.list_all() if h.get("mmsi") == mmsi]
        return {"mmsi": mmsi, "points": len(points), "history": points[-20:]}

    def status(self) -> dict[str, Any]:
        return {
            "receivers": self.store.nav_ais_receivers.count(),
            "messages": self.store.nav_ais_messages.count(),
            "tracks": self.store.nav_ais_tracks.count(),
            "history_points": self.store.nav_ais_history.count(),
        }
