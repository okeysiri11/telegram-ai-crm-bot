# RoleService — delegates authorization to centralized IAM.

from __future__ import annotations

from platform_identity.identity_service import identity_service


class RoleService:
    @staticmethod
    async def has_permission(telegram_id: int, permission_code: str) -> bool:
        return await identity_service.has_legacy_permission(telegram_id, permission_code)

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
        from services.pg_platform_permissions_engine import PlatformPermissionsEngineV1

        return await PlatformPermissionsEngineV1.ensure_seeded()

    @staticmethod
    async def user_role_codes(telegram_id: int) -> list[str]:
        from platform_identity.role_service import role_service as iam_role_service

        return await iam_role_service.roles_for_telegram_user(telegram_id)


role_service = RoleService()

LEGACY_PERMISSION_ALIASES: dict[str, str] = {
    "admin": "admin.access",
    "manage_leads": "leads.assign",
    "view_analytics": "analytics.view",
    "manage_inventory": "inventory.manage",
}


async def resolve_permission(code: str) -> str:
    return LEGACY_PERMISSION_ALIASES.get(code, code)
