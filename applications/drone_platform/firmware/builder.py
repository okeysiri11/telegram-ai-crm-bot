from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.firmware.service import FirmwareService, firmware_service
from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store

BUILD_PROFILES = ("clean", "debug", "release", "custom")


class FirmwareBuilder:
    """Engineering firmware build orchestrator (simulated validation-friendly builds)."""

    def __init__(self, store: DroneStore | None = None, firmware: FirmwareService | None = None) -> None:
        self.store = store or drone_store
        self.firmware = firmware or firmware_service

    def build(
        self,
        *,
        firmware_project_id: str,
        profile: str = "release",
        custom_modules: list[str] | None = None,
        custom_drivers: list[str] | None = None,
        custom_sensors: list[str] | None = None,
        custom_mavlink: list[str] | None = None,
        validate_dependencies: bool = True,
    ) -> dict[str, Any]:
        project = self.firmware.get_project(firmware_project_id)
        profile_l = profile.lower()
        if profile_l not in BUILD_PROFILES:
            raise ValidationError(f"Unsupported build profile: {profile}")
        deps_ok = True
        dep_issues: list[str] = []
        if validate_dependencies and not project.stack:
            deps_ok = False
            dep_issues.append("missing_stack")
        bid = f"bld_{uuid.uuid4().hex[:12]}"
        record = {
            "build_id": bid,
            "firmware_project_id": firmware_project_id,
            "stack": project.stack,
            "profile": profile_l,
            "custom_modules": list(custom_modules or []),
            "custom_drivers": list(custom_drivers or []),
            "custom_sensors": list(custom_sensors or []),
            "custom_mavlink": list(custom_mavlink or []),
            "status": "succeeded" if deps_ok else "failed_validation",
            "validation": {"dependencies_ok": deps_ok, "issues": dep_issues},
            "artifact_hint": f"{project.stack}-{project.version or 'dev'}-{profile_l}.apj",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.firmware_builds.save(bid, record)
        return record

    def clean_build(self, firmware_project_id: str) -> dict[str, Any]:
        return self.build(firmware_project_id=firmware_project_id, profile="clean")

    def debug_build(self, firmware_project_id: str) -> dict[str, Any]:
        return self.build(firmware_project_id=firmware_project_id, profile="debug")

    def release_build(self, firmware_project_id: str) -> dict[str, Any]:
        return self.build(firmware_project_id=firmware_project_id, profile="release")

    def get(self, build_id: str) -> dict[str, Any]:
        item = self.store.firmware_builds.get(build_id)
        if item is None:
            raise NotFoundError("firmware_build", build_id)
        return item

    def list_builds(self, firmware_project_id: str | None = None) -> list[dict[str, Any]]:
        items = self.store.firmware_builds.list_all()
        if firmware_project_id:
            return [b for b in items if b.get("firmware_project_id") == firmware_project_id]
        return items


firmware_builder = FirmwareBuilder()
