"""AI Flight Diagnostics — automatic anomaly detection (Sprint 11.3)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


DETECTION_RULES = (
    ("gps_glitch", lambda s: bool(s.get("gps_glitch")) or (s.get("gps_fix") is not None and int(s["gps_fix"]) < 5)),
    ("compass_problem", lambda s: bool(s.get("compass_error") or s.get("mag_error") or s.get("compass_inconsistent"))),
    ("ekf_error", lambda s: bool(s.get("ekf_error") or s.get("ekf_flags"))),
    ("vibration_issue", lambda s: float(s.get("vibe", 0) or 0) > 30 or bool(s.get("high_vibration"))),
    ("power_failure", lambda s: bool(s.get("power_failure") or s.get("brownout")) or (s.get("voltage") is not None and float(s["voltage"]) < 9.0)),
    ("motor_imbalance", lambda s: bool(s.get("motor_imbalance"))),
    ("esc_failure", lambda s: bool(s.get("esc_fault") or s.get("esc_failure"))),
    ("rc_signal_loss", lambda s: bool(s.get("rc_loss") or s.get("rc_failsafe"))),
    ("telemetry_loss", lambda s: bool(s.get("telemetry_loss") or s.get("link_loss"))),
    ("battery_degradation", lambda s: bool(s.get("battery_degraded")) or (s.get("battery") is not None and float(s["battery"]) < 15 and float(s.get("voltage", 16) or 16) < 14)),
    ("sensor_anomaly", lambda s: bool(s.get("imu_error") or s.get("baro_error") or s.get("sensor_anomaly"))),
    ("navigation_problem", lambda s: bool(s.get("nav_error") or s.get("pos_horiz_variance"))),
    ("mission_failure", lambda s: bool(s.get("mission_failure") or s.get("mission_error"))),
    ("landing_issue", lambda s: bool(s.get("landing_issue") or s.get("hard_landing"))),
    ("takeoff_issue", lambda s: bool(s.get("takeoff_issue") or s.get("takeoff_abort"))),
    ("crash_indicator", lambda s: bool(s.get("crash") or s.get("crash_detected") or s.get("impact"))),
)


class FlightDiagnosticsService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def detect(self, samples: list[dict[str, Any]], *, source: str = "telemetry") -> dict[str, Any]:
        detections: dict[str, list[dict[str, Any]]] = {name: [] for name, _ in DETECTION_RULES}
        for idx, sample in enumerate(samples):
            for name, rule in DETECTION_RULES:
                try:
                    if rule(sample):
                        detections[name].append({"index": idx, "at": sample.get("recorded_at"), "sample_keys": sorted(sample.keys())})
                except (TypeError, ValueError):
                    continue
        active = {k: v for k, v in detections.items() if v}
        severity = "critical" if active.get("crash_indicator") or active.get("power_failure") else "warning" if active else "ok"
        rid = f"diag_{uuid.uuid4().hex[:12]}"
        report = {
            "report_id": rid,
            "source": source,
            "sample_count": len(samples),
            "detections": active,
            "detection_counts": {k: len(v) for k, v in active.items()},
            "severity": severity,
            "detected_types": sorted(active.keys()),
            "created_at": _now(),
        }
        self.store.diagnostic_reports.save(rid, report)
        return report

    def get(self, report_id: str) -> dict[str, Any]:
        item = self.store.diagnostic_reports.get(report_id)
        if item is None:
            raise NotFoundError("diagnostic_report", report_id)
        return item

    def list(self) -> list[dict[str, Any]]:
        return self.store.diagnostic_reports.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "drone_diagnostics": "1.0",
            "supported_detections": [name for name, _ in DETECTION_RULES],
            "report_count": self.store.diagnostic_reports.count(),
        }


flight_diagnostics = FlightDiagnosticsService()
