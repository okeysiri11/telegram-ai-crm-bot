# Legacy migration feature flags — switch execution path without code changes.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Subsystem → env / config key for compatibility-mode (legacy path).
LEGACY_FLAG_KEYS: dict[str, str] = {
    "telegram": "legacy_handlers",
    "users": "legacy_users",
    "requests": "legacy_requests",
    "managers": "legacy_managers",
    "notifications": "legacy_notifications",
    "workflow": "legacy_workflow",
    "ai": "legacy_ai",
    "scheduler": "legacy_scheduler",
    "repositories": "legacy_database",
    "configuration": "legacy_configuration",
}


def flag_enabled_for_subsystem(flags: Any, subsystem: str) -> bool:
    key = LEGACY_FLAG_KEYS.get(subsystem)
    if not key:
        return False
    return bool(getattr(flags, key, False))


@dataclass(frozen=True, slots=True)
class LegacyMigrationFlags:
    """When True, route subsystem through legacy compatibility path."""

    legacy_users: bool = False
    legacy_requests: bool = False
    legacy_notifications: bool = False
    legacy_ai: bool = False
    legacy_handlers: bool = False
    legacy_scheduler: bool = False
    legacy_database: bool = False
    legacy_managers: bool = False
    legacy_workflow: bool = False
    legacy_configuration: bool = False

    def is_enabled(self, flag_name: str) -> bool:
        return bool(getattr(self, flag_name, False))

    def for_subsystem(self, subsystem: str) -> bool:
        return flag_enabled_for_subsystem(self, subsystem)

    def to_dict(self) -> dict[str, bool]:
        return {
            "legacy_users": self.legacy_users,
            "legacy_requests": self.legacy_requests,
            "legacy_notifications": self.legacy_notifications,
            "legacy_ai": self.legacy_ai,
            "legacy_handlers": self.legacy_handlers,
            "legacy_scheduler": self.legacy_scheduler,
            "legacy_database": self.legacy_database,
            "legacy_managers": self.legacy_managers,
            "legacy_workflow": self.legacy_workflow,
            "legacy_configuration": self.legacy_configuration,
        }


def _env_bool(name: str, default: bool) -> bool:
    try:
        from platform_configuration.env_source import getenv_bool

        return getenv_bool(name, default)
    except Exception:
        return default


def _config_bool(key: str, default: bool) -> bool:
    try:
        from platform_configuration.config_provider import config_provider

        value = config_provider.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in {"1", "true", "yes", "on"}
        return bool(value)
    except Exception:
        return default


def load_legacy_migration_flags() -> LegacyMigrationFlags:
    """Load flags from ConfigurationCenter snapshot with env fallback."""
    defaults = LegacyMigrationFlags()
    try:
        from platform_configuration.configuration_center import configuration_center

        center_flags = configuration_center.settings.legacy_migration
        return LegacyMigrationFlags(
            legacy_users=center_flags.legacy_users,
            legacy_requests=center_flags.legacy_requests,
            legacy_notifications=center_flags.legacy_notifications,
            legacy_ai=center_flags.legacy_ai,
            legacy_handlers=center_flags.legacy_handlers,
            legacy_scheduler=center_flags.legacy_scheduler,
            legacy_database=center_flags.legacy_database,
            legacy_managers=center_flags.legacy_managers,
            legacy_workflow=center_flags.legacy_workflow,
            legacy_configuration=center_flags.legacy_configuration,
        )
    except Exception:
        pass

    return LegacyMigrationFlags(
        legacy_users=_config_bool("feature_flags.legacy.users", _env_bool("LEGACY_USERS", defaults.legacy_users)),
        legacy_requests=_config_bool(
            "feature_flags.legacy.requests",
            _env_bool("LEGACY_REQUESTS", defaults.legacy_requests),
        ),
        legacy_notifications=_config_bool(
            "feature_flags.legacy.notifications",
            _env_bool("LEGACY_NOTIFICATIONS", defaults.legacy_notifications),
        ),
        legacy_ai=_config_bool("feature_flags.legacy.ai", _env_bool("LEGACY_AI", defaults.legacy_ai)),
        legacy_handlers=_config_bool(
            "feature_flags.legacy.handlers",
            _env_bool("LEGACY_HANDLERS", defaults.legacy_handlers),
        ),
        legacy_scheduler=_config_bool(
            "feature_flags.legacy.scheduler",
            _env_bool("LEGACY_SCHEDULER", defaults.legacy_scheduler),
        ),
        legacy_database=_config_bool(
            "feature_flags.legacy.database",
            _env_bool("LEGACY_DATABASE", defaults.legacy_database),
        ),
        legacy_managers=_config_bool(
            "feature_flags.legacy.managers",
            _env_bool("LEGACY_MANAGERS", defaults.legacy_managers),
        ),
        legacy_workflow=_config_bool(
            "feature_flags.legacy.workflow",
            _env_bool("LEGACY_WORKFLOW", defaults.legacy_workflow),
        ),
        legacy_configuration=_config_bool(
            "feature_flags.legacy.configuration",
            _env_bool("LEGACY_CONFIGURATION", defaults.legacy_configuration),
        ),
    )


legacy_migration_flags = load_legacy_migration_flags()


def reload_legacy_migration_flags() -> LegacyMigrationFlags:
    global legacy_migration_flags
    legacy_migration_flags = load_legacy_migration_flags()
    return legacy_migration_flags
