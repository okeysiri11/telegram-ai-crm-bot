# IAM domain models — principals, sessions, keys, policies.

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class PlatformRole(str, enum.Enum):
    OWNER = "owner"
    ADMINISTRATOR = "administrator"
    MANAGER = "manager"
    OPERATOR = "operator"
    READ_ONLY = "readonly"
    SERVICE = "service"
    PLUGIN = "plugin"
    AI = "ai"


class AuthMethod(str, enum.Enum):
    TELEGRAM_OWNER = "telegram_owner"
    TELEGRAM_USER = "telegram_user"
    JWT = "jwt"
    API_KEY = "api_key"
    SERVICE_ACCOUNT = "service_account"
    OAUTH = "oauth"


@dataclass
class ResourceRef:
    type: str
    id: str | None = None
    tenant_id: str | None = None


@dataclass
class Principal:
    """Authenticated identity — single source for authorization checks."""

    principal_id: str
    auth_method: AuthMethod
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    telegram_id: int | None = None
    service_account_id: str | None = None
    tenant_id: str | None = None
    session_id: str | None = None
    api_key_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_owner(self) -> bool:
        return PlatformRole.OWNER.value in self.roles

    def to_dict(self) -> dict[str, Any]:
        return {
            "principal_id": self.principal_id,
            "auth_method": self.auth_method.value,
            "roles": self.roles,
            "permissions": self.permissions,
            "telegram_id": self.telegram_id,
            "service_account_id": self.service_account_id,
            "tenant_id": self.tenant_id,
            "session_id": self.session_id,
            "api_key_id": self.api_key_id,
            "metadata": self.metadata,
        }


@dataclass
class SessionRecord:
    session_id: str
    principal_id: str
    telegram_id: int | None
    roles: list[str]
    login_at: datetime
    last_activity: datetime
    ip: str
    device: str
    expires_at: datetime
    revoked: bool = False
    refresh_token_id: str | None = None

    @staticmethod
    def new(
        *,
        principal: Principal,
        ip: str,
        device: str,
        ttl_seconds: int,
        refresh_token_id: str | None = None,
    ) -> SessionRecord:
        now = datetime.now(timezone.utc)
        return SessionRecord(
            session_id=str(uuid.uuid4()),
            principal_id=principal.principal_id,
            telegram_id=principal.telegram_id,
            roles=list(principal.roles),
            login_at=now,
            last_activity=now,
            ip=ip,
            device=device,
            expires_at=datetime.fromtimestamp(now.timestamp() + ttl_seconds, tz=timezone.utc),
            refresh_token_id=refresh_token_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "principal_id": self.principal_id,
            "telegram_id": self.telegram_id,
            "roles": self.roles,
            "login_at": self.login_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "ip": self.ip,
            "device": self.device,
            "expires_at": self.expires_at.isoformat(),
            "revoked": self.revoked,
            "refresh_token_id": self.refresh_token_id,
        }


@dataclass
class ApiKeyRecord:
    key_id: str
    name: str
    key_hash: str
    prefix: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None
    disabled: bool = False
    last_used_at: datetime | None = None
    principal_id: str | None = None
    telegram_id: int | None = None

    def to_dict(self, *, include_hash: bool = False) -> dict[str, Any]:
        data = {
            "key_id": self.key_id,
            "name": self.name,
            "prefix": self.prefix,
            "scopes": self.scopes,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "disabled": self.disabled,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "principal_id": self.principal_id,
            "telegram_id": self.telegram_id,
        }
        if include_hash:
            data["key_hash"] = self.key_hash
        return data


@dataclass
class PolicyRule:
    policy_id: str
    name: str
    effect: str  # allow | deny
    permissions: list[str]
    roles: list[str] = field(default_factory=list)
    principal_ids: list[str] = field(default_factory=list)
    resources: list[ResourceRef] = field(default_factory=list)
    tenant_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "effect": self.effect,
            "permissions": self.permissions,
            "roles": self.roles,
            "principal_ids": self.principal_ids,
            "resources": [
                {"type": r.type, "id": r.id, "tenant_id": r.tenant_id} for r in self.resources
            ],
            "tenant_id": self.tenant_id,
        }


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime
    session_id: str
    token_id: str
