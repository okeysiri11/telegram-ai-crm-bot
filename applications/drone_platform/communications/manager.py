"""Communications — link quality, telemetry router, failover, bandwidth, latency (Sprint 11.9)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CommunicationManager:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def open_link(
        self,
        *,
        aircraft_id: str,
        primary: str = "lte",
        secondary: str = "radio",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not aircraft_id:
            raise ValidationError("aircraft_id required")
        lid = f"lnk_{uuid.uuid4().hex[:12]}"
        link = {
            "link_id": lid,
            "aircraft_id": aircraft_id,
            "active": primary,
            "links": {
                primary: {"quality": 0.9, "latency_ms": 40, "bandwidth_kbps": 800, "up": True},
                secondary: {"quality": 0.7, "latency_ms": 80, "bandwidth_kbps": 200, "up": True},
            },
            "router": {"telemetry_path": primary, "failover": True},
            "recorder": {"enabled": False, "frames": 0},
            "metadata": dict(metadata or {}),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.comm_links.save(lid, link)
        return link

    def get_link(self, link_id: str) -> dict[str, Any]:
        item = self.store.comm_links.get(link_id)
        if item is None:
            raise NotFoundError("comm_link", link_id)
        return item

    def link_quality(self, link_id: str) -> dict[str, Any]:
        link = self.get_link(link_id)
        active = link["active"]
        q = link["links"].get(active, {})
        return {"link_id": link_id, "active": active, "quality": q.get("quality", 0), "up": q.get("up", False), "all": link["links"]}

    def update_quality(self, link_id: str, *, channel: str, quality: float, latency_ms: float = 50, bandwidth_kbps: float = 500, up: bool = True) -> dict[str, Any]:
        link = self.get_link(link_id)
        if channel not in link["links"]:
            link["links"][channel] = {}
        link["links"][channel].update({"quality": quality, "latency_ms": latency_ms, "bandwidth_kbps": bandwidth_kbps, "up": up})
        link["updated_at"] = _now()
        self.store.comm_links.save(link_id, link)
        return link

    def telemetry_router(self, link_id: str, *, prefer: str | None = None) -> dict[str, Any]:
        link = self.get_link(link_id)
        path = prefer or link["active"]
        if path not in link["links"] or not link["links"][path].get("up"):
            # pick best up link
            up_links = [(n, v) for n, v in link["links"].items() if v.get("up")]
            path = max(up_links, key=lambda x: x[1].get("quality", 0))[0] if up_links else link["active"]
        link["router"]["telemetry_path"] = path
        link["active"] = path
        link["updated_at"] = _now()
        self.store.comm_links.save(link_id, link)
        return {"link_id": link_id, "telemetry_path": path, "router": link["router"]}

    def automatic_link_switching(self, link_id: str, *, quality_threshold: float = 0.5) -> dict[str, Any]:
        link = self.get_link(link_id)
        active = link["active"]
        current_q = float(link["links"].get(active, {}).get("quality", 0))
        switched = False
        if current_q < quality_threshold or not link["links"].get(active, {}).get("up"):
            candidates = [(n, v) for n, v in link["links"].items() if n != active and v.get("up") and float(v.get("quality", 0)) >= quality_threshold]
            if candidates:
                best = max(candidates, key=lambda x: x[1].get("quality", 0))[0]
                link["active"] = best
                link["router"]["telemetry_path"] = best
                switched = True
        link["updated_at"] = _now()
        self.store.comm_links.save(link_id, link)
        return {"link_id": link_id, "active": link["active"], "switched": switched, "previous": active}

    def bandwidth_optimizer(self, link_id: str) -> dict[str, Any]:
        link = self.get_link(link_id)
        active = link["links"].get(link["active"], {})
        bw = float(active.get("bandwidth_kbps", 0))
        mode = "full" if bw >= 500 else "reduced" if bw >= 150 else "critical"
        profile = {"mode": mode, "telemetry_hz": 10 if mode == "full" else 5 if mode == "reduced" else 1, "video": mode == "full"}
        link["bandwidth_profile"] = profile
        self.store.comm_links.save(link_id, link)
        return {"link_id": link_id, "bandwidth_kbps": bw, "profile": profile}

    def latency_monitor(self, link_id: str) -> dict[str, Any]:
        link = self.get_link(link_id)
        samples = {n: v.get("latency_ms", 0) for n, v in link["links"].items()}
        active_lat = samples.get(link["active"], 0)
        return {"link_id": link_id, "active_latency_ms": active_lat, "samples": samples, "ok": active_lat < 200}

    def recorder(self, link_id: str, *, enable: bool = True, frames: int = 0) -> dict[str, Any]:
        link = self.get_link(link_id)
        link["recorder"] = {"enabled": enable, "frames": frames or link["recorder"].get("frames", 0)}
        if enable:
            link["recorder"]["frames"] = int(link["recorder"]["frames"]) + max(1, frames)
        self.store.comm_links.save(link_id, link)
        return link["recorder"] | {"link_id": link_id}

    def diagnostics(self, link_id: str) -> dict[str, Any]:
        link = self.get_link(link_id)
        issues = []
        for name, meta in link["links"].items():
            if not meta.get("up"):
                issues.append(f"{name}_down")
            if float(meta.get("quality", 0)) < 0.4:
                issues.append(f"{name}_poor_quality")
            if float(meta.get("latency_ms", 0)) > 250:
                issues.append(f"{name}_high_latency")
        return {"link_id": link_id, "active": link["active"], "issues": issues, "healthy": not issues, "at": _now()}

    def status(self) -> dict[str, Any]:
        return {"communications": "1.0", "links": len(self.store.comm_links.list_all()), "ready": True}


communication_manager = CommunicationManager()
