# Permissions domain scaffold — Typed models for future migration.
# Existing production tables: permission_engine_roles / permission_engine_permissions.
# These dataclasses do NOT register with SQLAlchemy Base (no runtime conflict).

from __future__ import annotations

from dataclasses import dataclass, field
import uuid


@dataclass
class Role:
    code: str
    name: str
    description: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Permission:
    code: str
    description: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class RolePermission:
    role_id: str
    permission_id: str


PLATFORM_ROLE_CODES = (
    "OWNER",
    "ADMIN",
    "MANAGER",
    "AUTO_MANAGER",
    "DEALER_MANAGER",
    "CLIENT",
    "AI_AGENT",
)

PLATFORM_PERMISSION_CODES = (
    "leads.view",
    "leads.create",
    "leads.assign",
    "leads.update_status",
    "clients.view",
    "clients.update",
    "inventory.view",
    "inventory.manage",
    "analytics.view",
    "admin.access",
    "ai.use",
    "api.access",
)
