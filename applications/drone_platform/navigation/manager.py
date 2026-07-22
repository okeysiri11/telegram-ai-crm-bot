"""Resilient Navigation Manager — multi-source nav, GPS/RTK, dead reckoning (Sprint 11.9)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class NavigationManager:
    """Navigation Manager + health, multi-source estimator, GPS/RTK, visual, dead reckoning, confidence."""

    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create_session(
        self,
        *,
        aircraft_id: str,
        sources: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not aircraft_id:
            raise ValidationError("aircraft_id required")
        nid = f"nav_{uuid.uuid4().hex[:12]}"
        session = {
            "nav_session_id": nid,
            "aircraft_id": aircraft_id,
            "sources": list(sources or ["gps", "imu", "baro"]),
            "position": {"lat": 0.0, "lon": 0.0, "alt": 0.0},
            "confidence": 0.0,
            "health": "unknown",
            "gps": {"fix_count": 0, "fix_ok": False, "hdop": 99.0},
            "rtk": {"fixed": False, "age_s": None},
            "visual_nav": {"enabled": False, "quality": 0.0},
            "dead_reckoning": {"active": False, "drift_m": 0.0},
            "metadata": dict(metadata or {}),
            "updated_at": _now(),
            "created_at": _now(),
        }
        self.store.nav_sessions.save(nid, session)
        return session

    def get_session(self, nav_session_id: str) -> dict[str, Any]:
        item = self.store.nav_sessions.get(nav_session_id)
        if item is None:
            raise NotFoundError("nav_session", nav_session_id)
        return item

    def navigation_health(self, nav_session_id: str) -> dict[str, Any]:
        s = self.get_session(nav_session_id)
        gps_ok = bool(s.get("gps", {}).get("fix_ok"))
        conf = float(s.get("confidence", 0))
        health = "healthy" if gps_ok and conf >= 0.7 else "degraded" if conf >= 0.4 else "critical"
        s["health"] = health
        self.store.nav_sessions.save(nav_session_id, s)
        return {"nav_session_id": nav_session_id, "health": health, "confidence": conf, "gps_ok": gps_ok, "sources": s.get("sources")}

    def update_gps(self, nav_session_id: str, *, fix_ok: bool, sat_count: int = 0, hdop: float = 1.0, lat: float = 0, lon: float = 0, alt: float = 0) -> dict[str, Any]:
        s = self.get_session(nav_session_id)
        s["gps"] = {"fix_ok": fix_ok, "sat_count": sat_count, "hdop": hdop}
        if fix_ok:
            s["position"] = {"lat": lat, "lon": lon, "alt": alt}
            s["dead_reckoning"]["active"] = False
        s["updated_at"] = _now()
        self.store.nav_sessions.save(nav_session_id, s)
        return s

    def update_rtk(self, nav_session_id: str, *, fixed: bool, age_s: float | None = 0.5) -> dict[str, Any]:
        s = self.get_session(nav_session_id)
        s["rtk"] = {"fixed": fixed, "age_s": age_s}
        if fixed and "rtk" not in s["sources"]:
            s["sources"].append("rtk")
        s["updated_at"] = _now()
        self.store.nav_sessions.save(nav_session_id, s)
        return s

    def visual_navigation_interface(self, nav_session_id: str, *, enabled: bool = True, quality: float = 0.8) -> dict[str, Any]:
        s = self.get_session(nav_session_id)
        s["visual_nav"] = {"enabled": enabled, "quality": quality}
        if enabled and "visual" not in s["sources"]:
            s["sources"].append("visual")
        s["updated_at"] = _now()
        self.store.nav_sessions.save(nav_session_id, s)
        return s["visual_nav"]

    def dead_reckoning(self, nav_session_id: str, *, dt_s: float = 1.0, vx: float = 0, vy: float = 0, vz: float = 0) -> dict[str, Any]:
        s = self.get_session(nav_session_id)
        pos = s["position"]
        # approximate meters to degrees
        pos["lat"] = float(pos.get("lat", 0)) + (vy * dt_s) / 111_320
        pos["lon"] = float(pos.get("lon", 0)) + (vx * dt_s) / 111_320
        pos["alt"] = float(pos.get("alt", 0)) + vz * dt_s
        drift = float(s.get("dead_reckoning", {}).get("drift_m", 0)) + abs(vx * dt_s) * 0.05 + abs(vy * dt_s) * 0.05
        s["position"] = pos
        s["dead_reckoning"] = {"active": True, "drift_m": round(drift, 3)}
        s["updated_at"] = _now()
        self.store.nav_sessions.save(nav_session_id, s)
        return s["dead_reckoning"] | {"position": pos}

    def multi_source_estimate(self, nav_session_id: str) -> dict[str, Any]:
        s = self.get_session(nav_session_id)
        weights = []
        if s.get("gps", {}).get("fix_ok"):
            weights.append(("gps", 0.5 if not s.get("rtk", {}).get("fixed") else 0.7))
        if s.get("rtk", {}).get("fixed"):
            weights.append(("rtk", 0.85))
        if s.get("visual_nav", {}).get("enabled"):
            weights.append(("visual", 0.4 * float(s["visual_nav"].get("quality", 0))))
        if s.get("dead_reckoning", {}).get("active"):
            weights.append(("dead_reckoning", max(0.1, 0.35 - float(s["dead_reckoning"].get("drift_m", 0)) / 100)))
        total_w = sum(w for _, w in weights) or 0.01
        confidence = min(1.0, total_w / 1.2)
        s["confidence"] = round(confidence, 3)
        s["estimate"] = {
            "position": s["position"],
            "sources_used": [n for n, _ in weights],
            "weights": {n: round(w, 3) for n, w in weights},
            "confidence": s["confidence"],
        }
        s["updated_at"] = _now()
        self.store.nav_sessions.save(nav_session_id, s)
        return s["estimate"]

    def position_confidence(self, nav_session_id: str) -> dict[str, Any]:
        estimate = self.multi_source_estimate(nav_session_id)
        level = "high" if estimate["confidence"] >= 0.75 else "medium" if estimate["confidence"] >= 0.45 else "low"
        return {"nav_session_id": nav_session_id, "confidence": estimate["confidence"], "level": level, "sources_used": estimate["sources_used"]}

    def status(self) -> dict[str, Any]:
        return {"navigation_manager": "1.0", "sessions": len(self.store.nav_sessions.list_all()), "ready": True}


navigation_manager = NavigationManager()
