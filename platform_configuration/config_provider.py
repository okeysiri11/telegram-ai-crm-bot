# Configuration provider — runtime read facade (no .env in business logic).

from __future__ import annotations

import logging
from typing import Any

from platform_configuration.config_schema import (
    PLATFORM_CONFIG_SCHEMA,
    ConfigSection,
    default_for_key,
    section_for_key,
)

logger = logging.getLogger(__name__)

_runtime_snapshot: dict[str, Any] = {}


class ConfigProvider:
    @staticmethod
    def apply_snapshot(snapshot: dict[str, Any]) -> None:
        global _runtime_snapshot
        _runtime_snapshot = dict(snapshot)
        logger.info("config_provider_snapshot_applied keys=%s", len(_runtime_snapshot))

    @staticmethod
    def reset_snapshot() -> None:
        global _runtime_snapshot
        _runtime_snapshot = {}

    @staticmethod
    def snapshot() -> dict[str, Any]:
        return dict(_runtime_snapshot)

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        if key in _runtime_snapshot:
            return _runtime_snapshot[key]
        schema_default = default_for_key(key)
        if schema_default is not None:
            return schema_default
        return default

    @staticmethod
    def get_section(section: ConfigSection | str) -> dict[str, Any]:
        prefix = section.value if isinstance(section, ConfigSection) else section
        result: dict[str, Any] = {}
        for spec in PLATFORM_CONFIG_SCHEMA.values():
            if spec.section.value == prefix:
                result[spec.key] = ConfigProvider.get(spec.key)
        for key, value in _runtime_snapshot.items():
            if section_for_key(key) == prefix and key not in result:
                result[key] = value
        return result

    @staticmethod
    def is_feature_enabled(key: str, *, default: bool = False) -> bool:
        value = ConfigProvider.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in {"1", "true", "yes", "on"}
        return bool(value)

    @staticmethod
    def is_vertical_enabled(vertical_code: str) -> bool:
        code = vertical_code.lower()
        return ConfigProvider.is_feature_enabled(
            f"feature_flags.verticals.{code}",
            default=True,
        )

    @staticmethod
    def assignment_mode() -> str:
        mode = ConfigProvider.get("smart_assignment.mode", "SMART")
        return str(mode).upper()

    @staticmethod
    def manager_assignment_mode() -> str:
        mode = ConfigProvider.get("managers.assignment_mode", "ROUND_ROBIN")
        return str(mode).upper()

    @staticmethod
    def sla_settings() -> dict[str, int]:
        return {
            "assignment_sec": int(ConfigProvider.get("sla.assignment_sec", 900)),
            "first_response_sec": int(ConfigProvider.get("sla.first_response_sec", 1800)),
            "close_sec": int(ConfigProvider.get("sla.close_sec", 259200)),
        }

    @staticmethod
    def smart_assignment_weights() -> dict[str, float]:
        return {
            "load": float(ConfigProvider.get("smart_assignment.load_weight", 0.40)),
            "response": float(ConfigProvider.get("smart_assignment.response_weight", 0.25)),
            "completed": float(ConfigProvider.get("smart_assignment.completed_weight", 0.15)),
            "priority": float(ConfigProvider.get("smart_assignment.priority_weight", 0.10)),
            "specialization": float(
                ConfigProvider.get("smart_assignment.specialization_weight", 0.10)
            ),
        }

    @staticmethod
    def owner_escalation_settings() -> dict[str, Any]:
        return {
            "enabled": ConfigProvider.is_feature_enabled("escalation.owner_enabled", default=True),
            "delay_minutes": int(ConfigProvider.get("escalation.owner_delay_minutes", 240)),
        }

    @staticmethod
    def update_key(key: str, value: Any) -> None:
        _runtime_snapshot[key] = value

    @staticmethod
    def remove_key(key: str) -> None:
        _runtime_snapshot.pop(key, None)


config_provider = ConfigProvider()
