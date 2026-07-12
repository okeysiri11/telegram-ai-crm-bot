# Permission Engine — permission repository.

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.permission import EnginePermissionCode, Permission
from database.models.role import Role
from database.models.role_permission import RolePermission


class PermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_permission_by_code(self, permission_code: str) -> Permission | None:
        result = await self._session.execute(
            select(Permission).where(Permission.code == permission_code)
        )
        return result.scalar_one_or_none()

    async def assign_permission(
        self,
        role_id: uuid.UUID,
        permission_code: str,
    ) -> RolePermission:
        if permission_code not in {p.value for p in EnginePermissionCode}:
            raise ValueError(f"Invalid permission code: {permission_code}")

        permission = await self._get_permission_by_code(permission_code)
        if permission is None:
            raise ValueError(f"Permission not found: {permission_code}")

        existing = await self._session.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission.id,
            )
        )
        link = existing.scalar_one_or_none()
        if link is not None:
            return link

        link = RolePermission(role_id=role_id, permission_id=permission.id)
        self._session.add(link)
        await self._session.flush()
        return link

    async def revoke_permission(
        self,
        role_id: uuid.UUID,
        permission_code: str,
    ) -> bool:
        permission = await self._get_permission_by_code(permission_code)
        if permission is None:
            return False

        result = await self._session.execute(
            delete(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission.id,
            )
        )
        await self._session.flush()
        return result.rowcount > 0

    async def get_permissions_for_role(self, role_id: uuid.UUID) -> list[Permission]:
        result = await self._session.execute(
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
            .order_by(Permission.code.asc())
        )
        return list(result.scalars().all())
