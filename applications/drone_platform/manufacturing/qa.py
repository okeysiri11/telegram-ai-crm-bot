"""Quality assurance checklists and certification (Sprint 11.6)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError
from applications.drone_platform.shared.store import DroneStore, drone_store


QA_CHECKS = (
    "assembly_validation",
    "visual_inspection",
    "electrical_tests",
    "current_tests",
    "motor_tests",
    "sensor_validation",
    "communication_validation",
    "flight_readiness_validation",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class QualityAssurance:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def checklist(self) -> list[str]:
        return list(QA_CHECKS)

    def run_check(
        self,
        *,
        serial_number: str,
        check_type: str,
        passed: bool = True,
        notes: str = "",
        measurements: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        qid = f"qa_{uuid.uuid4().hex[:12]}"
        item = {
            "qa_id": qid,
            "serial_number": serial_number,
            "check_type": check_type,
            "passed": passed,
            "notes": notes,
            "measurements": dict(measurements or {}),
            "created_at": _now(),
        }
        self.store.qa_checks.save(qid, item)
        return item

    def run_full_checklist(self, *, serial_number: str, results: dict[str, bool] | None = None) -> dict[str, Any]:
        results = dict(results or {c: True for c in QA_CHECKS})
        checks = []
        for name in QA_CHECKS:
            checks.append(self.run_check(serial_number=serial_number, check_type=name, passed=bool(results.get(name, True))))
        all_passed = all(c["passed"] for c in checks)
        return {"serial_number": serial_number, "checks": checks, "passed": all_passed}

    def final_certification(self, *, serial_number: str, inspector: str = "qa") -> dict[str, Any]:
        prior = [c for c in self.store.qa_checks.list_all() if c.get("serial_number") == serial_number]
        passed = all(c.get("passed", False) for c in prior) if prior else False
        cert = {
            "certificate_id": f"cert_{uuid.uuid4().hex[:12]}",
            "serial_number": serial_number,
            "inspector": inspector,
            "certified": passed,
            "checks_reviewed": len(prior),
            "issued_at": _now(),
            "status": "certified" if passed else "rejected",
        }
        self.store.qa_checks.save(cert["certificate_id"], {"qa_id": cert["certificate_id"], "check_type": "final_certification", **cert})
        return cert

    def list(self, *, serial_number: str | None = None) -> list[dict[str, Any]]:
        items = self.store.qa_checks.list_all()
        if serial_number:
            return [c for c in items if c.get("serial_number") == serial_number]
        return items

    def status(self) -> dict[str, Any]:
        return {
            "quality_assurance": "1.0",
            "checklist": self.checklist(),
            "check_count": self.store.qa_checks.count(),
            "capabilities": [
                "quality_checklists",
                "assembly_validation",
                "visual_inspection",
                "electrical_tests",
                "current_tests",
                "motor_tests",
                "sensor_validation",
                "communication_validation",
                "flight_readiness_validation",
                "final_certification",
            ],
        }


quality_assurance = QualityAssurance()
