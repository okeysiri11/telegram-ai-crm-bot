# Organization models — org hierarchy and membership.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


@dataclass
class Organization:
    organization_id: str = field(default_factory=_id)
    tenant_id: str = ""
    name: str = ""
    slug: str = ""
    owner_id: str = ""
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "slug": self.slug,
            "owner_id": self.owner_id,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class Workspace:
    workspace_id: str = field(default_factory=_id)
    organization_id: str = ""
    name: str = ""
    slug: str = ""
    owner_id: str = ""
    is_default: bool = False
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "organization_id": self.organization_id,
            "name": self.name,
            "slug": self.slug,
            "owner_id": self.owner_id,
            "is_default": self.is_default,
            "created_at": self.created_at,
        }


@dataclass
class Department:
    department_id: str = field(default_factory=_id)
    organization_id: str = ""
    name: str = ""
    parent_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "department_id": self.department_id,
            "organization_id": self.organization_id,
            "name": self.name,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
        }


@dataclass
class Team:
    team_id: str = field(default_factory=_id)
    organization_id: str = ""
    department_id: str = ""
    name: str = ""
    lead_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "team_id": self.team_id,
            "organization_id": self.organization_id,
            "department_id": self.department_id,
            "name": self.name,
            "lead_id": self.lead_id,
            "created_at": self.created_at,
        }


@dataclass
class Project:
    project_id: str = field(default_factory=_id)
    organization_id: str = ""
    workspace_id: str = ""
    team_id: str = ""
    name: str = ""
    status: str = "active"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "team_id": self.team_id,
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class Membership:
    membership_id: str = field(default_factory=_id)
    organization_id: str = ""
    user_id: str = ""
    role_id: str = ""
    department_id: str = ""
    team_id: str = ""
    status: str = "active"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "membership_id": self.membership_id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "role_id": self.role_id,
            "department_id": self.department_id,
            "team_id": self.team_id,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class Invitation:
    invitation_id: str = field(default_factory=_id)
    organization_id: str = ""
    email: str = ""
    role_id: str = ""
    invited_by: str = ""
    token: str = ""
    status: str = "pending"
    expires_at: float = field(default_factory=lambda: _ts() + 604800)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "invitation_id": self.invitation_id,
            "organization_id": self.organization_id,
            "email": self.email,
            "role_id": self.role_id,
            "invited_by": self.invited_by,
            "status": self.status,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
        }
