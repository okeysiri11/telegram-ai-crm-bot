# RoleService — permissions and role assignment (PostgreSQL permission engine).

from __future__ import annotations

from config import OWNER_ID
from database.session import get_session
from repositories.user_repository import UserRepository
from services.pg_platform_permissions_engine import PlatformPermissionsEngineV1


class RoleService:
    @staticmethod
    async def has_permission(telegram_id: int, permission_code: str) -> bool:
        if OWNER_ID is not None and telegram_id == OWNER_ID:
            return True
        return await PlatformPermissionsEngineV1.user_has_permission(
            telegram_id,
            permission_code,
        )

    @staticmethod
    async def assign_role(
        *,
        telegram_id: int,
        role_code: str,
    ) -> dict | None:
        from services.user_service import user_service

        return await user_service.assign_role(telegram_id=telegram_id, role_code=role_code)

    @staticmethod
    async def ensure_platform_roles_seeded() -> dict:
        return await PlatformPermissionsEngineV1.ensure_seeded()

    @staticmethod
    async def user_role_codes(telegram_id: int) -> list[str]:
        async with get_session() as session:
            user = await UserRepository(session).get_by_telegram_id(telegram_id)
            if user is None:
                return []
            return await UserRepository(session).list_role_codes(user.id)


role_service = RoleService()

# Legacy permission alias map (SQLite names → permission engine codes).
LEGACY_PERMISSION_ALIASES: dict[str, str] = {
    "admin": "admin.access",
    "manage_leads": "leads.assign",
    "view_analytics": "analytics.view",
    "manage_inventory": "inventory.manage",
}


async def resolve_permission(code: str) -> str:
    return LEGACY_PERMISSION_ALIASES.get(code, code)
