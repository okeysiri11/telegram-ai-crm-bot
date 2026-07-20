# ConfigurationValidator — schema validation facade for Sprint 5.4 layer.

from __future__ import annotations

from typing import Any

from platform_configuration.config_validator import ConfigValidator as _LegacyValidator
from platform_configuration.layer_exceptions import ConfigurationValidationError
from platform_configuration.models import ConfigurationSnapshot


class ConfigurationValidator:
    """Validates configuration keys, payloads, and snapshots."""

    @staticmethod
    def validate_key(key: str) -> None:
        try:
            _LegacyValidator.validate_key(key)
        except Exception as exc:
            raise ConfigurationValidationError(str(exc), key=key) from exc

    @staticmethod
    def validate_value(key: str, value: Any) -> Any:
        try:
            return _LegacyValidator.validate_value(key, value)
        except Exception as exc:
            raise ConfigurationValidationError(str(exc), key=key) from exc

    @staticmethod
    def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return _LegacyValidator.validate_payload(payload)
        except Exception as exc:
            raise ConfigurationValidationError(str(exc)) from exc

    @staticmethod
    def validate_snapshot(snapshot: ConfigurationSnapshot) -> ConfigurationSnapshot:
        validated = ConfigurationValidator.validate_payload(snapshot.values)
        snapshot.values = validated
        return snapshot

    @staticmethod
    def validate_environment_name(name: str) -> str:
        normalized = (name or "").strip().lower()
        if not normalized:
            raise ConfigurationValidationError("Environment name is required")
        if len(normalized) > 64:
            raise ConfigurationValidationError("Environment name too long")
        return normalized


configuration_validator = ConfigurationValidator()
