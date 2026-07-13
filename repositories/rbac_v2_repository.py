# RBAC v2 repository — permissions, inheritance, templates, grants.

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.rbac_v2_engine import (
    RbacPermission,
    RbacRoleGrant,
    RbacRoleInheritance,
    RbacRoleTemplate,
)
from database.models.role import Role
from database.models.user_role import UserRole
from database.seeds.rbac_v2 import (
    RBAC_V2_DIRECT_ROLE_PERMISSIONS,
    RBAC_V2_PERMISSIONS,
    RBAC_V2_ROLE_INHERITANCE,
    RBAC_V2_ROLE_TEMPLATES,
    RBAC_V2_ROLES,
)


class RbacV2Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def seed_v2(self) -> dict[str, int]:
        perm_count = 0
        for code, category, parent_code, description in RBAC_V2_PERMISSIONS:
            existing = await self._session.execute(
                select(RbacPermission).where(RbacPermission.code == code)
            )
            if existing.scalar_one_or_none() is None:
                self._session.add(
                    RbacPermission(
                        code=code,
                        category=category,
                        parent_code=parent_code,
                        description=description,
                    )
                )
                perm_count += 1
        await self._session.flush()

        role_count = 0
        for code, name, description in RBAC_V2_ROLES:
            existing = await self._session.execute(select(Role).where(Role.code == code))
            if existing.scalar_one_or_none() is None:
                self._session.add(Role(code=code, name=name, description=description))
                role_count += 1
        await self._session.flush()

        inherit_count = 0
        for role_code, parents in RBAC_V2_ROLE_INHERITANCE.items():
            for parent in parents:
                exists = await self._session.execute(
                    select(RbacRoleInheritance).where(
                        RbacRoleInheritance.role_code == role_code,
                        RbacRoleInheritance.parent_role_code == parent,
                    )
                )
                if exists.scalar_one_or_none() is None:
                    self._session.add(
                        RbacRoleInheritance(role_code=role_code, parent_role_code=parent)
                    )
                    inherit_count += 1
        await self._session.flush()

        grant_count = 0
        for role_code, permission_codes in RBAC_V2_DIRECT_ROLE_PERMISSIONS.items():
            for permission_code in permission_codes:
                exists = await self._session.execute(
                    select(RbacRoleGrant).where(
                        RbacRoleGrant.role_code == role_code,
                        RbacRoleGrant.permission_code == permission_code,
                    )
                )
                if exists.scalar_one_or_none() is None:
                    self._session.add(
                        RbacRoleGrant(role_code=role_code, permission_code=permission_code)
                    )
                    grant_count += 1
        await self._session.flush()

        template_count = 0
        for code, name, description, role_codes, permission_codes in RBAC_V2_ROLE_TEMPLATES:
            existing = await self._session.execute(
                select(RbacRoleTemplate).where(RbacRoleTemplate.code == code)
            )
            row = existing.scalar_one_or_none()
            if row is None:
                self._session.add(
                    RbacRoleTemplate(
                        code=code,
                        name=name,
                        description=description,
                        role_codes=list(role_codes),
                        permission_codes=list(permission_codes),
                    )
                )
                template_count += 1
        await self._session.flush()

        return {
            "permissions": perm_count,
            "roles": role_count,
            "inheritance": inherit_count,
            "grants": grant_count,
            "templates": template_count,
        }

    async def list_permissions(self) -> list[RbacPermission]:
        result = await self._session.execute(select(RbacPermission))
        return list(result.scalars().all())

    async def list_role_inheritance(self) -> list[RbacRoleInheritance]:
        result = await self._session.execute(select(RbacRoleInheritance))
        return list(result.scalars().all())

    async def list_role_grants(self) -> list[RbacRoleGrant]:
        result = await self._session.execute(select(RbacRoleGrant))
        return list(result.scalars().all())

    async def list_templates(self) -> list[RbacRoleTemplate]:
        result = await self._session.execute(select(RbacRoleTemplate))
        return list(result.scalars().all())

    async def get_user_role_codes(self, telegram_user_id: int) -> list[str]:
        result = await self._session.execute(
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == telegram_user_id)
            .order_by(Role.code.asc())
        )
        return list(result.scalars().all())

    async def assign_role_by_code(self, telegram_user_id: int, role_code: str) -> bool:
        role_result = await self._session.execute(select(Role).where(Role.code == role_code))
        role = role_result.scalar_one_or_none()
        if role is None:
            return False
        existing = await self._session.execute(
            select(UserRole).where(
                UserRole.user_id == telegram_user_id,
                UserRole.role_id == role.id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return True
        self._session.add(UserRole(user_id=telegram_user_id, role_id=role.id))
        await self._session.flush()
        return True

    async def clear_user_roles(self, telegram_user_id: int) -> None:
        await self._session.execute(
            delete(UserRole).where(UserRole.user_id == telegram_user_id)
        )
        await self._session.flush()
