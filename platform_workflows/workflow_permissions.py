"""Epic 45.3 — workflow ACL."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

ROLE_RANK = {"viewer": 1, "member": 2, "manager": 3, "owner": 4, "admin": 5}

@dataclass(frozen=True)
class WorkflowPrincipal:
    owner_id: str
    company_id: str = "default"
    role: str = "owner"
    def to_dict(self) -> dict[str, Any]:
        return {"owner_id": self.owner_id, "company_id": self.company_id, "role": self.role}

def can_run(p: WorkflowPrincipal) -> bool:
    return ROLE_RANK.get(p.role, 0) >= ROLE_RANK["member"]

def can_manage(p: WorkflowPrincipal) -> bool:
    return ROLE_RANK.get(p.role, 0) >= ROLE_RANK["manager"]

def can_approve(p: WorkflowPrincipal) -> bool:
    return ROLE_RANK.get(p.role, 0) >= ROLE_RANK["member"]
