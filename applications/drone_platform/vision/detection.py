"""Object detection, tracking, and classification (Sprint 11.4)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


DETECTION_CLASSES = (
    "vehicle",
    "person",
    "aircraft",
    "ship",
    "building",
    "road",
    "tree",
    "power_line",
    "landing_zone",
    "obstacle",
    "target",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ObjectDetector:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def detect(
        self,
        *,
        frame_id: str,
        annotations: list[dict[str, Any]] | None = None,
        model: str = "drone_cv_v1",
    ) -> dict[str, Any]:
        anns = list(annotations or [])
        if not anns:
            # synthetic demo detections for empty annotation payload
            anns = [
                {"class": "obstacle", "confidence": 0.82, "bbox": [100, 120, 80, 60]},
                {"class": "landing_zone", "confidence": 0.76, "bbox": [400, 300, 160, 120]},
            ]
        detections = []
        for ann in anns:
            cls = str(ann.get("class", "obstacle")).lower()
            if cls not in DETECTION_CLASSES:
                raise ValidationError(f"Unsupported detection class: {cls}")
            did = f"det_{uuid.uuid4().hex[:12]}"
            item = {
                "detection_id": did,
                "frame_id": frame_id,
                "class": cls,
                "confidence": float(ann.get("confidence", 0.5)),
                "bbox": list(ann.get("bbox") or [0, 0, 0, 0]),
                "model": model,
                "created_at": _now(),
            }
            self.store.detections.save(did, item)
            detections.append(item)
        return {"frame_id": frame_id, "count": len(detections), "detections": detections}

    def detect_class(self, *, frame_id: str, class_name: str, **kwargs: Any) -> dict[str, Any]:
        return self.detect(
            frame_id=frame_id,
            annotations=[{"class": class_name, "confidence": kwargs.get("confidence", 0.8), "bbox": kwargs.get("bbox", [10, 10, 50, 50])}],
            model=kwargs.get("model", "drone_cv_v1"),
        )

    def classify(self, detection_id: str, *, label: str | None = None) -> dict[str, Any]:
        det = self.store.detections.get(detection_id)
        if det is None:
            raise NotFoundError("detection", detection_id)
        det["classified_as"] = label or det["class"]
        det["classification_confidence"] = float(det.get("confidence", 0.5))
        self.store.detections.save(detection_id, det)
        return det

    def list(self, *, frame_id: str | None = None) -> list[dict[str, Any]]:
        items = self.store.detections.list_all()
        if frame_id:
            return [d for d in items if d.get("frame_id") == frame_id]
        return items


class TargetTracker:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def start_track(self, *, detection_id: str, label: str = "") -> dict[str, Any]:
        det = self.store.detections.get(detection_id)
        if det is None:
            raise NotFoundError("detection", detection_id)
        tid = f"trk_{uuid.uuid4().hex[:12]}"
        track = {
            "track_id": tid,
            "detection_id": detection_id,
            "label": label or det.get("class", "target"),
            "class": det.get("class"),
            "history": [{"bbox": det.get("bbox"), "at": _now()}],
            "status": "active",
            "created_at": _now(),
        }
        self.store.tracks.save(tid, track)
        return track

    def update(self, track_id: str, *, bbox: list[float]) -> dict[str, Any]:
        track = self.store.tracks.get(track_id)
        if track is None:
            raise NotFoundError("track", track_id)
        track["history"].append({"bbox": list(bbox), "at": _now()})
        track["updated_at"] = _now()
        self.store.tracks.save(track_id, track)
        return track

    def multi_object_track(self, detection_ids: list[str]) -> list[dict[str, Any]]:
        return [self.start_track(detection_id=did) for did in detection_ids]

    def list(self) -> list[dict[str, Any]]:
        return self.store.tracks.list_all()


class DetectionSuite:
    """Named detectors for required detection categories."""

    def __init__(self, detector: ObjectDetector | None = None, tracker: TargetTracker | None = None) -> None:
        self.detector = detector or ObjectDetector()
        self.tracker = tracker or TargetTracker()

    def vehicle_detection(self, frame_id: str, **kw: Any) -> dict[str, Any]:
        return self.detector.detect_class(frame_id=frame_id, class_name="vehicle", **kw)

    def person_detection(self, frame_id: str, **kw: Any) -> dict[str, Any]:
        return self.detector.detect_class(frame_id=frame_id, class_name="person", **kw)

    def aircraft_detection(self, frame_id: str, **kw: Any) -> dict[str, Any]:
        return self.detector.detect_class(frame_id=frame_id, class_name="aircraft", **kw)

    def ship_detection(self, frame_id: str, **kw: Any) -> dict[str, Any]:
        return self.detector.detect_class(frame_id=frame_id, class_name="ship", **kw)

    def building_detection(self, frame_id: str, **kw: Any) -> dict[str, Any]:
        return self.detector.detect_class(frame_id=frame_id, class_name="building", **kw)

    def road_detection(self, frame_id: str, **kw: Any) -> dict[str, Any]:
        return self.detector.detect_class(frame_id=frame_id, class_name="road", **kw)

    def tree_detection(self, frame_id: str, **kw: Any) -> dict[str, Any]:
        return self.detector.detect_class(frame_id=frame_id, class_name="tree", **kw)

    def power_line_detection(self, frame_id: str, **kw: Any) -> dict[str, Any]:
        return self.detector.detect_class(frame_id=frame_id, class_name="power_line", **kw)

    def landing_zone_detection(self, frame_id: str, **kw: Any) -> dict[str, Any]:
        return self.detector.detect_class(frame_id=frame_id, class_name="landing_zone", **kw)

    def obstacle_detection(self, frame_id: str, **kw: Any) -> dict[str, Any]:
        return self.detector.detect_class(frame_id=frame_id, class_name="obstacle", **kw)

    def status(self) -> dict[str, Any]:
        return {
            "object_detection": "1.0",
            "classes": list(DETECTION_CLASSES),
            "detection_count": self.detector.store.detections.count(),
            "track_count": self.tracker.store.tracks.count(),
            "capabilities": [
                "object_detector",
                "vehicle",
                "person",
                "aircraft",
                "ship",
                "building",
                "road",
                "tree",
                "power_line",
                "landing_zone",
                "obstacle",
                "target_tracking",
                "multi_object_tracking",
                "classification",
            ],
        }


detection_suite = DetectionSuite()
