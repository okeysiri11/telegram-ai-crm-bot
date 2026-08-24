"""Epic 45.2 — Memory ACL (user / company / role / project).

Sprint 47.1: MemoryPrincipal.scope (see platform_memory.scope.MemoryScope) is
derived from tenant_id/vertical/customer_id/owner_id, not stored separately —
a principal's identifiers are the source of truth."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from platform_memory.continuity_store import MemoryRecord
from platform_memory.scope import MemoryScope, resolve_memory_scope


@dataclass(frozen=True)
class MemoryPrincipal:
    """Sprint 47.0 (Decision 5): tenant_id is the canonical org identifier going
    forward; company_id is kept for backward compatibility and tenant_id mirrors it
    via __post_init__ when not explicitly supplied. Sprint 47.1: vertical/customer_id
    are additive, optional identifiers used only to derive .scope — they do not
    change can_read/can_write/can_delete, which remain tenant_id/owner_id/role/
    project_ids based exactly as in Sprint 47.0."""

    owner_id: str
    company_id: str = "default"
    role: str = "owner"
    project_ids: tuple[str, ...] = ()
    tenant_id: str | None = None
    vertical: str | None = None
    customer_id: str | None = None

    def __post_init__(self) -> None:
        if self.tenant_id is None:
            object.__setattr__(self, "tenant_id", self.company_id)

    @property
    def scope(self) -> MemoryScope:
        return resolve_memory_scope(
            tenant_id=self.tenant_id,
            vertical=self.vertical,
            customer_id=self.customer_id,
            user_id=self.owner_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_id": self.owner_id,
            "company_id": self.company_id,
            "tenant_id": self.tenant_id,
            "vertical": self.vertical,
            "customer_id": self.customer_id,
            "scope": self.scope.value,
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
    # Sprint 47.0 (Decision 5): compare on tenant_id — equivalent to the prior
    # company_id comparison for every existing caller, since tenant_id mirrors
    # company_id when not explicitly set (see MemoryPrincipal/MemoryRecord).
    if record.owner_id == principal.owner_id and record.tenant_id == principal.tenant_id:
        return True
    if record.tenant_id != principal.tenant_id:
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
        return record.tenant_id == principal.tenant_id
    pid = project_id or record.project_id
    return bool(pid and pid in principal.project_ids)


def can_delete(principal: MemoryPrincipal, record: MemoryRecord) -> bool:
    if record.owner_id == principal.owner_id:
        return True
    return principal.role in ("admin", "owner") and record.tenant_id == principal.tenant_id


def filter_readable(principal: MemoryPrincipal, records: list[MemoryRecord]) -> list[MemoryRecord]:
    return [r for r in records if can_read(principal, r)]
