# RBAC v2 repository — PostgreSQL async data access.

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.permissions import Permission, RolePermission
from database.models.roles import RbacRole, UserRoleLink
from database.seeds.rbac_v2 import (
    DEFAULT_PERMISSIONS,
    DEFAULT_ROLE_PERMISSIONS,
    DEFAULT_ROLES,
)


class RbacRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_role_by_code(self, role_code: str) -> RbacRole | None:
        result = await self._session.execute(
            select(RbacRole).where(RbacRole.code == role_code)
        )
        return result.scalar_one_or_none()

    async def get_permission_by_code(self, permission_code: str) -> Permission | None:
        result = await self._session.execute(
            select(Permission).where(Permission.code == permission_code)
        )
        return result.scalar_one_or_none()

    async def user_has_permission(
        self,
        user_id: uuid.UUID,
        permission_code: str,
    ) -> bool:
        stmt = (
            select(Permission.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(RbacRole, RbacRole.id == RolePermission.role_id)
            .join(UserRoleLink, UserRoleLink.role_id == RbacRole.id)
            .where(UserRoleLink.user_id == user_id, Permission.code == permission_code)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def assign_role(
        self,
        user_id: uuid.UUID,
        role_code: str,
        assigned_by: uuid.UUID | None = None,
    ) -> bool:
        role = await self.get_role_by_code(role_code)
        if role is None:
            return False

        existing = await self._session.execute(
            select(UserRoleLink).where(
                UserRoleLink.user_id == user_id,
                UserRoleLink.role_id == role.id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return True

        self._session.add(
            UserRoleLink(
                user_id=user_id,
                role_id=role.id,
                assigned_by=assigned_by,
            )
        )
        await self._session.flush()
        return True

    async def remove_role(self, user_id: uuid.UUID, role_code: str) -> bool:
        role = await self.get_role_by_code(role_code)
        if role is None:
            return False

        result = await self._session.execute(
            delete(UserRoleLink).where(
                UserRoleLink.user_id == user_id,
                UserRoleLink.role_id == role.id,
            )
        )
        await self._session.flush()
        return result.rowcount > 0

    async def seed_defaults(self) -> dict[str, int]:
        roles_by_code: dict[str, RbacRole] = {}
        for code, name, description in DEFAULT_ROLES:
            role = await self.get_role_by_code(code)
            if role is None:
                role = RbacRole(code=code, name=name, description=description)
                self._session.add(role)
                await self._session.flush()
            roles_by_code[code] = role

        permissions_by_code: dict[str, Permission] = {}
        for code, description in DEFAULT_PERMISSIONS:
            permission = await self.get_permission_by_code(code)
            if permission is None:
                permission = Permission(code=code, description=description)
                self._session.add(permission)
                await self._session.flush()
            permissions_by_code[code] = permission

        links_created = 0
        for role_code, permission_codes in DEFAULT_ROLE_PERMISSIONS.items():
            role = roles_by_code[role_code]
            for permission_code in permission_codes:
                permission = permissions_by_code[permission_code]
                existing = await self._session.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permission.id,
                    )
                )
                if existing.scalar_one_or_none() is None:
                    self._session.add(
                        RolePermission(role_id=role.id, permission_id=permission.id)
                    )
                    links_created += 1

        await self._session.flush()
        return {
            "roles": len(roles_by_code),
            "permissions": len(permissions_by_code),
            "role_permissions": links_created,
        }
