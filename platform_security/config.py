# Security layer configuration.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SecurityConfig:
    allow_anonymous: bool = False
    jwt_enabled: bool = True
    api_key_enabled: bool = True
    oauth_enabled: bool = False
    service_account_enabled: bool = True
    secret_master_key: str = "platform-dev-key"
    audit_retention_limit: int = 10000
    session_ttl_seconds: int = 3600

    @classmethod
    def from_configuration(cls) -> SecurityConfig:
        try:
            from platform_configuration.configuration_center import configuration_center

            env_name = configuration_center.settings.security.environment
            allow_anonymous = env_name in {"development", "dev", "test"}
            return cls(allow_anonymous=allow_anonymous)
        except Exception:
            return cls()


DEFAULT_SECURITY_CONFIG = SecurityConfig()
