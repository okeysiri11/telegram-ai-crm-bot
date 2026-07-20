# EnvironmentManager — environment profiles and isolation.

from __future__ import annotations

import logging
import time
from typing import Any

from platform_configuration.configuration_loader import ConfigurationLoader, configuration_loader
from platform_configuration.layer_exceptions import EnvironmentNotFoundError
from platform_configuration.models import ConfigurationSnapshot, EnvironmentProfile

logger = logging.getLogger(__name__)

_BUILTIN = frozenset(p.value for p in EnvironmentProfile if p != EnvironmentProfile.CUSTOM)


class EnvironmentManager:
    """Manages development, testing, staging, production, and custom profiles."""

    def __init__(self, *, loader: ConfigurationLoader | None = None) -> None:
        self._loader = loader or configuration_loader
        self._active: str = EnvironmentProfile.DEVELOPMENT.value
        self._snapshots: dict[str, ConfigurationSnapshot] = {}
        self._status: dict[str, dict[str, Any]] = {}

    def reset(self) -> None:
        self._active = EnvironmentProfile.DEVELOPMENT.value
        self._snapshots.clear()
        self._status.clear()

    @property
    def active_environment(self) -> str:
        return self._active

    def list_profiles(self) -> list[str]:
        custom = [p for p in self._loader.registered_profiles() if p not in _BUILTIN]
        return sorted(_BUILTIN | set(custom))

    def activate(self, name: str, *, overrides: dict[str, Any] | None = None) -> ConfigurationSnapshot:
        normalized = name.strip().lower()
        snapshot = self._loader.load(environment=normalized, overrides=overrides)
        self._snapshots[normalized] = snapshot
        self._active = normalized
        self._status[normalized] = {
            "status": "active",
            "activated_at": time.time(),
            "isolated": normalized not in {EnvironmentProfile.DEVELOPMENT.value},
        }
        logger.info("environment_activated name=%s keys=%s", normalized, len(snapshot.values))
        return snapshot

    def get_snapshot(self, name: str | None = None) -> ConfigurationSnapshot:
        env = (name or self._active).strip().lower()
        snapshot = self._snapshots.get(env)
        if snapshot is None:
            raise EnvironmentNotFoundError(env)
        return snapshot

    def register_custom(self, name: str, overrides: dict[str, Any]) -> None:
        normalized = name.strip().lower()
        self._loader.register_profile(normalized, overrides)
        self._status[normalized] = {"status": "registered", "isolated": True}

    def environment_status(self) -> dict[str, Any]:
        return {
            "active": self._active,
            "profiles": self.list_profiles(),
            "status": dict(self._status),
        }

    def is_isolated(self, name: str | None = None) -> bool:
        env = (name or self._active).strip().lower()
        if env == EnvironmentProfile.DEVELOPMENT.value:
            return False
        return self._status.get(env, {}).get("isolated", True)


environment_manager = EnvironmentManager()
