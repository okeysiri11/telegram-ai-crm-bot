"""Calibration station and reports (Sprint 11.6)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.store import DroneStore, drone_store


CALIBRATION_TYPES = (
    "accelerometer",
    "gyroscope",
    "compass",
    "gps",
    "barometer",
    "esc",
    "motor_direction",
    "radio",
    "failsafe",
    "telemetry",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CalibrationStation:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def calibrate(self, *, serial_number: str, calibration_type: str, result: str = "pass", details: dict[str, Any] | None = None) -> dict[str, Any]:
        ctype = calibration_type.lower().strip()
        if ctype not in CALIBRATION_TYPES:
            ctype = calibration_type  # allow custom with note
        rid = f"cal_{uuid.uuid4().hex[:12]}"
        report = {
            "report_id": rid,
            "serial_number": serial_number,
            "calibration_type": ctype,
            "result": result,
            "details": dict(details or {}),
            "created_at": _now(),
        }
        self.store.calibration_reports.save(rid, report)
        return report

    def run_suite(self, *, serial_number: str, types: list[str] | None = None) -> dict[str, Any]:
        selected = list(types or CALIBRATION_TYPES)
        reports = [self.calibrate(serial_number=serial_number, calibration_type=t) for t in selected]
        return {
            "serial_number": serial_number,
            "reports": reports,
            "passed": all(r["result"] == "pass" for r in reports),
            "count": len(reports),
        }

    def list(self, *, serial_number: str | None = None) -> list[dict[str, Any]]:
        items = self.store.calibration_reports.list_all()
        if serial_number:
            return [r for r in items if r.get("serial_number") == serial_number]
        return items

    def status(self) -> dict[str, Any]:
        return {
            "calibration": "1.0",
            "types": list(CALIBRATION_TYPES),
            "report_count": self.store.calibration_reports.count(),
            "automatic_reports": True,
        }


calibration_station = CalibrationStation()
