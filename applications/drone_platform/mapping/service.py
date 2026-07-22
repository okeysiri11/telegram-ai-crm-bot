"""SLAM & Mapping intelligence (Sprint 11.4)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MappingService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def visual_slam(self, *, frame_ids: list[str], seed_pose: dict[str, float] | None = None) -> dict[str, Any]:
        mid = f"map_{uuid.uuid4().hex[:12]}"
        slam = {
            "map_id": mid,
            "map_type": "visual_slam",
            "frame_ids": list(frame_ids),
            "pose": dict(seed_pose or {"x": 0, "y": 0, "z": 0, "yaw": 0}),
            "keyframes": len(frame_ids),
            "status": "mapping",
            "created_at": _now(),
        }
        self.store.maps.save(mid, slam)
        return slam

    def feature_mapping(self, *, map_id: str, features: list[dict[str, Any]]) -> dict[str, Any]:
        m = self.get_map(map_id)
        m["features"] = list(features)
        m["feature_count"] = len(features)
        m["updated_at"] = _now()
        self.store.maps.save(map_id, m)
        return m

    def point_cloud(self, *, map_id: str, points: list[dict[str, float]] | None = None) -> dict[str, Any]:
        self.get_map(map_id)
        pts = list(points or [{"x": 0, "y": 0, "z": 0}, {"x": 1, "y": 0, "z": 0.2}, {"x": 1, "y": 1, "z": 0.1}])
        pid = f"pcd_{uuid.uuid4().hex[:12]}"
        cloud = {
            "point_cloud_id": pid,
            "map_id": map_id,
            "points": pts,
            "point_count": len(pts),
            "created_at": _now(),
        }
        self.store.point_clouds.save(pid, cloud)
        return cloud

    def reconstruct_3d(self, *, map_id: str, point_cloud_id: str) -> dict[str, Any]:
        cloud = self.store.point_clouds.get(point_cloud_id)
        if cloud is None:
            raise NotFoundError("point_cloud", point_cloud_id)
        m = self.get_map(map_id)
        m["reconstruction"] = {
            "point_cloud_id": point_cloud_id,
            "mesh_ready": True,
            "vertices": cloud.get("point_count", 0),
            "status": "complete",
        }
        m["updated_at"] = _now()
        self.store.maps.save(map_id, m)
        return m

    def terrain_mapping(self, *, bounds: dict[str, float], samples: list[dict[str, float]] | None = None) -> dict[str, Any]:
        mid = f"map_{uuid.uuid4().hex[:12]}"
        samples = list(samples or [{"lat": bounds.get("south", 0), "lon": bounds.get("west", 0), "elev_m": 10}])
        m = {
            "map_id": mid,
            "map_type": "terrain",
            "bounds": bounds,
            "samples": samples,
            "sample_count": len(samples),
            "created_at": _now(),
        }
        self.store.maps.save(mid, m)
        return m

    def orthophoto(self, *, map_id: str, resolution_cm: float = 5.0) -> dict[str, Any]:
        m = self.get_map(map_id)
        m["orthophoto"] = {"resolution_cm": resolution_cm, "status": "generated", "tiles": 4}
        m["updated_at"] = _now()
        self.store.maps.save(map_id, m)
        return m

    def digital_elevation_model(self, *, map_id: str, grid_size: int = 32) -> dict[str, Any]:
        m = self.get_map(map_id)
        m["dem"] = {"grid_size": grid_size, "status": "generated", "units": "meters"}
        m["updated_at"] = _now()
        self.store.maps.save(map_id, m)
        return m

    def local_map_cache(self, *, map_id: str, radius_m: float = 200.0) -> dict[str, Any]:
        m = self.get_map(map_id)
        cache = {"map_id": map_id, "radius_m": radius_m, "cached": True, "at": _now()}
        m["local_cache"] = cache
        self.store.maps.save(map_id, m)
        return cache

    def mission_map_builder(self, *, mission_id: str, waypoints: list[dict[str, Any]]) -> dict[str, Any]:
        if not waypoints:
            raise ValidationError("waypoints required for mission map")
        mid = f"map_{uuid.uuid4().hex[:12]}"
        m = {
            "map_id": mid,
            "map_type": "mission",
            "mission_id": mission_id,
            "waypoints": waypoints,
            "layers": ["waypoints", "geofence", "terrain"],
            "created_at": _now(),
        }
        self.store.maps.save(mid, m)
        return m

    def get_map(self, map_id: str) -> dict[str, Any]:
        item = self.store.maps.get(map_id)
        if item is None:
            raise NotFoundError("map", map_id)
        return item

    def list_maps(self) -> list[dict[str, Any]]:
        return self.store.maps.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "slam_mapping": "1.0",
            "map_count": self.store.maps.count(),
            "point_cloud_count": self.store.point_clouds.count(),
            "capabilities": [
                "visual_slam",
                "feature_mapping",
                "point_cloud",
                "3d_reconstruction",
                "terrain_mapping",
                "orthophoto",
                "dem",
                "local_map_cache",
                "mission_map_builder",
            ],
        }


mapping_service = MappingService()
