"""MAVLink Command Registry."""

from __future__ import annotations

from typing import Any


COMMAND_REGISTRY: dict[str, dict[str, Any]] = {
    "MAV_CMD_NAV_WAYPOINT": {"id": 16, "category": "navigation"},
    "MAV_CMD_NAV_LOITER_UNLIM": {"id": 17, "category": "navigation"},
    "MAV_CMD_NAV_RETURN_TO_LAUNCH": {"id": 20, "category": "navigation"},
    "MAV_CMD_NAV_LAND": {"id": 21, "category": "navigation"},
    "MAV_CMD_NAV_TAKEOFF": {"id": 22, "category": "navigation"},
    "MAV_CMD_DO_SET_MODE": {"id": 176, "category": "mode"},
    "MAV_CMD_DO_CHANGE_SPEED": {"id": 178, "category": "mission"},
    "MAV_CMD_DO_SET_HOME": {"id": 179, "category": "mission"},
    "MAV_CMD_DO_SET_RELAY": {"id": 181, "category": "actuator"},
    "MAV_CMD_DO_SET_SERVO": {"id": 183, "category": "actuator"},
    "MAV_CMD_DO_JUMP": {"id": 177, "category": "mission"},
    "MAV_CMD_CONDITION_DELAY": {"id": 112, "category": "condition"},
    "MAV_CMD_CONDITION_CHANGE_ALT": {"id": 113, "category": "condition"},
    "MAV_CMD_PREFLIGHT_CALIBRATION": {"id": 241, "category": "preflight"},
    "MAV_CMD_PREFLIGHT_STORAGE": {"id": 245, "category": "preflight"},
    "MAV_CMD_COMPONENT_ARM_DISARM": {"id": 400, "category": "safety"},
    "MAV_CMD_GET_HOME_POSITION": {"id": 410, "category": "navigation"},
    "MAV_CMD_REQUEST_MESSAGE": {"id": 512, "category": "system"},
}


class CommandRegistry:
    def list_commands(self, *, category: str | None = None) -> list[dict[str, Any]]:
        items = []
        for name, meta in COMMAND_REGISTRY.items():
            if category and meta.get("category") != category:
                continue
            items.append({"name": name, **meta})
        return sorted(items, key=lambda c: c["id"])

    def get(self, name: str) -> dict[str, Any] | None:
        key = name.upper()
        meta = COMMAND_REGISTRY.get(key)
        if meta is None:
            return None
        return {"name": key, **meta}


command_registry = CommandRegistry()
