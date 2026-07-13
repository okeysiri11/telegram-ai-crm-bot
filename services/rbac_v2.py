# RBAC v2 service — permission checks, inheritance, cache, role templates.

from __future__ import annotations

import time
from typing import Any

from config import OWNER_ID
from database.seeds.rbac_v2 import (
    RBAC_V2_DIRECT_ROLE_PERMISSIONS,
    RBAC_V2_ROLE_INHERITANCE,
)
from database.session import get_session
from repositories.rbac_v2_repository import RbacV2Repository


class RbacV2Engine:
    _CACHE_TTL_SECONDS = 300
    _permission_cache: dict[int, tuple[float, frozenset[str]]] = {}
    _registry_loaded = False
    _permission_parents: dict[str, str | None] = {}
    _role_grants: dict[str, frozenset[str]] = {}
    _role_inheritance: dict[str, frozenset[str]] = {}

    @classmethod
    def invalidate_cache(cls, telegram_user_id: int | None = None) -> None:
        if telegram_user_id is None:
            cls._permission_cache.clear()
            return
        cls._permission_cache.pop(telegram_user_id, None)

    @classmethod
    async def seed_defaults(cls) -> dict[str, int]:
        async with get_session() as session:
            counts = await RbacV2Repository(session).seed_v2()
        cls._registry_loaded = False
        cls.invalidate_cache()
        return counts

    @classmethod
    async def _ensure_registry(cls) -> None:
        if cls._registry_loaded:
            return
        async with get_session() as session:
            repo = RbacV2Repository(session)
            permissions = await repo.list_permissions()
            cls._permission_parents = {p.code: p.parent_code for p in permissions}
            grants = await repo.list_role_grants()
            role_grants: dict[str, set[str]] = {}
            for grant in grants:
                role_grants.setdefault(grant.role_code, set()).add(grant.permission_code)
            cls._role_grants = {k: frozenset(v) for k, v in role_grants.items()}
            inheritance = await repo.list_role_inheritance()
            role_inheritance: dict[str, set[str]] = {}
            for row in inheritance:
                role_inheritance.setdefault(row.role_code, set()).add(row.parent_role_code)
            cls._role_inheritance = {k: frozenset(v) for k, v in role_inheritance.items()}
        if not cls._role_grants:
            cls._role_grants = dict(RBAC_V2_DIRECT_ROLE_PERMISSIONS)
        if not cls._role_inheritance:
            cls._role_inheritance = dict(RBAC_V2_ROLE_INHERITANCE)
        cls._registry_loaded = True

    @classmethod
    def _expand_roles(cls, role_codes: set[str]) -> set[str]:
        expanded = set(role_codes)
        queue = list(role_codes)
        while queue:
            role = queue.pop()
            for parent in cls._role_inheritance.get(role, frozenset()):
                if parent not in expanded:
                    expanded.add(parent)
                    queue.append(parent)
        return expanded

    @classmethod
    def _expand_permission_parents(cls, codes: set[str]) -> set[str]:
        expanded = set(codes)
        queue = list(codes)
        while queue:
            code = queue.pop()
            parent = cls._permission_parents.get(code)
            if parent and parent not in expanded:
                expanded.add(parent)
                queue.append(parent)
        return expanded

    @classmethod
    def _resolve_grants_for_roles(cls, role_codes: set[str]) -> frozenset[str]:
        perms: set[str] = set()
        for role in role_codes:
            perms.update(cls._role_grants.get(role, frozenset()))
        return frozenset(cls._expand_permission_parents(perms))

    @classmethod
    async def get_effective_permissions(cls, telegram_user_id: int) -> frozenset[str]:
        if telegram_user_id == OWNER_ID:
            from database.seeds.rbac_v2 import ALL_RBAC_V2_PERMISSION_CODES
            return ALL_RBAC_V2_PERMISSION_CODES

        cached = cls._permission_cache.get(telegram_user_id)
        now = time.monotonic()
        if cached and now - cached[0] < cls._CACHE_TTL_SECONDS:
            return cached[1]

        await cls._ensure_registry()
        async with get_session() as session:
            role_codes = set(await RbacV2Repository(session).get_user_role_codes(telegram_user_id))
        effective_roles = cls._expand_roles(role_codes)
        permissions = cls._resolve_grants_for_roles(effective_roles)
        cls._permission_cache[telegram_user_id] = (now, permissions)
        return permissions

    @classmethod
    async def has_permission(cls, telegram_user_id: int, permission_code: str) -> bool:
        return permission_code in await cls.get_effective_permissions(telegram_user_id)

    @classmethod
    async def has_module_access(cls, telegram_user_id: int, module_key: str) -> bool:
        mapping = {
            "automotive": "auto.module",
            "auto": "auto.module",
            "agro": "agro.module",
            "agro_trading": "agro.module",
            "finance": "finance.module",
            "legal": "legal.module",
            "law": "legal.module",
            "drone": "drone.module",
            "billing": "billing.module",
            "analytics": "analytics.module",
        }
        code = mapping.get(module_key, f"{module_key}.module")
        return await cls.has_permission(telegram_user_id, code)

    @classmethod
    async def has_entity_access(cls, telegram_user_id: int, entity_code: str) -> bool:
        return await cls.has_permission(telegram_user_id, entity_code)

    @classmethod
    async def has_tenant_access(cls, telegram_user_id: int, *, write: bool = False) -> bool:
        code = "tenant.write" if write else "tenant.read"
        return await cls.has_permission(telegram_user_id, code)

    @classmethod
    async def has_billing_access(cls, telegram_user_id: int, *, approve: bool = False) -> bool:
        if approve:
            return await cls.has_permission(telegram_user_id, "billing.approve")
        return await cls.has_permission(telegram_user_id, "billing.view")

    @classmethod
    async def has_analytics_access(cls, telegram_user_id: int, *, export: bool = False) -> bool:
        if export:
            return await cls.has_permission(telegram_user_id, "analytics.export")
        return await cls.has_permission(telegram_user_id, "analytics.view")

    @classmethod
    async def assign_role(cls, telegram_user_id: int, role_code: str) -> bool:
        async with get_session() as session:
            ok = await RbacV2Repository(session).assign_role_by_code(telegram_user_id, role_code)
        cls.invalidate_cache(telegram_user_id)
        return ok

    @classmethod
    async def get_access_matrix(cls) -> dict[str, dict[str, bool]]:
        await cls._ensure_registry()
        from database.seeds.rbac_v2 import RBAC_V2_ROLES, ALL_RBAC_V2_PERMISSION_CODES

        matrix: dict[str, dict[str, bool]] = {}
        sample_perms = sorted(ALL_RBAC_V2_PERMISSION_CODES)
        for role_code, _, _ in RBAC_V2_ROLES:
            roles = cls._expand_roles({role_code})
            grants = cls._resolve_grants_for_roles(roles)
            matrix[role_code] = {perm: perm in grants for perm in sample_perms}
        return matrix

    @classmethod
    async def format_inspector(cls, telegram_user_id: int) -> str:
        perms = sorted(await cls.get_effective_permissions(telegram_user_id))
        async with get_session() as session:
            roles = await RbacV2Repository(session).get_user_role_codes(telegram_user_id)
        lines = [
            f"RBAC v2 — user {telegram_user_id}",
            f"Roles: {', '.join(roles) if roles else '—'}",
            f"Permissions ({len(perms)}):",
        ]
        lines.extend(f"• {code}" for code in perms[:40])
        if len(perms) > 40:
            lines.append(f"... +{len(perms) - 40} more")
        return "\n".join(lines)


# Backward-compatible async helpers (UUID user API)
async def user_has_permission(user_id, permission_code: str) -> bool:
    return await RbacV2Engine.has_permission(int(user_id), permission_code)


async def assign_role(user_id, role_code: str, assigned_by=None) -> bool:
    return await RbacV2Engine.assign_role(int(user_id), role_code)


async def remove_role(user_id, role_code: str) -> bool:
    async with get_session() as session:
        repo = RbacV2Repository(session)
        roles = await repo.get_user_role_codes(int(user_id))
        if role_code not in roles:
            return False
        await repo.clear_user_roles(int(user_id))
        for code in roles:
            if code != role_code:
                await repo.assign_role_by_code(int(user_id), code)
    RbacV2Engine.invalidate_cache(int(user_id))
    return True


async def seed_rbac_defaults() -> dict[str, int]:
    return await RbacV2Engine.seed_defaults()
