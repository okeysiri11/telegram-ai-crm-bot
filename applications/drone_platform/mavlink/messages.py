"""MAVLink Message Registry."""

from __future__ import annotations

from typing import Any


# Common MAVLink message definitions (dialect-agnostic registry).
MESSAGE_REGISTRY: dict[str, dict[str, Any]] = {
    "HEARTBEAT": {"id": 0, "category": "system", "fields": ["type", "autopilot", "base_mode", "system_status"]},
    "SYS_STATUS": {"id": 1, "category": "system", "fields": ["voltage_battery", "current_battery", "battery_remaining"]},
    "SYSTEM_TIME": {"id": 2, "category": "system", "fields": ["time_unix_usec", "time_boot_ms"]},
    "PING": {"id": 4, "category": "system", "fields": ["time_usec", "seq"]},
    "CHANGE_OPERATOR_CONTROL": {"id": 5, "category": "system", "fields": ["target_system", "control_request"]},
    "PARAM_VALUE": {"id": 22, "category": "parameter", "fields": ["param_id", "param_value", "param_type"]},
    "PARAM_SET": {"id": 23, "category": "parameter", "fields": ["param_id", "param_value", "param_type"]},
    "GPS_RAW_INT": {"id": 24, "category": "navigation", "fields": ["fix_sat", "lat", "lon", "alt", "eph", "epv"]},
    "RAW_IMU": {"id": 27, "category": "sensor", "fields": ["xacc", "yacc", "zacc", "xgyro", "ygyro", "zgyro"]},
    "SCALED_PRESSURE": {"id": 29, "category": "sensor", "fields": ["press_abs", "temperature"]},
    "ATTITUDE": {"id": 30, "category": "navigation", "fields": ["roll", "pitch", "yaw"]},
    "GLOBAL_POSITION_INT": {"id": 33, "category": "navigation", "fields": ["lat", "lon", "alt", "relative_alt", "vx", "vy", "vz"]},
    "RC_CHANNELS": {"id": 65, "category": "rc", "fields": ["chancount", "rssi"]},
    "VFR_HUD": {"id": 74, "category": "navigation", "fields": ["airspeed", "groundspeed", "heading", "throttle", "alt", "climb"]},
    "COMMAND_LONG": {"id": 76, "category": "command", "fields": ["command", "param1", "param2", "param3", "param4", "param5", "param6", "param7"]},
    "COMMAND_ACK": {"id": 77, "category": "command", "fields": ["command", "result"]},
    "MISSION_ITEM": {"id": 39, "category": "mission", "fields": ["seq", "command", "x", "y", "z"]},
    "MISSION_REQUEST": {"id": 40, "category": "mission", "fields": ["seq", "target_system"]},
    "MISSION_CURRENT": {"id": 42, "category": "mission", "fields": ["seq"]},
    "MISSION_COUNT": {"id": 44, "category": "mission", "fields": ["count"]},
    "MISSION_ITEM_REACHED": {"id": 46, "category": "mission", "fields": ["seq"]},
    "FILE_TRANSFER_PROTOCOL": {"id": 110, "category": "ftp", "fields": ["target_network", "target_system", "payload"]},
    "BATTERY_STATUS": {"id": 147, "category": "power", "fields": ["id", "battery_remaining", "current_battery", "voltages"]},
    "STATUSTEXT": {"id": 253, "category": "system", "fields": ["severity", "text"]},
}


class MessageRegistry:
    def list_messages(self, *, category: str | None = None) -> list[dict[str, Any]]:
        items = []
        for name, meta in MESSAGE_REGISTRY.items():
            if category and meta.get("category") != category:
                continue
            items.append({"name": name, **meta})
        return sorted(items, key=lambda m: m["id"])

    def get(self, name: str) -> dict[str, Any] | None:
        meta = MESSAGE_REGISTRY.get(name.upper())
        if meta is None:
            return None
        return {"name": name.upper(), **meta}

    def categories(self) -> list[str]:
        return sorted({m["category"] for m in MESSAGE_REGISTRY.values()})


message_registry = MessageRegistry()
