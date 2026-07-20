# ConfigurationLoader — hierarchical configuration loading with inheritance.

from __future__ import annotations

import logging
import time
from typing import Any

from platform_configuration.config_schema import PLATFORM_CONFIG_SCHEMA
from platform_configuration.configuration_validator import ConfigurationValidator, configuration_validator
from platform_configuration.layer_config import DEFAULT_LAYER_CONFIG, ConfigurationLayerConfig
from platform_configuration.layer_exceptions import ConfigurationValidationError
from platform_configuration.models import ConfigurationSnapshot, EnvironmentProfile

logger = logging.getLogger(__name__)

_BASE_DEFAULTS: dict[str, Any] = {spec.key: spec.default for spec in PLATFORM_CONFIG_SCHEMA.values()}

_PROFILE_OVERRIDES: dict[str, dict[str, Any]] = {
    EnvironmentProfile.DEVELOPMENT.value: {
        "general.environment": "development",
        "general.log_level": "DEBUG",
        "feature_flags.experimental.ai": True,
    },
    EnvironmentProfile.TESTING.value: {
        "general.environment": "testing",
        "general.log_level": "INFO",
        "feature_flags.experimental.ai": True,
    },
    EnvironmentProfile.STAGING.value: {
        "general.environment": "staging",
        "general.log_level": "INFO",
        "feature_flags.experimental.ai": False,
    },
    EnvironmentProfile.PRODUCTION.value: {
        "general.environment": "production",
        "general.log_level": "WARNING",
        "feature_flags.experimental.ai": False,
    },
}


class ConfigurationLoader:
    """Loads hierarchical configuration with inheritance and overrides."""

    def __init__(self, *, config: ConfigurationLayerConfig | None = None) -> None:
        self._config = config or DEFAULT_LAYER_CONFIG
        self._custom_profiles: dict[str, dict[str, Any]] = {}
        self._last_load_ms: float = 0.0

    def reset(self) -> None:
        self._custom_profiles.clear()
        self._last_load_ms = 0.0

    @property
    def last_load_ms(self) -> float:
        return self._last_load_ms

    def register_profile(self, name: str, overrides: dict[str, Any]) -> None:
        normalized = configuration_validator.validate_environment_name(name)
        self._custom_profiles[normalized] = dict(overrides)

    def _merge_layers(self, *layers: dict[str, Any]) -> dict[str, Any]:
        merged = dict(_BASE_DEFAULTS)
        for layer in layers:
            merged.update(layer)
        return merged

    def registered_profiles(self) -> list[str]:
        return sorted(self._custom_profiles.keys())

    def load(
        self,
        *,
        environment: str = "development",
        overrides: dict[str, Any] | None = None,
        encrypted_keys: set[str] | None = None,
    ) -> ConfigurationSnapshot:
        started = time.perf_counter()
        env = configuration_validator.validate_environment_name(environment)
        layers: list[str] = ["base_defaults"]
        layer_values = [dict(_BASE_DEFAULTS)]

        profile = _PROFILE_OVERRIDES.get(env)
        if profile:
            layers.append(f"profile:{env}")
            layer_values.append(profile)

        custom = self._custom_profiles.get(env)
        if custom:
            layers.append(f"custom:{env}")
            layer_values.append(custom)

        if overrides:
            layers.append("runtime_overrides")
            layer_values.append(overrides)

        merged = self._merge_layers(*layer_values)
        try:
            validated = configuration_validator.validate_payload(merged)
        except ConfigurationValidationError:
            raise

        self._last_load_ms = (time.perf_counter() - started) * 1000.0
        snapshot = ConfigurationSnapshot(
            environment=env,
            values=validated,
            encrypted_keys=encrypted_keys or set(),
            schema_version=self._config.schema_version,
            source_layers=layers,
        )
        logger.info(
            "configuration_loaded environment=%s keys=%s duration_ms=%.2f",
            env,
            len(validated),
            self._last_load_ms,
        )
        return snapshot

    def load_encrypted_values(
        self,
        snapshot: ConfigurationSnapshot,
        *,
        decrypt_fn: Any | None = None,
    ) -> ConfigurationSnapshot:
        if not snapshot.encrypted_keys:
            return snapshot
        decrypt = decrypt_fn or self._default_decrypt
        resolved = dict(snapshot.values)
        for key in snapshot.encrypted_keys:
            if key in resolved:
                resolved[key] = decrypt(str(resolved[key]))
        snapshot.values = resolved
        return snapshot

    @staticmethod
    def _default_decrypt(ciphertext: str) -> str:
        try:
            from platform_security.secrets import secret_manager

            return secret_manager.retrieve(ciphertext)
        except Exception:
            logger.debug("decrypt fallback for encrypted config value")
            return ciphertext


configuration_loader = ConfigurationLoader()
