# MigrationManager — configuration schema migrations with rollback.

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from platform_configuration.layer_exceptions import MigrationError
from platform_configuration.models import MigrationDirection, MigrationRecord

logger = logging.getLogger(__name__)

MigrationFn = Callable[[dict[str, Any]], dict[str, Any]]


class MigrationManager:
    """Automatic configuration migrations with history and rollback."""

    def __init__(self) -> None:
        self._migrations: dict[str, tuple[MigrationFn, MigrationFn]] = {}
        self._migration_targets: dict[str, str] = {}
        self._history: list[MigrationRecord] = []
        self._current_schema: str = "1.0"
        self._register_builtins()

    def _register_builtins(self) -> None:
        if "config_1_0_to_1_1" not in self._migrations:
            self.register(
                "config_1_0_to_1_1",
                up=lambda cfg: {**cfg, "deployment.last_version": cfg.get("deployment.last_version", "")},
                down=lambda cfg: {k: v for k, v in cfg.items() if k != "deployment.last_version"},
                version_to="1.1",
            )

    def reset(self) -> None:
        self._migrations.clear()
        self._migration_targets.clear()
        self._history.clear()
        self._current_schema = "1.0"
        self._register_builtins()

    @property
    def current_schema(self) -> str:
        return self._current_schema

    def register(
        self,
        migration_id: str,
        *,
        up: MigrationFn,
        down: MigrationFn,
        version_to: str,
    ) -> None:
        self._migrations[migration_id] = (up, down)
        self._migration_targets[migration_id] = version_to

    def apply(
        self,
        migration_id: str,
        config: dict[str, Any],
        *,
        direction: MigrationDirection = MigrationDirection.UP,
    ) -> tuple[dict[str, Any], MigrationRecord]:
        entry = self._migrations.get(migration_id)
        if entry is None:
            raise MigrationError(f"Unknown migration: {migration_id}", migration_id=migration_id)

        up_fn, down_fn = entry
        version_from = self._current_schema
        started = time.perf_counter()
        try:
            if direction == MigrationDirection.UP:
                migrated = up_fn(dict(config))
                version_to = self._migration_targets.get(migration_id, version_from)
                self._current_schema = version_to
            else:
                migrated = down_fn(dict(config))
                version_to = version_from
            success = True
            message = f"Migration {migration_id} {direction.value} applied"
        except Exception as exc:
            raise MigrationError(str(exc), migration_id=migration_id) from exc

        duration_ms = (time.perf_counter() - started) * 1000.0
        record = MigrationRecord(
            migration_id=migration_id,
            version_from=version_from,
            version_to=version_to if success else version_from,
            direction=direction,
            success=success,
            message=f"{message} ({duration_ms:.2f}ms)",
        )
        self._history.append(record)
        logger.info("migration_applied id=%s direction=%s", migration_id, direction.value)
        return migrated, record

    def migrate_auto(self, config: dict[str, Any], *, target_schema: str) -> dict[str, Any]:
        current = dict(config)
        for migration_id, version_to in sorted(self._migration_targets.items()):
            if self._current_schema >= target_schema:
                break
            current, _ = self.apply(migration_id, current, direction=MigrationDirection.UP)
            if version_to >= target_schema:
                break
        return current

    def rollback(self, migration_id: str, config: dict[str, Any]) -> tuple[dict[str, Any], MigrationRecord]:
        return self.apply(migration_id, config, direction=MigrationDirection.DOWN)

    def validate_migration(self, migration_id: str) -> bool:
        return migration_id in self._migrations

    def history(self) -> list[MigrationRecord]:
        return list(self._history)


migration_manager = MigrationManager()
