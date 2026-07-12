# RBAC v2 service — permission checks and role assignment.

from __future__ import annotations

import uuid

from database.session import get_session
from repositories.rbac_repository import RbacRepository


async def user_has_permission(user_id: uuid.UUID, permission_code: str) -> bool:
    async with get_session() as session:
        repo = RbacRepository(session)
        return await repo.user_has_permission(user_id, permission_code)


async def assign_role(
    user_id: uuid.UUID,
    role_code: str,
    assigned_by: uuid.UUID | None = None,
) -> bool:
    async with get_session() as session:
        repo = RbacRepository(session)
        return await repo.assign_role(user_id, role_code, assigned_by=assigned_by)


async def remove_role(user_id: uuid.UUID, role_code: str) -> bool:
    async with get_session() as session:
        repo = RbacRepository(session)
        return await repo.remove_role(user_id, role_code)


async def seed_rbac_defaults() -> dict[str, int]:
    async with get_session() as session:
        repo = RbacRepository(session)
        return await repo.seed_defaults()
