# Platform roles & permissions seed / check.

from __future__ import annotations

import logging
from typing import Any

from database.session import get_session

logger = logging.getLogger(__name__)

PLATFORM_ROLES = (
    "OWNER",
    "ADMIN",
    "SUPER_ADMIN",
    "MANAGER",
    "AUTO_MANAGER",
    "AGRO_MANAGER",
    "DEALER_MANAGER",
    "CLIENT",
    "AI_AGENT",
)

PLATFORM_PERMISSIONS: dict[str, str] = {
    "leads.view": "View leads",
    "leads.create": "Create leads",
    "leads.assign": "Assign managers",
    "leads.update_status": "Update lead status",
    "clients.view": "View clients",
    "clients.update": "Update client data",
    "inventory.view": "View inventory",
    "inventory.manage": "Manage inventory",
    "analytics.view": "View analytics",
    "admin.access": "Admin panel access",
    "ai.use": "Use AI manager",
    "api.access": "REST API access",
}

ROLE_PERMISSION_MAP: dict[str, tuple[str, ...]] = {
    "OWNER": tuple(PLATFORM_PERMISSIONS.keys()),
    "ADMIN": (
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
    ),
    "SUPER_ADMIN": tuple(PLATFORM_PERMISSIONS.keys()),
    "MANAGER": (
        "leads.view",
        "leads.assign",
        "leads.update_status",
        "clients.view",
        "inventory.view",
        "ai.use",
    ),
    "AUTO_MANAGER": (
        "leads.view",
        "leads.assign",
        "leads.update_status",
        "clients.view",
        "inventory.view",
        "ai.use",
    ),
    "AGRO_MANAGER": (
        "leads.view",
        "leads.assign",
        "leads.update_status",
        "clients.view",
        "ai.use",
    ),
    "DEALER_MANAGER": (
        "leads.view",
        "leads.update_status",
        "clients.view",
        "inventory.view",
        "inventory.manage",
        "ai.use",
    ),
    "CLIENT": ("leads.create", "inventory.view", "ai.use"),
    "AI_AGENT": ("leads.view", "leads.create", "ai.use"),
}


class PlatformPermissionsEngineV1:
    @staticmethod
    async def ensure_seeded() -> dict[str, Any]:
        """Ensure platform roles + permissions exist in permission_engine tables."""
        from database.models.permission import Permission
        from database.models.role import PermissionRole
        from database.models.role_permission import RolePermission
        from sqlalchemy import select

        created_roles = 0
        created_perms = 0
        linked = 0

        async with get_session() as session:
            perm_by_code: dict[str, Any] = {}
            for code, desc in PLATFORM_PERMISSIONS.items():
                row = (
                    await session.execute(select(Permission).where(Permission.code == code))
                ).scalar_one_or_none()
                if row is None:
                    row = Permission(code=code, description=desc)
                    session.add(row)
                    await session.flush()
                    created_perms += 1
                perm_by_code[code] = row

            for role_code in PLATFORM_ROLES:
                role = (
                    await session.execute(
                        select(PermissionRole).where(PermissionRole.code == role_code)
                    )
                ).scalar_one_or_none()
                if role is None:
                    role = PermissionRole(
                        code=role_code,
                        name=role_code.replace("_", " ").title(),
                        description=f"Platform role {role_code}",
                    )
                    session.add(role)
                    await session.flush()
                    created_roles += 1

                for perm_code in ROLE_PERMISSION_MAP.get(role_code, ()):
                    perm = perm_by_code.get(perm_code)
                    if perm is None:
                        continue
                    existing = (
                        await session.execute(
                            select(RolePermission).where(
                                RolePermission.role_id == role.id,
                                RolePermission.permission_id == perm.id,
                            )
                        )
                    ).scalar_one_or_none()
                    if existing is None:
                        session.add(
                            RolePermission(role_id=role.id, permission_id=perm.id)
                        )
                        linked += 1

        return {
            "roles_created": created_roles,
            "permissions_created": created_perms,
            "links_created": linked,
            "roles": list(PLATFORM_ROLES),
        }

    @staticmethod
    async def user_has_permission(telegram_user_id: int, permission_code: str) -> bool:
        from config import OWNER_ID
        from repositories.user_role_repository import UserRoleRepository
        from repositories.users_repository import UsersRepository
        from sqlalchemy import select
        from database.models.role_permission import RolePermission
        from database.models.permission import Permission
        from database.models.user_role import PermissionUserRole

        if OWNER_ID is not None and telegram_user_id == OWNER_ID:
            return True

        async with get_session() as session:
            user = await UsersRepository(session).get_by_telegram_id(telegram_user_id)
            if user is None:
                return False
            result = await session.execute(
                select(Permission.code)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .join(PermissionUserRole, PermissionUserRole.role_id == RolePermission.role_id)
                .where(PermissionUserRole.user_id == user.id)
                .where(Permission.code == permission_code)
            )
            return result.scalar_one_or_none() is not None
