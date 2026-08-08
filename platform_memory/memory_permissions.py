"""Epic 45.2 — Memory ACL (user / company / role / project)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from platform_memory.continuity_store import MemoryRecord


@dataclass(frozen=True)
class MemoryPrincipal:
    owner_id: str
    company_id: str = "default"
    role: str = "owner"
    project_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_id": self.owner_id,
            "company_id": self.company_id,
            "role": self.role,
            "project_ids": list(self.project_ids),
        }


ROLE_RANK = {
    "viewer": 1,
    "member": 2,
    "manager": 3,
    "owner": 4,
    "admin": 5,
}


def can_read(principal: MemoryPrincipal, record: MemoryRecord) -> bool:
    if record.owner_id == principal.owner_id and record.company_id == principal.company_id:
        return True
    if record.company_id != principal.company_id:
        return False
    if principal.role in ("admin", "owner"):
        return True
    if record.project_id and record.project_id in principal.project_ids:
        return ROLE_RANK.get(principal.role, 0) >= ROLE_RANK.get("member", 0)
    return False


def can_write(principal: MemoryPrincipal, record: MemoryRecord | None = None, *, project_id: str | None = None) -> bool:
    if ROLE_RANK.get(principal.role, 0) < ROLE_RANK.get("member", 0):
        return False
    if record is None:
        return True
    if record.owner_id == principal.owner_id:
        return True
    if principal.role in ("admin", "owner"):
        return record.company_id == principal.company_id
    pid = project_id or record.project_id
    return bool(pid and pid in principal.project_ids)


def can_delete(principal: MemoryPrincipal, record: MemoryRecord) -> bool:
    if record.owner_id == principal.owner_id:
        return True
    return principal.role in ("admin", "owner") and record.company_id == principal.company_id


def filter_readable(principal: MemoryPrincipal, records: list[MemoryRecord]) -> list[MemoryRecord]:
    return [r for r in records if can_read(principal, r)]
