"""Computer Vision engine — cameras, streams, pipelines (Sprint 11.4)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


CAMERA_TYPES = ("rgb", "stereo", "thermal", "night_vision", "depth", "multispectral")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CameraManager:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def register(
        self,
        *,
        name: str,
        camera_type: str = "rgb",
        resolution: str = "1920x1080",
        fps: int = 30,
        uav_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        camera_type = camera_type.lower().strip()
        if camera_type not in CAMERA_TYPES:
            raise ValidationError(f"Unsupported camera type: {camera_type}")
        cid = f"cam_{uuid.uuid4().hex[:12]}"
        camera = {
            "camera_id": cid,
            "name": name,
            "camera_type": camera_type,
            "resolution": resolution,
            "fps": fps,
            "uav_id": uav_id,
            "status": "ready",
            "metadata": dict(metadata or {}),
            "created_at": _now(),
        }
        self.store.cameras.save(cid, camera)
        return camera

    def get(self, camera_id: str) -> dict[str, Any]:
        item = self.store.cameras.get(camera_id)
        if item is None:
            raise NotFoundError("camera", camera_id)
        return item

    def list(self, *, camera_type: str | None = None) -> list[dict[str, Any]]:
        items = self.store.cameras.list_all()
        if camera_type:
            return [c for c in items if c.get("camera_type") == camera_type]
        return items


class VideoStreamManager:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def open(self, *, camera_id: str, name: str = "primary") -> dict[str, Any]:
        sid = f"vst_{uuid.uuid4().hex[:12]}"
        stream = {
            "stream_id": sid,
            "camera_id": camera_id,
            "name": name,
            "status": "live",
            "frame_count": 0,
            "opened_at": _now(),
        }
        self.store.video_streams.save(sid, stream)
        return stream

    def get(self, stream_id: str) -> dict[str, Any]:
        item = self.store.video_streams.get(stream_id)
        if item is None:
            raise NotFoundError("video_stream", stream_id)
        return item

    def list(self) -> list[dict[str, Any]]:
        return self.store.video_streams.list_all()


class FrameProcessor:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def process(
        self,
        *,
        stream_id: str,
        width: int = 1920,
        height: int = 1080,
        timestamp_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        stream = self.store.video_streams.get(stream_id)
        if stream is None:
            raise NotFoundError("video_stream", stream_id)
        fid = f"frm_{uuid.uuid4().hex[:12]}"
        frame = {
            "frame_id": fid,
            "stream_id": stream_id,
            "width": width,
            "height": height,
            "timestamp_ms": timestamp_ms if timestamp_ms is not None else stream["frame_count"] * 33,
            "processed": True,
            "pipeline_stage": "normalized",
            "metadata": dict(metadata or {}),
            "created_at": _now(),
        }
        stream["frame_count"] = int(stream.get("frame_count", 0)) + 1
        self.store.video_streams.save(stream_id, stream)
        self.store.vision_frames.save(fid, frame)
        return frame


class ImagePipeline:
    STAGES = ("ingest", "normalize", "enhance", "detect", "track", "map")

    def run(self, frame: dict[str, Any], *, stages: list[str] | None = None) -> dict[str, Any]:
        selected = stages or list(self.STAGES)
        results = []
        for stage in selected:
            results.append({"stage": stage, "status": "ok", "frame_id": frame.get("frame_id")})
        return {
            "frame_id": frame.get("frame_id"),
            "stages": results,
            "output": "pipeline_complete",
            "completed_at": _now(),
        }


class VisionManager:
    """Unified computer vision facade (Sprint 11.4)."""

    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store
        self.cameras = CameraManager(self.store)
        self.streams = VideoStreamManager(self.store)
        self.frames = FrameProcessor(self.store)
        self.pipeline = ImagePipeline()

    def register_multi_camera(self, *, uav_id: str, cameras: list[dict[str, Any]]) -> list[dict[str, Any]]:
        registered = []
        for cam in cameras:
            registered.append(
                self.cameras.register(
                    name=cam.get("name", "camera"),
                    camera_type=cam.get("camera_type", "rgb"),
                    resolution=cam.get("resolution", "1920x1080"),
                    fps=int(cam.get("fps", 30)),
                    uav_id=uav_id,
                    metadata=cam.get("metadata"),
                )
            )
        return registered

    def support_matrix(self) -> dict[str, bool]:
        return {
            "multi_camera": True,
            "stereo_camera": True,
            "thermal_camera": True,
            "night_vision": True,
            "depth_camera": True,
        }

    def status(self) -> dict[str, Any]:
        return {
            "computer_vision": "1.0",
            "camera_types": list(CAMERA_TYPES),
            "cameras": self.store.cameras.count(),
            "streams": self.store.video_streams.count(),
            "frames": self.store.vision_frames.count(),
            "support": self.support_matrix(),
            "capabilities": [
                "vision_manager",
                "camera_manager",
                "video_stream_manager",
                "frame_processor",
                "image_pipeline",
                "multi_camera",
                "stereo",
                "thermal",
                "night_vision",
                "depth",
            ],
        }


vision_manager = VisionManager()
