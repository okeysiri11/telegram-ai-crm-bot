"""Flight testing for production acceptance (Sprint 11.6)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError
from applications.drone_platform.shared.store import DroneStore, drone_store


TEST_TYPES = ("bench", "motor", "hover", "autonomous", "waypoint", "safety")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FlightTesting:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def run_test(
        self,
        *,
        serial_number: str,
        test_type: str,
        result: str = "pass",
        metrics: dict[str, Any] | None = None,
        notes: str = "",
    ) -> dict[str, Any]:
        tid = f"ft_{uuid.uuid4().hex[:12]}"
        item = {
            "test_id": tid,
            "serial_number": serial_number,
            "test_type": test_type,
            "result": result,
            "metrics": dict(metrics or {}),
            "notes": notes,
            "created_at": _now(),
        }
        self.store.flight_tests.save(tid, item)
        return item

    def mission_replay(self, *, test_id: str, waypoints: list[dict[str, Any]]) -> dict[str, Any]:
        test = self.store.flight_tests.get(test_id)
        if test is None:
            raise NotFoundError("flight_test", test_id)
        replay = {"test_id": test_id, "waypoints": waypoints, "step_count": len(waypoints), "replayed_at": _now()}
        test["replay"] = replay
        self.store.flight_tests.save(test_id, test)
        return replay

    def flight_report(self, *, serial_number: str) -> dict[str, Any]:
        tests = [t for t in self.store.flight_tests.list_all() if t.get("serial_number") == serial_number]
        return {
            "serial_number": serial_number,
            "test_count": len(tests),
            "passed": all(t.get("result") == "pass" for t in tests) if tests else False,
            "tests": tests,
            "generated_at": _now(),
        }

    def acceptance_protocol(self, *, serial_number: str) -> dict[str, Any]:
        report = self.flight_report(serial_number=serial_number)
        required = set(TEST_TYPES)
        done = {t.get("test_type") for t in report["tests"]}
        missing = sorted(required - done)
        accepted = report["passed"] and not missing
        return {
            "serial_number": serial_number,
            "accepted": accepted,
            "missing_tests": missing,
            "report": report,
            "protocol": "production_acceptance_v1",
        }

    def list(self) -> list[dict[str, Any]]:
        return self.store.flight_tests.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "flight_testing": "1.0",
            "test_types": list(TEST_TYPES),
            "test_count": self.store.flight_tests.count(),
            "capabilities": [
                "bench_tests",
                "motor_tests",
                "hover_tests",
                "autonomous_tests",
                "waypoint_missions",
                "safety_validation",
                "mission_replay",
                "flight_reports",
                "acceptance_protocol",
            ],
        }


flight_testing = FlightTesting()
