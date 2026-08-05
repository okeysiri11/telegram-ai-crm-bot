# Security layer configuration — Sprint 30.0 (ConfigurationCenter only).

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
    allow_header_auth: bool = True
    require_tenant_filter: bool = True

    @classmethod
    def from_configuration(cls) -> SecurityConfig:
        from platform_configuration.configuration_center import configuration_center

        s = configuration_center.settings
        env_name = s.security.environment
        allow_anonymous = env_name in {"development", "dev", "test"}
        master = s.security.secret_master_key or (
            "platform-dev-key" if allow_anonymous else ""
        )
        return cls(
            allow_anonymous=allow_anonymous,
            secret_master_key=master,
            allow_header_auth=s.security.allow_header_auth,
            require_tenant_filter=s.security.require_tenant_filter,
            session_ttl_seconds=s.jwt.session_ttl_seconds,
        )


DEFAULT_SECURITY_CONFIG = SecurityConfig()


def reload_default_security_config() -> SecurityConfig:
    global DEFAULT_SECURITY_CONFIG
    DEFAULT_SECURITY_CONFIG = SecurityConfig.from_configuration()
    return DEFAULT_SECURITY_CONFIG
