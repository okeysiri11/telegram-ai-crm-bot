"""Radar, navigation management, maritime safety, and AI navigation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

OBJECT_CLASSES = ["vessel", "buoy", "debris", "unknown"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class RadarIntelligence:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_radar(self, *, name: str, coverage_nm: float = 24.0) -> dict[str, Any]:
        if not name:
            raise ValidationError("radar name required")
        rid = _id("nav_rad")
        return self.store.nav_radars.save(
            rid,
            {
                "radar_id": rid,
                "name": name,
                "coverage_nm": float(coverage_nm),
                "status": "online",
                "created_at": _now(),
            },
        )

    def detect_target(
        self,
        *,
        radar_id: str,
        bearing: float,
        range_nm: float,
        object_class: str = "vessel",
    ) -> dict[str, Any]:
        if self.store.nav_radars.get(radar_id) is None:
            raise NotFoundError("radar", radar_id)
        if object_class not in OBJECT_CLASSES:
            raise ValidationError(f"object_class must be one of {OBJECT_CLASSES}")
        tid = _id("nav_tgt")
        return self.store.nav_radar_targets.save(
            tid,
            {
                "target_id": tid,
                "radar_id": radar_id,
                "bearing": float(bearing),
                "range_nm": float(range_nm),
                "object_class": object_class,
                "tracked": True,
                "at": _now(),
            },
        )

    def blind_zone(self, *, radar_id: str, sector: str, severity: str = "medium") -> dict[str, Any]:
        if self.store.nav_radars.get(radar_id) is None:
            raise NotFoundError("radar", radar_id)
        bid = _id("nav_blind")
        return self.store.nav_radar_blinds.save(
            bid,
            {
                "blind_id": bid,
                "radar_id": radar_id,
                "sector": sector,
                "severity": severity,
                "at": _now(),
            },
        )

    def alert(self, *, radar_id: str, message: str, level: str = "warning") -> dict[str, Any]:
        if self.store.nav_radars.get(radar_id) is None:
            raise NotFoundError("radar", radar_id)
        aid = _id("nav_ral")
        return self.store.nav_radar_alerts.save(
            aid,
            {
                "alert_id": aid,
                "radar_id": radar_id,
                "message": message,
                "level": level,
                "at": _now(),
            },
        )

    def analytics(self, radar_id: str) -> dict[str, Any]:
        if self.store.nav_radars.get(radar_id) is None:
            raise NotFoundError("radar", radar_id)
        targets = [t for t in self.store.nav_radar_targets.list_all() if t.get("radar_id") == radar_id]
        return {
            "radar_id": radar_id,
            "targets": len(targets),
            "alerts": len([a for a in self.store.nav_radar_alerts.list_all() if a.get("radar_id") == radar_id]),
            "blind_zones": len(
                [b for b in self.store.nav_radar_blinds.list_all() if b.get("radar_id") == radar_id]
            ),
        }

    def status(self) -> dict[str, Any]:
        return {
            "radars": self.store.nav_radars.count(),
            "targets": self.store.nav_radar_targets.count(),
            "alerts": self.store.nav_radar_alerts.count(),
        }


class NavigationManagement:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def create_route(self, *, name: str, waypoints: list[dict[str, float]] | None = None) -> dict[str, Any]:
        if not name:
            raise ValidationError("route name required")
        rid = _id("nav_rte")
        return self.store.nav_routes.save(
            rid,
            {
                "route_id": rid,
                "name": name,
                "waypoints": waypoints or [],
                "created_at": _now(),
            },
        )

    def fairway(self, *, name: str, depth_m: float = 14.0) -> dict[str, Any]:
        if not name:
            raise ValidationError("fairway name required")
        fid = _id("nav_fw")
        return self.store.nav_fairways.save(
            fid, {"fairway_id": fid, "name": name, "depth_m": float(depth_m), "created_at": _now()}
        )

    def pilot_boarding(self, *, name: str, lat: float, lon: float) -> dict[str, Any]:
        pid = _id("nav_pbz")
        return self.store.nav_pilot_zones.save(
            pid,
            {
                "zone_id": pid,
                "name": name,
                "lat": float(lat),
                "lon": float(lon),
                "created_at": _now(),
            },
        )

    def anchorage(self, *, name: str, capacity: int = 10) -> dict[str, Any]:
        if not name:
            raise ValidationError("anchorage name required")
        aid = _id("nav_anch")
        return self.store.nav_anchorages.save(
            aid, {"anchorage_id": aid, "name": name, "capacity": int(capacity), "created_at": _now()}
        )

    def restriction(self, *, title: str, area: str, reason: str = "") -> dict[str, Any]:
        if not title:
            raise ValidationError("restriction title required")
        rid = _id("nav_nrest")
        return self.store.nav_restrictions.save(
            rid,
            {
                "restriction_id": rid,
                "title": title,
                "area": area,
                "reason": reason,
                "active": True,
                "at": _now(),
            },
        )

    def weather_overlay(self, *, area: str, wind_kn: float, visibility_nm: float) -> dict[str, Any]:
        wid = _id("nav_wx")
        return self.store.nav_weather.save(
            wid,
            {
                "overlay_id": wid,
                "area": area,
                "wind_kn": float(wind_kn),
                "visibility_nm": float(visibility_nm),
                "at": _now(),
            },
        )

    def sea_state(self, *, area: str, douglas_scale: int = 3) -> dict[str, Any]:
        sid = _id("nav_sea")
        return self.store.nav_sea_state.save(
            sid,
            {
                "reading_id": sid,
                "area": area,
                "douglas_scale": int(douglas_scale),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "routes": self.store.nav_routes.count(),
            "fairways": self.store.nav_fairways.count(),
            "pilot_zones": self.store.nav_pilot_zones.count(),
            "anchorages": self.store.nav_anchorages.count(),
            "restrictions": self.store.nav_restrictions.count(),
        }


class MaritimeSafety:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def collision_risk(self, *, vessel_a: str, vessel_b: str, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 1:
            raise ValidationError("score must be 0..1")
        rid = _id("nav_crisk")
        return self.store.nav_safety_risks.save(
            rid,
            {
                "risk_id": rid,
                "vessel_a": vessel_a,
                "vessel_b": vessel_b,
                "score": score,
                "level": "critical" if score >= 0.75 else "elevated" if score >= 0.45 else "normal",
                "at": _now(),
            },
        )

    def warning(self, *, title: str, message: str, kind: str = "navigation") -> dict[str, Any]:
        if not title:
            raise ValidationError("warning title required")
        wid = _id("nav_warn")
        return self.store.nav_warnings.save(
            wid,
            {
                "warning_id": wid,
                "title": title,
                "message": message,
                "kind": kind,
                "at": _now(),
            },
        )

    def emergency(self, *, vessel_id: str, nature: str) -> dict[str, Any]:
        eid = _id("nav_emg")
        return self.store.nav_emergencies.save(
            eid,
            {
                "emergency_id": eid,
                "vessel_id": vessel_id,
                "nature": nature,
                "sar_support": True,
                "status": "active",
                "at": _now(),
            },
        )

    def restricted_zone_alert(self, *, zone: str, vessel_id: str) -> dict[str, Any]:
        aid = _id("nav_rzal")
        return self.store.nav_zone_alerts.save(
            aid, {"alert_id": aid, "zone": zone, "vessel_id": vessel_id, "at": _now()}
        )

    def environmental_hazard(self, *, hazard: str, severity: str = "medium") -> dict[str, Any]:
        hid = _id("nav_env")
        return self.store.nav_env_hazards.save(
            hid, {"hazard_id": hid, "hazard": hazard, "severity": severity, "at": _now()}
        )

    def status(self) -> dict[str, Any]:
        return {
            "risks": self.store.nav_safety_risks.count(),
            "warnings": self.store.nav_warnings.count(),
            "emergencies": self.store.nav_emergencies.count(),
            "zone_alerts": self.store.nav_zone_alerts.count(),
        }


class AINavigationIntelligence:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def predict_traffic(self, *, area: str, horizon_hours: int = 6) -> dict[str, Any]:
        pid = _id("nav_tpred")
        return self.store.nav_ai_traffic.save(
            pid,
            {
                "prediction_id": pid,
                "area": area,
                "horizon_hours": int(horizon_hours),
                "flow_index": 0.62,
                "congestion_risk": 0.38,
                "at": _now(),
            },
        )

    def optimal_route(self, *, origin: str, destination: str) -> dict[str, Any]:
        if not origin or not destination:
            raise ValidationError("origin and destination required")
        rid = _id("nav_oroute")
        return self.store.nav_ai_routes.save(
            rid,
            {
                "route_id": rid,
                "origin": origin,
                "destination": destination,
                "optimized": True,
                "eta_gain_hours": 1.4,
                "at": _now(),
            },
        )

    def arrival_optimization(self, *, vessel_id: str, requested_eta: str) -> dict[str, Any]:
        oid = _id("nav_aopt")
        return self.store.nav_ai_arrival.save(
            oid,
            {
                "optimization_id": oid,
                "vessel_id": vessel_id,
                "requested_eta": requested_eta,
                "recommended_speed_kn": 12.5,
                "at": _now(),
            },
        )

    def berth_recommendation(self, *, vessel_id: str, candidates: list[str] | None = None) -> dict[str, Any]:
        opts = candidates or ["Berth A1", "Berth B2"]
        bid = _id("nav_berth")
        return self.store.nav_ai_berth.save(
            bid,
            {
                "recommendation_id": bid,
                "vessel_id": vessel_id,
                "candidates": opts,
                "recommended": opts[0],
                "at": _now(),
            },
        )

    def operational_risk(self, *, vessel_id: str, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 1:
            raise ValidationError("score must be 0..1")
        rid = _id("nav_orisk")
        return self.store.nav_ai_risk.save(
            rid,
            {
                "score_id": rid,
                "vessel_id": vessel_id,
                "score": score,
                "band": "high" if score >= 0.65 else "medium" if score >= 0.35 else "low",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "traffic_predictions": self.store.nav_ai_traffic.count(),
            "routes": self.store.nav_ai_routes.count(),
            "berth_recs": self.store.nav_ai_berth.count(),
        }
