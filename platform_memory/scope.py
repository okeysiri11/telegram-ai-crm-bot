"""Sprint 47.1 — AI Agent Memory Architecture: the canonical memory scope enum.

Every memory record in the platform is visible to some audience: everyone
(PLATFORM), everyone in one tenant (ORGANIZATION), everyone working a given
business vertical (VERTICAL), one person (USER), or one specific
customer/project (CUSTOMER). This module is the single source of truth for
that classification — do not add a second, parallel scope concept elsewhere.

This is intentionally a *derivation* over the identifiers Sprint 47.0 already
established as canonical (tenant_id, vertical, customer_id, user_id — see
platform_orchestrator.models.AgentContext and the tenant_id fields added to
platform_memory.models / platform_memory.continuity_store /
platform_memory.memory_permissions), not a field every record must be told to
set independently. A record's identifiers are the source of truth; scope is
computed from them so the two can never silently disagree.

"level" (session | working | project | long_term | knowledge, see
continuity_store.MemoryRecord) is a *durability* axis — how long a memory
sticks around — and is orthogonal to scope. Do not conflate them.
"""

from __future__ import annotations

from enum import Enum


class MemoryScope(str, Enum):
    PLATFORM = "platform"
    ORGANIZATION = "organization"
    VERTICAL = "vertical"
    USER = "user"
    CUSTOMER = "customer"


def resolve_memory_scope(
    *,
    tenant_id: str | None = None,
    vertical: str | None = None,
    customer_id: str | None = None,
    user_id: str | None = None,
) -> MemoryScope:
    """Derive the narrowest applicable scope from whichever identifiers are set.

    Precedence, narrowest first: a record tied to one CUSTOMER/project is the
    most tightly scoped, even if it also happens to carry a user_id or
    vertical (e.g. "what the account manager noted about customer X" is
    CUSTOMER-scoped, not USER-scoped, even though a specific user wrote it).
    Next narrowest is USER (a person's own preference/fact, independent of
    which vertical they were in when it was recorded). Then VERTICAL (shared
    knowledge for a whole business vertical, not tied to one person or
    customer). Then ORGANIZATION (tenant-wide). PLATFORM is the fallback when
    none of the identifiers are set — a fact true everywhere.
    """
    if customer_id:
        return MemoryScope.CUSTOMER
    if user_id:
        return MemoryScope.USER
    if vertical:
        return MemoryScope.VERTICAL
    if tenant_id:
        return MemoryScope.ORGANIZATION
    return MemoryScope.PLATFORM
