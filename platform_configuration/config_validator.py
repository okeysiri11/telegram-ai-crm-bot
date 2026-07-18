# Configuration validator — schema-based validation.

from __future__ import annotations

from typing import Any

from platform_configuration.config_schema import PLATFORM_CONFIG_SCHEMA, ConfigKeySpec


class ConfigValidationError(ValueError):
    def __init__(self, message: str, *, key: str | None = None) -> None:
        super().__init__(message)
        self.key = key


class ConfigValidator:
    @staticmethod
    def validate_key(key: str) -> None:
        if not key or not key.strip():
            raise ConfigValidationError("Configuration key is required", key=key)
        if len(key) > 256:
            raise ConfigValidationError("Configuration key too long", key=key)

    @staticmethod
    def validate_value(key: str, value: Any) -> Any:
        ConfigValidator.validate_key(key)
        spec = PLATFORM_CONFIG_SCHEMA.get(key)
        if spec is None:
            return value
        return ConfigValidator._validate_against_spec(spec, value)

    @staticmethod
    def _validate_against_spec(spec: ConfigKeySpec, value: Any) -> Any:
        vtype = spec.value_type
        try:
            if vtype == "bool":
                if isinstance(value, bool):
                    coerced = value
                elif isinstance(value, str):
                    coerced = value.lower() in {"1", "true", "yes", "on"}
                else:
                    coerced = bool(value)
            elif vtype == "int":
                coerced = int(value)
                if spec.min_value is not None and coerced < spec.min_value:
                    raise ConfigValidationError(
                        f"{spec.key} must be >= {spec.min_value}",
                        key=spec.key,
                    )
                if spec.max_value is not None and coerced > spec.max_value:
                    raise ConfigValidationError(
                        f"{spec.key} must be <= {spec.max_value}",
                        key=spec.key,
                    )
            elif vtype == "float":
                coerced = float(value)
            elif vtype == "str":
                coerced = str(value)
            elif vtype == "json":
                coerced = value
            else:
                coerced = value
        except ConfigValidationError:
            raise
        except (TypeError, ValueError) as exc:
            raise ConfigValidationError(
                f"Invalid value type for {spec.key}: expected {vtype}",
                key=spec.key,
            ) from exc

        if spec.allowed_values is not None and coerced not in spec.allowed_values:
            raise ConfigValidationError(
                f"{spec.key} must be one of {spec.allowed_values}",
                key=spec.key,
            )
        return coerced

    @staticmethod
    def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
        validated: dict[str, Any] = {}
        errors: list[str] = []
        for key, value in payload.items():
            try:
                validated[key] = ConfigValidator.validate_value(key, value)
            except ConfigValidationError as exc:
                errors.append(str(exc))
        if errors:
            raise ConfigValidationError("; ".join(errors))
        return validated
