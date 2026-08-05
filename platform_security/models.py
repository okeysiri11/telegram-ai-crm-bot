"""Security hardening constants + core types — Sprint 21.4 / 30.0."""

from __future__ import annotations

import fnmatch
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

AUTH_METHODS = (
    "oauth2",
    "oidc",
    "google",
    "jwt",
    "jwt_rotation",
    "refresh_token",
    "service_account",
    "api_key",
    "mfa",
    "trusted_device",
    "session_manager",
)

ABAC_ATTRIBUTES = (
    "organization",
    "department",
    "project",
    "owner",
    "secrecy_level",
    "geo_zone",
    "operation_type",
)

ZERO_TRUST_CHECKS = (
    "user",
    "device",
    "token",
    "ip",
    "context",
    "risk_level",
    "security_policy",
)

SECRET_KINDS = (
    "api_key",
    "jwt_secret",
    "encryption_key",
    "database_password",
    "cloud_credential",
    "ai_provider_key",
)

ENCRYPTION_ALGORITHMS = (
    "tls_1_3",
    "aes_256",
    "rsa",
    "ed25519",
    "hashing",
    "digital_signature",
)

AUDIT_ACTIONS = (
    "user_login",
    "ai_action",
    "data_change",
    "role_change",
    "workflow_start",
    "api_access",
    "admin_action",
)

MONITORING_SIGNALS = (
    "password_spray",
    "anomalous_request",
    "suspicious_token",
    "unusual_activity",
    "mass_delete",
    "data_exfiltration",
)

PROTECTION_CONTROLS = (
    "rate_limit",
    "burst_control",
    "api_quota",
    "anti_bruteforce",
    "anti_ddos",
    "request_validation",
)

COMPLIANCE_FRAMEWORKS = (
    "gdpr",
    "iso_27001",
    "soc_2",
    "nist_csf",
    "owasp_asvs",
)

SECURITY_TESTS = (
    "dependency_scan",
    "secret_scan",
    "sast",
    "dast",
    "container_scan",
    "license_audit",
    "security_regression",
)

INTEGRATION_TARGETS = (
    "api_platform",
    "ai_agents",
    "workflow",
    "event_bus",
    "data_fabric",
    "enterprise_hub",
    "vertical_modules",
)


class AuthMethodType(str, Enum):
    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH = "oauth"
    SERVICE_ACCOUNT = "service_account"
    ANONYMOUS = "anonymous"
    TELEGRAM = "telegram"


class PermissionScope(str, Enum):
    CAPABILITY = "capability"
    AGENT = "agent"
    TOOL = "tool"
    WORKFLOW = "workflow"
    REPOSITORY = "repository"
    SYSTEM = "system"


class SecurityRole(str, Enum):
    OWNER = "owner"
    ADMINISTRATOR = "administrator"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    MANAGER = "manager"
    VIEWER = "viewer"
    AI_AGENT = "ai_agent"
    SERVICE = "service"
    AUDITOR = "auditor"


class AuditEventType(str, Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SECRET_ACCESS = "secret_access"
    CONFIG_CHANGE = "config_change"
    SESSION = "session"
    API_ACCESS = "api_access"
    ADMIN_ACTION = "admin_action"
    TOOL_ACCESS = "tool_access"
    WORKFLOW_ACCESS = "workflow_access"
    SECURITY = "security"


@dataclass
class SecurityPrincipal:
    principal_id: str
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    auth_method: AuthMethodType | str | None = None
    session_id: str | None = None
    service_account_id: str | None = None
    telegram_id: int | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessPolicy:
    name: str
    effect: str = "allow"  # allow | deny
    policy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    priority: int = 0

    def matches(
        self,
        *,
        role: str | None = None,
        permission: str | None = None,
        resource: str | None = None,
    ) -> bool:
        if self.roles and role is not None and role not in self.roles:
            return False
        if self.permissions and permission is not None:
            if not any(
                permission == p
                or (p.endswith(".*") and permission.startswith(p[:-1]))
                or fnmatch.fnmatch(permission, p)
                for p in self.permissions
            ):
                return False
        if self.resources and resource is not None and resource not in self.resources:
            return False
        return True


@dataclass
class SecretRecord:
    name: str
    encrypted_value: str
    secret_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    rotated_at: float | None = None


@dataclass
class AuditRecord:
    event_type: AuditEventType | str
    action: str
    principal_id: str | None = None
    resource: str | None = None
    success: bool = True
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))


PolicyMatcher = Callable[..., bool]
