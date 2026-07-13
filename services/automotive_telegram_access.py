# Automotive Telegram UI v2 — role-based access helpers.

from __future__ import annotations

from config import OWNER_ID
from database import get_user_roles
from repositories.user_role_repository import UserRoleRepository
from database.session import get_session

AUTOMOTIVE_UI_ROLES = frozenset(
    {
        "OWNER",
        "ADMIN",
        "SUPER_MANAGER",
        "AUTO_OWNER",
        "AUTO_MANAGER",
        "AUTO_DEALER",
        "MANAGER",
    }
)
AUTOMOTIVE_MENU_ROLES = frozenset(
    {"OWNER", "ADMIN", "SUPER_MANAGER", "AUTO_OWNER", "AUTO_MANAGER", "AUTO_DEALER"}
)


async def can_access_automotive_ui(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    legacy_roles = set(get_user_roles(user_id))
    if legacy_roles & {"OWNER", "ADMIN", "SUPER_MANAGER", "AUTO_MANAGER", "AUTO_DEALER", "MANAGER"}:
        return True
    async with get_session() as session:
        roles = await UserRoleRepository(session).get_user_roles(user_id)
        return any(role.code in AUTOMOTIVE_UI_ROLES for role in roles)


async def can_see_automotive_menu_button(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    legacy_roles = set(get_user_roles(user_id))
    if legacy_roles & AUTOMOTIVE_MENU_ROLES:
        return True
    async with get_session() as session:
        roles = await UserRoleRepository(session).get_user_roles(user_id)
        return any(role.code in AUTOMOTIVE_MENU_ROLES for role in roles)


async def is_billing_owner(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    return "OWNER" in set(get_user_roles(user_id))
