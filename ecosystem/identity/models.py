# Identity models — unified user, session, device.

from __future__ import annotations

import enum
import hashlib
import secrets
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class SSOProvider(str, enum.Enum):
    LOCAL = "local"
    OAUTH = "oauth"
    SAML = "saml"
    OIDC = "oidc"


@dataclass
class UnifiedUser:
    user_id: str = field(default_factory=_id)
    email: str = ""
    password_hash: str = ""
    display_name: str = ""
    is_active: bool = True
    sso_provider: SSOProvider = SSOProvider.LOCAL
    external_id: str = ""
    mfa_enabled: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "display_name": self.display_name,
            "is_active": self.is_active,
            "sso_provider": self.sso_provider.value,
            "mfa_enabled": self.mfa_enabled,
            "created_at": self.created_at,
        }


@dataclass
class UnifiedSession:
    session_id: str = field(default_factory=_id)
    user_id: str = ""
    access_token: str = ""
    refresh_token: str = ""
    organization_id: str = ""
    workspace_id: str = ""
    device_id: str = ""
    expires_at: float = field(default_factory=lambda: _ts() + 86400)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "device_id": self.device_id,
            "expires_at": self.expires_at,
            "token_type": "Bearer",
        }


@dataclass
class SessionHistoryEntry:
    entry_id: str = field(default_factory=_id)
    user_id: str = ""
    session_id: str = ""
    action: str = ""
    ip_address: str = ""
    user_agent: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "action": self.action,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at,
        }


@dataclass
class Device:
    device_id: str = field(default_factory=_id)
    user_id: str = ""
    name: str = ""
    platform: str = ""
    is_trusted: bool = False
    last_seen_at: float = field(default_factory=_ts)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "user_id": self.user_id,
            "name": self.name,
            "platform": self.platform,
            "is_trusted": self.is_trusted,
            "last_seen_at": self.last_seen_at,
            "created_at": self.created_at,
        }


@dataclass
class MFAEnrollment:
    enrollment_id: str = field(default_factory=_id)
    user_id: str = ""
    method: str = "totp"
    secret_hint: str = ""
    verified: bool = False
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enrollment_id": self.enrollment_id,
            "user_id": self.user_id,
            "method": self.method,
            "verified": self.verified,
            "created_at": self.created_at,
        }


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token() -> str:
    return secrets.token_urlsafe(32)
