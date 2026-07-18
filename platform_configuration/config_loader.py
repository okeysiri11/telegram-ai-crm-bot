# Configuration loader — seed defaults and bootstrap runtime snapshot.

from __future__ import annotations

import logging
import os
from typing import Any

from database.session import get_session
from platform_configuration.config_repository import ConfigRepository
from platform_configuration.config_schema import PLATFORM_CONFIG_SCHEMA

logger = logging.getLogger(__name__)


def schema_defaults() -> dict[str, Any]:
    return {spec.key: spec.default for spec in PLATFORM_CONFIG_SCHEMA.values()}


def env_overrides_for_seed() -> dict[str, Any]:
    """One-time migration: map legacy .env values into config center on first seed."""
    mapping: dict[str, Any] = {}

    def _bool(name: str) -> bool | None:
        raw = os.getenv(name, "").strip().lower()
        if not raw:
            return None
        return raw in {"1", "true", "yes", "on"}

    def _int(name: str) -> int | None:
        raw = os.getenv(name, "").strip()
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    def _float(name: str) -> float | None:
        raw = os.getenv(name, "").strip()
        if not raw:
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    def _str(name: str) -> str | None:
        raw = os.getenv(name, "").strip()
        return raw or None

    env_map: dict[str, tuple[str, str]] = {
        "general.environment": ("ENVIRONMENT", "str"),
        "general.log_level": ("LOG_LEVEL", "str"),
        "sla.assignment_sec": ("SLA_ASSIGNMENT_SEC", "int"),
        "sla.first_response_sec": ("SLA_FIRST_RESPONSE_SEC", "int"),
        "sla.close_sec": ("SLA_CLOSE_SEC", "int"),
        "escalation.owner_enabled": ("OWNER_ESCALATION_ENABLED", "bool"),
        "escalation.owner_delay_minutes": ("OWNER_ESCALATION_DELAY_MINUTES", "int"),
        "escalation.level2_after_sec": ("ESCALATION_LEVEL2_AFTER_SEC", "int"),
        "escalation.level3_after_sec": ("ESCALATION_LEVEL3_AFTER_SEC", "int"),
        "escalation.remind_sec": ("ESCALATION_REMIND_SEC", "int"),
        "escalation.repeat_sec": ("ESCALATION_REPEAT_SEC", "int"),
        "escalation.reassign_sec": ("ESCALATION_REASSIGN_SEC", "int"),
        "escalation.owner_sec": ("ESCALATION_OWNER_SEC", "int"),
        "sla.risk_window_minutes": ("SLA_RISK_MINUTES", "int"),
        "smart_assignment.mode": ("ASSIGNMENT_MODE", "str"),
        "managers.assignment_mode": ("MANAGER_ASSIGNMENT_MODE", "str"),
        "smart_assignment.load_weight": ("SMART_ASSIGNMENT_LOAD_WEIGHT", "float"),
        "smart_assignment.response_weight": ("SMART_ASSIGNMENT_RESPONSE_WEIGHT", "float"),
        "smart_assignment.completed_weight": ("SMART_ASSIGNMENT_COMPLETED_WEIGHT", "float"),
        "smart_assignment.priority_weight": ("SMART_ASSIGNMENT_PRIORITY_WEIGHT", "float"),
        "smart_assignment.specialization_weight": (
            "SMART_ASSIGNMENT_SPECIALIZATION_WEIGHT",
            "float",
        ),
    }

    for key, (env_name, vtype) in env_map.items():
        if vtype == "bool":
            value = _bool(env_name)
        elif vtype == "int":
            value = _int(env_name)
        elif vtype == "float":
            value = _float(env_name)
        else:
            value = _str(env_name)
        if value is not None:
            mapping[key] = value

    assignment_mode = _str("ASSIGNMENT_MODE")
    if assignment_mode and "smart_assignment.mode" not in mapping:
        mapping["smart_assignment.mode"] = assignment_mode.upper()

    return mapping


async def seed_platform_configuration(*, include_env: bool = True) -> dict[str, Any]:
    defaults = schema_defaults()
    if include_env:
        defaults.update(env_overrides_for_seed())

    async with get_session() as session:
        repo = ConfigRepository(session)
        seeded = await repo.seed_defaults(defaults)
        entries = await repo.list_entries()

    snapshot = {row.key: row.value for row in entries}
    logger.info(
        "platform_configuration_seeded seeded=%s total=%s",
        seeded,
        len(snapshot),
    )
    return {"seeded": seeded, "total": len(snapshot), "snapshot": snapshot}


async def load_runtime_snapshot() -> dict[str, Any]:
    async with get_session() as session:
        repo = ConfigRepository(session)
        entries = await repo.list_entries()
    return {row.key: row.value for row in entries}
