# Permission and role models.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class SystemRole(str, enum.Enum):
    PLATFORM_OWNER = "platform_owner"
    ORGANIZATION_OWNER = "organization_owner"
    ADMINISTRATOR = "administrator"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    CUSTOMER = "customer"
    DEALER = "dealer"
    PARTNER = "partner"
    AI_AGENT = "ai_agent"


BUILTIN_ROLE_PERMISSIONS: dict[SystemRole, list[str]] = {
    SystemRole.PLATFORM_OWNER: ["*"],
    SystemRole.ORGANIZATION_OWNER: ["org:*", "workspace:*", "members:*"],
    SystemRole.ADMINISTRATOR: ["org:read", "org:write", "workspace:*", "members:*"],
    SystemRole.MANAGER: ["org:read", "workspace:read", "workspace:write", "members:read"],
    SystemRole.EMPLOYEE: ["org:read", "workspace:read"],
    SystemRole.CUSTOMER: ["workspace:read", "apps:auto_marketplace:customer"],
    SystemRole.DEALER: ["workspace:read", "apps:auto_marketplace:dealer"],
    SystemRole.PARTNER: ["workspace:read", "apps:auto_marketplace:partner"],
    SystemRole.AI_AGENT: ["workspace:read", "ai:invoke", "ai:delegate"],
}


@dataclass
class Role:
    role_id: str = field(default_factory=_id)
    name: str = ""
    system_role: SystemRole | None = None
    is_custom: bool = False
    organization_id: str = ""
    permissions: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "name": self.name,
            "system_role": self.system_role.value if self.system_role else None,
            "is_custom": self.is_custom,
            "organization_id": self.organization_id,
            "permissions": list(self.permissions),
            "created_at": self.created_at,
        }


@dataclass
class RoleAssignment:
    assignment_id: str = field(default_factory=_id)
    user_id: str = ""
    role_id: str = ""
    organization_id: str = ""
    scope: str = "organization"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "user_id": self.user_id,
            "role_id": self.role_id,
            "organization_id": self.organization_id,
            "scope": self.scope,
            "created_at": self.created_at,
        }
