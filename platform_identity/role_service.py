# IAM roles — definitions, inheritance, assignment.

from __future__ import annotations

from platform_identity.models import PlatformRole
from platform_identity.permission_service import IAM_PERMISSIONS

ROLE_INHERITANCE: dict[str, tuple[str, ...]] = {
    PlatformRole.OWNER.value: (PlatformRole.ADMINISTRATOR.value,),
    PlatformRole.ADMINISTRATOR.value: (PlatformRole.OPERATOR.value,),
    PlatformRole.OPERATOR.value: (PlatformRole.READ_ONLY.value,),
    PlatformRole.MANAGER.value: (PlatformRole.READ_ONLY.value,),
    PlatformRole.SERVICE.value: (),
    PlatformRole.PLUGIN.value: (),
    PlatformRole.AI.value: (),
}

ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    PlatformRole.OWNER.value: tuple(IAM_PERMISSIONS.keys()),
    PlatformRole.ADMINISTRATOR.value: (
        "system.read",
        "system.admin",
        "configuration.read",
        "configuration.write",
        "dashboard.read",
        "dashboard.admin",
        "requests.read",
        "requests.write",
        "requests.assign",
        "managers.read",
        "managers.write",
        "audit.read",
        "audit.export",
        "workflow.read",
        "workflow.write",
        "sdk.read",
        "sdk.write",
        "plugins.read",
        "plugins.write",
        "ai.read",
        "ai.use",
        "ai.admin",
        "management.read",
        "management.write",
        "management.admin",
        "management.identity.read",
        "management.identity.write",
        "integrations.read",
        "integrations.write",
        "integrations.admin",
        *[k for k in IAM_PERMISSIONS if k.startswith("realtime.")],
    ),
    PlatformRole.MANAGER.value: (
        "dashboard.read",
        "requests.read",
        "requests.write",
        "requests.assign",
        "managers.read",
        "workflow.read",
        "audit.read",
        "ai.use",
        "management.read",
        "realtime.channel.dashboard",
        "realtime.channel.requests",
        "realtime.channel.managers",
        "realtime.channel.workflows",
        "realtime.channel.notifications",
        "realtime.channel.system",
        "realtime.channel.health",
    ),
    PlatformRole.OPERATOR.value: (
        "dashboard.read",
        "requests.read",
        "requests.write",
        "managers.read",
        "workflow.read",
        "audit.read",
        "management.read",
        "realtime.channel.dashboard",
        "realtime.channel.requests",
        "realtime.channel.managers",
        "realtime.channel.workflows",
        "realtime.channel.notifications",
        "realtime.channel.system",
        "realtime.channel.health",
        "realtime.channel.audit",
    ),
    PlatformRole.READ_ONLY.value: (
        "system.read",
        "dashboard.read",
        "requests.read",
        "managers.read",
        "audit.read",
        "workflow.read",
        "configuration.read",
        "plugins.read",
        "ai.read",
        "management.read",
        "management.identity.read",
        "integrations.read",
        "realtime.channel.system",
        "realtime.channel.dashboard",
        "realtime.channel.requests",
        "realtime.channel.workflows",
        "realtime.channel.managers",
        "realtime.channel.audit",
        "realtime.channel.notifications",
        "realtime.channel.health",
    ),
    PlatformRole.SERVICE.value: (
        "sdk.read",
        "sdk.write",
        "management.read",
        "requests.read",
        "requests.write",
    ),
    PlatformRole.PLUGIN.value: (
        "plugins.read",
        "plugins.write",
        "realtime.channel.plugins",
    ),
    PlatformRole.AI.value: (
        "ai.read",
        "ai.use",
        "realtime.channel.ai",
    ),
}


class RoleService:
    @staticmethod
    def list_roles() -> list[str]:
        return [r.value for r in PlatformRole]

    @staticmethod
    def expand_roles(roles: list[str]) -> list[str]:
        expanded: set[str] = set()
        queue = list(roles)
        while queue:
            role = queue.pop(0)
            if role in expanded:
                continue
            expanded.add(role)
            for parent in ROLE_INHERITANCE.get(role, ()):
                if parent not in expanded:
                    queue.append(parent)
        return sorted(expanded)

    @staticmethod
    def permissions_for_role(role: str) -> set[str]:
        perms: set[str] = set()
        for expanded_role in RoleService.expand_roles([role]):
            perms.update(ROLE_PERMISSIONS.get(expanded_role, ()))
        return perms

    @staticmethod
    async def roles_for_telegram_user(telegram_id: int) -> list[str]:
        from config import OWNER_ID

        if OWNER_ID is not None and telegram_id == OWNER_ID:
            return [PlatformRole.OWNER.value]

        roles: list[str] = []
        try:
            from services.pg_platform_permissions_engine import PlatformPermissionsEngineV1

            if await PlatformPermissionsEngineV1.user_has_permission(telegram_id, "admin.access"):
                roles.append(PlatformRole.ADMINISTRATOR.value)
            elif any(
                await PlatformPermissionsEngineV1.user_has_permission(telegram_id, p)
                for p in ("platform.config.read", "analytics.view", "api.access")
            ):
                roles.append(PlatformRole.READ_ONLY.value)
            else:
                from database.session import get_session
                from repositories.user_repository import UserRepository

                async with get_session() as session:
                    user = await UserRepository(session).get_by_telegram_id(telegram_id)
                    if user is not None:
                        db_roles = await UserRepository(session).list_role_codes(user.id)
                        for code in db_roles:
                            mapped = RoleService._map_legacy_role(code)
                            if mapped and mapped not in roles:
                                roles.append(mapped)
        except Exception:
            pass

        if not roles:
            roles.append(PlatformRole.READ_ONLY.value)
        return RoleService.expand_roles(roles)

    @staticmethod
    def _map_legacy_role(code: str) -> str | None:
        mapping = {
            "OWNER": PlatformRole.OWNER.value,
            "ADMIN": PlatformRole.ADMINISTRATOR.value,
            "SUPER_ADMIN": PlatformRole.ADMINISTRATOR.value,
            "MANAGER": PlatformRole.MANAGER.value,
            "AUTO_MANAGER": PlatformRole.MANAGER.value,
            "AGRO_MANAGER": PlatformRole.MANAGER.value,
            "DEALER_MANAGER": PlatformRole.MANAGER.value,
            "AI_AGENT": PlatformRole.AI.value,
            "CLIENT": PlatformRole.READ_ONLY.value,
        }
        return mapping.get(code.upper())


role_service = RoleService()
