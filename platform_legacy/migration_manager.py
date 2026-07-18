# MigrationManager — tracks subsystem migration state (reversible).

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from platform_legacy.feature_flags import LEGACY_FLAG_KEYS, flag_enabled_for_subsystem, load_legacy_migration_flags

logger = logging.getLogger(__name__)


class MigrationState(str, enum.Enum):
    LEGACY = "LEGACY"
    MIGRATING = "MIGRATING"
    PLATFORM = "PLATFORM"
    REMOVED = "REMOVED"


# Default states — Platform Core preferred; legacy remains available in MIGRATING.
_DEFAULT_STATES: dict[str, MigrationState] = {
    "telegram": MigrationState.LEGACY,
    "users": MigrationState.MIGRATING,
    "requests": MigrationState.MIGRATING,
    "managers": MigrationState.MIGRATING,
    "notifications": MigrationState.MIGRATING,
    "workflow": MigrationState.MIGRATING,
    "ai": MigrationState.LEGACY,
    "repositories": MigrationState.LEGACY,
    "configuration": MigrationState.PLATFORM,
    "scheduler": MigrationState.LEGACY,
}


@dataclass(slots=True)
class SubsystemMigration:
    name: str
    state: MigrationState
    legacy_flag: str
    platform_module: str
    legacy_module: str
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "legacy_flag": self.legacy_flag,
            "platform_module": self.platform_module,
            "legacy_module": self.legacy_module,
            "updated_at": self.updated_at.isoformat(),
            "notes": self.notes,
        }


class MigrationManager:
    """Tracks migration state per subsystem; transitions are reversible."""

    def __init__(self) -> None:
        self._subsystems: dict[str, SubsystemMigration] = {}
        self._history: list[dict[str, Any]] = []
        self._bootstrap_defaults()

    def _bootstrap_defaults(self) -> None:
        platform_modules = {
            "telegram": "platform_sdk",
            "users": "platform_identity",
            "requests": "platform_sdk.verticals",
            "managers": "platform_operations",
            "notifications": "platform_sdk.notification_provider",
            "workflow": "platform_workflows",
            "ai": "platform_ai",
            "repositories": "repositories",
            "configuration": "platform_configuration",
            "scheduler": "platform_jobs",
        }
        legacy_modules = {
            "telegram": "handlers.py",
            "users": "services/pg_platform_permissions_engine",
            "requests": "services/pg_auto_client_request_engine",
            "managers": "services/pg_manager_delivery_engine",
            "notifications": "services/notification_service",
            "workflow": "platform_workflows/adapters/legacy_rules",
            "ai": "openrouter.py",
            "repositories": "database_legacy.py",
            "configuration": "database_legacy (config keys)",
            "scheduler": "services/pg_scheduler_engine",
        }
        for name, state in _DEFAULT_STATES.items():
            self._subsystems[name] = SubsystemMigration(
                name=name,
                state=state,
                legacy_flag=LEGACY_FLAG_KEYS.get(name, f"legacy_{name}"),
                platform_module=platform_modules.get(name, "platform_core"),
                legacy_module=legacy_modules.get(name, "legacy"),
            )

    def list_subsystems(self) -> list[str]:
        return sorted(self._subsystems)

    def get(self, subsystem: str) -> SubsystemMigration:
        if subsystem not in self._subsystems:
            raise KeyError(f"Unknown subsystem: {subsystem}")
        return self._subsystems[subsystem]

    def state(self, subsystem: str) -> MigrationState:
        return self.get(subsystem).state

    def set_state(
        self,
        subsystem: str,
        state: MigrationState | str,
        *,
        notes: str = "",
    ) -> SubsystemMigration:
        if isinstance(state, str):
            state = MigrationState(state.upper())
        record = self.get(subsystem)
        previous = record.state
        record.state = state
        record.updated_at = datetime.now(timezone.utc)
        record.notes = notes
        self._history.append(
            {
                "subsystem": subsystem,
                "from": previous.value,
                "to": state.value,
                "notes": notes,
                "at": record.updated_at.isoformat(),
            }
        )
        logger.info(
            "migration_state_change subsystem=%s from=%s to=%s",
            subsystem,
            previous.value,
            state.value,
        )
        return record

    def rollback(self, subsystem: str, *, notes: str = "rollback") -> SubsystemMigration:
        """Revert subsystem to LEGACY compatibility mode."""
        return self.set_state(subsystem, MigrationState.LEGACY, notes=notes)

    def should_route_to_legacy(self, subsystem: str) -> bool:
        """Decide execution path: platform (default) vs legacy compatibility."""
        state = self.state(subsystem)
        flags = load_legacy_migration_flags()

        if state == MigrationState.REMOVED:
            return False
        if state == MigrationState.LEGACY:
            return True
        if state == MigrationState.PLATFORM:
            return flag_enabled_for_subsystem(flags, subsystem)
        # MIGRATING — platform default; legacy flag enables compatibility path
        return flag_enabled_for_subsystem(flags, subsystem)

    def snapshot(self) -> dict[str, Any]:
        flags = load_legacy_migration_flags()
        subsystems = {
            name: {
                **rec.to_dict(),
                "route": "legacy" if self.should_route_to_legacy(name) else "platform",
                "legacy_flag_enabled": flag_enabled_for_subsystem(flags, name),
            }
            for name, rec in self._subsystems.items()
        }
        platform_count = sum(1 for s in subsystems.values() if s["route"] == "platform")
        total = len(subsystems) or 1
        return {
            "subsystems": subsystems,
            "history": self._history[-20:],
            "platform_routed_count": platform_count,
            "legacy_routed_count": total - platform_count,
            "platform_percent": round(platform_count / total * 100, 1),
        }


migration_manager = MigrationManager()
