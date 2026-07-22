"""Programming station — flashing, params, serial/QR registration (Sprint 11.6)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProgrammingStation:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def flash_firmware(
        self,
        *,
        serial_number: str,
        firmware_version: str,
        stack: str = "ardupilot",
        artifact_id: str = "",
    ) -> dict[str, Any]:
        sid = f"prg_{uuid.uuid4().hex[:12]}"
        session = {
            "session_id": sid,
            "serial_number": serial_number,
            "action": "flash",
            "stack": stack,
            "firmware_version": firmware_version,
            "artifact_id": artifact_id,
            "status": "flashed",
            "created_at": _now(),
        }
        self.store.programming_sessions.save(sid, session)
        return session

    def upload_parameters(self, *, serial_number: str, parameters: dict[str, Any], profile: str = "default") -> dict[str, Any]:
        sid = f"prg_{uuid.uuid4().hex[:12]}"
        session = {
            "session_id": sid,
            "serial_number": serial_number,
            "action": "param_upload",
            "profile": profile,
            "parameter_count": len(parameters),
            "parameters": dict(parameters),
            "status": "uploaded",
            "created_at": _now(),
        }
        self.store.programming_sessions.save(sid, session)
        return session

    def configuration_profiles(self) -> list[dict[str, Any]]:
        return [
            {"name": "default", "stack": "ardupilot"},
            {"name": "survey", "stack": "ardupilot"},
            {"name": "px4_default", "stack": "px4"},
        ]

    def bootloader_manager(self, *, serial_number: str, action: str = "verify") -> dict[str, Any]:
        return {"serial_number": serial_number, "action": action, "bootloader": "ok", "status": "ready"}

    def version_verification(self, *, serial_number: str, expected_version: str, actual_version: str) -> dict[str, Any]:
        return {
            "serial_number": serial_number,
            "expected_version": expected_version,
            "actual_version": actual_version,
            "valid": expected_version == actual_version,
        }

    def automatic_validation(self, *, serial_number: str, checks: dict[str, bool] | None = None) -> dict[str, Any]:
        checks = dict(checks or {"firmware": True, "parameters": True, "sensors": True})
        return {"serial_number": serial_number, "checks": checks, "passed": all(checks.values())}

    def assign_serial_number(self, *, prefix: str = "UAV") -> dict[str, Any]:
        sn = f"{prefix}-{uuid.uuid4().hex[:10].upper()}"
        return {"serial_number": sn, "assigned_at": _now()}

    def qr_code_generator(self, *, serial_number: str) -> dict[str, Any]:
        payload = f"drone:{serial_number}"
        digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return {"serial_number": serial_number, "qr_payload": payload, "qr_token": digest, "format": "qr"}

    def device_registration(self, *, serial_number: str, model: str, order_id: str = "") -> dict[str, Any]:
        rid = f"dev_{uuid.uuid4().hex[:12]}"
        record = {
            "device_id": rid,
            "serial_number": serial_number,
            "model": model,
            "order_id": order_id,
            "registered_at": _now(),
            "status": "registered",
        }
        self.store.programming_sessions.save(rid, {"session_id": rid, "action": "register", **record})
        return record

    def list(self) -> list[dict[str, Any]]:
        return self.store.programming_sessions.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "programming_station": "1.0",
            "sessions": self.store.programming_sessions.count(),
            "capabilities": [
                "firmware_flashing",
                "parameter_upload",
                "configuration_profiles",
                "bootloader_manager",
                "version_verification",
                "automatic_validation",
                "serial_number_assignment",
                "qr_code_generator",
                "device_registration",
            ],
        }


programming_station = ProgrammingStation()
