# ConfigurationProvider — hierarchical read/write facade for Sprint 5.4 layer.

from __future__ import annotations

from typing import Any

from platform_configuration.config_provider import ConfigProvider as _LegacyProvider
from platform_configuration.configuration_center import configuration_center
from platform_configuration.models import ConfigurationSnapshot


class ConfigurationProvider:
    """Centralized configuration access with runtime snapshot support."""

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        return _LegacyProvider.get(key, default)

    @staticmethod
    def get_section(section: str) -> dict[str, Any]:
        return _LegacyProvider.get_section(section)

    @staticmethod
    def set(key: str, value: Any) -> None:
        _LegacyProvider.update_key(key, value)

    @staticmethod
    def remove(key: str) -> None:
        _LegacyProvider.remove_key(key)

    @staticmethod
    def apply_snapshot(snapshot: ConfigurationSnapshot | dict[str, Any]) -> None:
        if isinstance(snapshot, ConfigurationSnapshot):
            _LegacyProvider.apply_snapshot(snapshot.values)
        else:
            _LegacyProvider.apply_snapshot(snapshot)

    @staticmethod
    def current_snapshot() -> ConfigurationSnapshot:
        return ConfigurationSnapshot(
            environment=configuration_center.settings.security.environment,
            values=_LegacyProvider.snapshot(),
        )

    @staticmethod
    def typed_settings() -> Any:
        return configuration_center.settings


configuration_provider = ConfigurationProvider()
