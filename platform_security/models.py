# Security domain models.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SecurityRole(str, Enum):
    OWNER = "owner"
    ADMINISTRATOR = "administrator"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    MANAGER = "manager"
    VIEWER = "viewer"
    AI_AGENT = "ai_agent"
    SERVICE = "service"
    CUSTOM = "custom"


class AuthMethodType(str, Enum):
    API_KEY = "api_key"
    JWT = "jwt"
    OAUTH = "oauth"
    SERVICE_ACCOUNT = "service_account"
    ANONYMOUS = "anonymous"


class PermissionScope(str, Enum):
    CAPABILITY = "capability"
    AGENT = "agent"
    TOOL = "tool"
    WORKFLOW = "workflow"
    REPOSITORY = "repository"
    SYSTEM = "system"


class AuditEventType(str, Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    TOOL_ACCESS = "tool_access"
    WORKFLOW_ACCESS = "workflow_access"
    CONFIG_CHANGE = "config_change"
    SECURITY = "security"
    SECRET_ACCESS = "secret_access"


@dataclass
class SecurityPrincipal:
    principal_id: str
    auth_method: AuthMethodType = AuthMethodType.JWT
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    agent_id: str | None = None
    service_account_id: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def to_dict(self) -> dict[str, Any]:
        return {
            "principal_id": self.principal_id,
            "auth_method": self.auth_method.value,
            "roles": list(self.roles),
            "permissions": list(self.permissions),
            "agent_id": self.agent_id,
            "session_id": self.session_id,
        }


@dataclass
class AccessPolicy:
    policy_id: str
    name: str
    description: str = ""
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    resource_type: str | None = None
    resource_pattern: str | None = None
    effect: str = "allow"  # allow | deny
    priority: int = 0

    def matches(self, *, role: str, permission: str, resource: str | None = None) -> bool:
        if self.roles and role not in self.roles:
            return False
        if self.permissions and not any(permission.startswith(p.rstrip("*")) for p in self.permissions):
            return False
        if self.resource_pattern and resource:
            prefix = self.resource_pattern.rstrip("*")
            if not resource.startswith(prefix):
                return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "roles": list(self.roles),
            "permissions": list(self.permissions),
            "effect": self.effect,
        }


@dataclass
class SecretRecord:
    secret_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    encrypted_value: str = ""
    version: int = 1
    rotated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "secret_id": self.secret_id,
            "name": self.name,
            "version": self.version,
            "rotated_at": self.rotated_at,
        }


@dataclass
class AuditRecord:
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType = AuditEventType.SECURITY
    principal_id: str | None = None
    action: str = ""
    resource: str | None = None
    success: bool = True
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "event_type": self.event_type.value,
            "principal_id": self.principal_id,
            "action": self.action,
            "resource": self.resource,
            "success": self.success,
            "timestamp": self.timestamp,
        }
