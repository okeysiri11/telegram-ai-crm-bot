# Configuration schema — hierarchical sections, defaults, and validation rules.

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class ConfigSection(str, enum.Enum):
    GENERAL = "general"
    VERTICALS = "verticals"
    MANAGERS = "managers"
    WORKFLOW = "workflow"
    SLA = "sla"
    ESCALATION = "escalation"
    SMART_ASSIGNMENT = "smart_assignment"
    NOTIFICATIONS = "notifications"
    AI = "ai"
    PLUGINS = "plugins"
    INTEGRATIONS = "integrations"
    SECURITY = "security"
    FEATURE_FLAGS = "feature_flags"


@dataclass(frozen=True)
class ConfigKeySpec:
    key: str
    section: ConfigSection
    value_type: str
    default: Any
    description: str = ""
    min_value: float | None = None
    max_value: float | None = None
    allowed_values: tuple[Any, ...] | None = None


def _spec(
    section: ConfigSection,
    name: str,
    value_type: str,
    default: Any,
    *,
    description: str = "",
    **kwargs: Any,
) -> ConfigKeySpec:
    return ConfigKeySpec(
        key=f"{section.value}.{name}",
        section=section,
        value_type=value_type,
        default=default,
        description=description,
        **kwargs,
    )


PLATFORM_CONFIG_SCHEMA: dict[str, ConfigKeySpec] = {
    spec.key: spec
    for spec in (
        _spec(ConfigSection.GENERAL, "environment", "str", "development"),
        _spec(ConfigSection.GENERAL, "log_level", "str", "INFO"),
        _spec(ConfigSection.SLA, "assignment_sec", "int", 900, min_value=60),
        _spec(ConfigSection.SLA, "first_response_sec", "int", 1800, min_value=60),
        _spec(ConfigSection.SLA, "close_sec", "int", 259200, min_value=3600),
        _spec(ConfigSection.SLA, "risk_window_minutes", "int", 30, min_value=1),
        _spec(ConfigSection.ESCALATION, "owner_enabled", "bool", True),
        _spec(ConfigSection.ESCALATION, "owner_delay_minutes", "int", 240, min_value=1),
        _spec(ConfigSection.ESCALATION, "level2_after_sec", "int", 900, min_value=60),
        _spec(ConfigSection.ESCALATION, "level3_after_sec", "int", 900, min_value=60),
        _spec(ConfigSection.ESCALATION, "remind_sec", "int", 300, min_value=60),
        _spec(ConfigSection.ESCALATION, "repeat_sec", "int", 900, min_value=60),
        _spec(ConfigSection.ESCALATION, "reassign_sec", "int", 1800, min_value=60),
        _spec(ConfigSection.ESCALATION, "owner_sec", "int", 3600, min_value=60),
        _spec(ConfigSection.SMART_ASSIGNMENT, "mode", "str", "SMART", allowed_values=("SMART", "ROUND_ROBIN", "LEAST_LOADED", "PRIORITY", "WEIGHTED")),
        _spec(ConfigSection.SMART_ASSIGNMENT, "load_weight", "float", 0.40),
        _spec(ConfigSection.SMART_ASSIGNMENT, "response_weight", "float", 0.25),
        _spec(ConfigSection.SMART_ASSIGNMENT, "completed_weight", "float", 0.15),
        _spec(ConfigSection.SMART_ASSIGNMENT, "priority_weight", "float", 0.10),
        _spec(ConfigSection.SMART_ASSIGNMENT, "specialization_weight", "float", 0.10),
        _spec(ConfigSection.MANAGERS, "assignment_mode", "str", "ROUND_ROBIN"),
        _spec(ConfigSection.WORKFLOW, "definitions_auto_reload", "bool", False),
        _spec(ConfigSection.NOTIFICATIONS, "enabled", "bool", True),
        _spec(ConfigSection.NOTIFICATIONS, "owner_notifications", "bool", True),
        _spec(ConfigSection.AI, "openrouter_enabled", "bool", False),
        _spec(ConfigSection.INTEGRATIONS, "webhooks_enabled", "bool", True),
        _spec(ConfigSection.SECURITY, "config_read_permission", "str", "platform.config.read"),
        _spec(ConfigSection.SECURITY, "config_write_permission", "str", "platform.config.write"),
        _spec(ConfigSection.FEATURE_FLAGS, "verticals.auto", "bool", True),
        _spec(ConfigSection.FEATURE_FLAGS, "verticals.agro", "bool", True),
        _spec(ConfigSection.FEATURE_FLAGS, "verticals.realty", "bool", True),
        _spec(ConfigSection.FEATURE_FLAGS, "verticals.legal", "bool", True),
        _spec(ConfigSection.FEATURE_FLAGS, "verticals.logistics", "bool", True),
        _spec(ConfigSection.FEATURE_FLAGS, "verticals.crm", "bool", True),
        _spec(ConfigSection.FEATURE_FLAGS, "plugins.enabled", "bool", True),
        _spec(ConfigSection.FEATURE_FLAGS, "ai.providers", "bool", False),
        _spec(ConfigSection.FEATURE_FLAGS, "notifications.enabled", "bool", True),
        _spec(ConfigSection.FEATURE_FLAGS, "assignment.smart", "bool", True),
        _spec(ConfigSection.FEATURE_FLAGS, "assignment.round_robin", "bool", True),
        _spec(ConfigSection.FEATURE_FLAGS, "assignment.least_loaded", "bool", True),
        _spec(ConfigSection.FEATURE_FLAGS, "assignment.priority", "bool", True),
        _spec(ConfigSection.FEATURE_FLAGS, "assignment.weighted", "bool", True),
        _spec(ConfigSection.FEATURE_FLAGS, "experimental.workflow_v2", "bool", False),
        _spec(ConfigSection.FEATURE_FLAGS, "plugins.hot_reload", "bool", False),
        _spec(ConfigSection.FEATURE_FLAGS, "ai.memory_cache", "bool", True),
        _spec(ConfigSection.FEATURE_FLAGS, "experimental.ai", "bool", False),
        _spec(ConfigSection.FEATURE_FLAGS, "ai.multi_provider", "bool", False),
    )
}


def section_for_key(key: str) -> str:
    if key in PLATFORM_CONFIG_SCHEMA:
        return PLATFORM_CONFIG_SCHEMA[key].section.value
    if "." in key:
        return key.split(".", 1)[0]
    return ConfigSection.GENERAL.value


def default_for_key(key: str) -> Any:
    spec = PLATFORM_CONFIG_SCHEMA.get(key)
    return spec.default if spec else None
