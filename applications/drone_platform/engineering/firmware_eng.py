"""Firmware engineering helpers for the Engineering Suite (Sprint 11.5).

Bridges existing firmware intelligence without modifying Platform Core.
"""

from __future__ import annotations

from typing import Any

from applications.drone_platform.firmware.manager import FirmwareManager, firmware_manager
from applications.drone_platform.firmware.service import FirmwareService, firmware_service
from applications.drone_platform.shared.store import drone_store


class FirmwareEngineering:
    def __init__(
        self,
        service: FirmwareService | None = None,
        manager: FirmwareManager | None = None,
    ) -> None:
        self.service = service or firmware_service
        self.manager = manager or firmware_manager

    def firmware_builder(self, *, firmware_project_id: str, build_type: str = "release") -> dict[str, Any]:
        if build_type == "debug":
            return self.manager.builder.debug_build(firmware_project_id)
        if build_type == "clean":
            return self.manager.builder.clean_build(firmware_project_id)
        return self.manager.builder.release_build(firmware_project_id)

    def parameter_library(self, *, stack: str = "ardupilot") -> dict[str, Any]:
        return {"stack": stack, "templates": [t.to_dict() for t in self.service.list_templates(stack)]}

    def parameter_compare(self, *, left_id: str, right_id: str) -> dict[str, Any]:
        return self.service.compare_parameters(left_id, right_id)

    def configuration_templates(self, *, stack: str = "") -> list[dict[str, Any]]:
        return [t.to_dict() for t in self.service.list_templates(stack or None)]

    def firmware_diff(self, *, left_artifact_id: str, right_artifact_id: str) -> dict[str, Any]:
        return self.manager.comparator.compare_artifacts(left_artifact_id, right_artifact_id)

    def firmware_patch_generator(self, *, firmware_project_id: str, title: str, diff: str) -> dict[str, Any]:
        return self.manager.patches.create_patch(firmware_project_id=firmware_project_id, title=title, diff=diff)

    def mission_planner_profiles(self) -> list[dict[str, Any]]:
        return drone_store.mp_profiles.list_all()

    def ardupilot_profiles(self) -> dict[str, Any]:
        return {"stack": "ardupilot", "note": "Use /ardupilot vehicle profiles and parameter database"}

    def px4_profiles(self) -> dict[str, Any]:
        return {"stack": "px4", "note": "PX4 configuration profiles available via firmware templates"}

    def status(self) -> dict[str, Any]:
        return {
            "firmware_engineering": "1.0",
            "capabilities": [
                "firmware_builder",
                "parameter_library",
                "parameter_compare",
                "configuration_templates",
                "firmware_diff",
                "firmware_patch_generator",
                "mission_planner_profiles",
                "ardupilot_profiles",
                "px4_profiles",
            ],
        }


firmware_engineering = FirmwareEngineering()
