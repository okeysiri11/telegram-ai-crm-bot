# ManagerService — vertical lead routing (AUTO / AGRO / SUPER_ADMIN rules).

from __future__ import annotations

import logging
import uuid
from typing import Any

from config import (
    DEFAULT_AGRO_MANAGER_ID,
    DEFAULT_AUTO_MANAGER_ID,
    DEFAULT_DEALER_MANAGER_ID,
    DEFAULT_REALTY_MANAGER_ID,
    OWNER_ID,
)
from database.session import get_session
from repositories.manager_repository import ManagerRepository
from repositories.user_repository import UserRepository
from services.system_roles import SystemRole, Vertical, normalize_vertical

logger = logging.getLogger(__name__)

# Verticals where SUPER_ADMIN must NOT receive automatic lead assignment.
NON_ASSIGNABLE_ROLES = frozenset({SystemRole.SUPER_ADMIN.value, "OWNER", "ADMIN"})

# Default assignees (Telegram IDs from config / .env).
DEFAULT_ASSIGNEES: dict[str, int | None] = {
    Vertical.AUTO.value: DEFAULT_AUTO_MANAGER_ID,
    Vertical.AGRO.value: DEFAULT_AGRO_MANAGER_ID,
    Vertical.REALTY.value: DEFAULT_REALTY_MANAGER_ID,
    Vertical.LEGAL.value: None,
    Vertical.LOGISTICS.value: None,
}

# Display names for diagnostics.
ASSIGNEE_LABELS: dict[str, str] = {
    Vertical.AUTO.value: "Boroda_0003 (AUTO_MANAGER)",
    Vertical.AGRO.value: "Christopher Moltisanti (AGRO_MANAGER)",
    Vertical.REALTY.value: "Luc (REALTY_MANAGER)",
}


class ManagerService:
    @staticmethod
    async def resolve_manager_for_vertical(vertical: str) -> dict[str, Any] | None:
        """
        Resolve primary manager for lead assignment.

        Rules:
        - AUTO → Boroda_0003 (DEFAULT_AUTO_MANAGER_ID)
        - AGRO → Christopher Moltisanti (grain, rapeseed, soy, apples, freight, etc.)
        - SUPER_ADMIN (Tony Soprano / OWNER_ID) — full access but NOT auto-assigned
        """
        key = normalize_vertical(vertical) or vertical.strip().lower()

        async with get_session() as session:
            mgr_repo = ManagerRepository(session)
            subscribed = await mgr_repo.get_primary_for_vertical(key)
            if subscribed is not None:
                sub, user = subscribed
                if user.role in NON_ASSIGNABLE_ROLES or sub.role_code in NON_ASSIGNABLE_ROLES:
                    logger.info(
                        "Skipping SUPER_ADMIN for auto-assign vertical=%s user=%s",
                        key,
                        user.telegram_id,
                    )
                elif user.telegram_id is not None:
                    return ManagerRepository.manager_snapshot(user, sub)

        # Fallback to configured defaults.
        default_tid = DEFAULT_ASSIGNEES.get(key)
        if default_tid is None and key == Vertical.AUTO.value:
            default_tid = DEFAULT_DEALER_MANAGER_ID

        if default_tid is None:
            logger.warning("No manager configured for vertical=%s", key)
            return None

        if OWNER_ID is not None and default_tid == OWNER_ID:
            logger.info("SUPER_ADMIN excluded from auto-assign vertical=%s", key)
            return None

        async with get_session() as session:
            user = await UserRepository(session).get_by_telegram_id(default_tid)
            if user is None or user.telegram_id is None:
                return None
            return ManagerRepository.manager_snapshot(user)

    @staticmethod
    async def resolve_manager_triple(
        vertical: str,
    ) -> tuple[uuid.UUID, int, str] | None:
        """Return (user_uuid, telegram_id, display_name) for engines expecting tuple."""
        info = await ManagerService.resolve_manager_for_vertical(vertical)
        if info is None:
            return None
        return (
            uuid.UUID(info["user_id"]),
            int(info["telegram_id"]),
            info["display_name"],
        )

    @staticmethod
    async def is_super_admin(telegram_id: int) -> bool:
        if OWNER_ID is not None and telegram_id == OWNER_ID:
            return True
        async with get_session() as session:
            user = await UserRepository(session).get_by_telegram_id(telegram_id)
            if user is None:
                return False
            roles = await UserRepository(session).list_role_codes(user.id)
            return bool(
                {SystemRole.SUPER_ADMIN.value, "OWNER", "ADMIN"} & set(roles)
                or user.role in NON_ASSIGNABLE_ROLES
            )

    @staticmethod
    async def list_vertical_managers(vertical: str) -> list[dict[str, Any]]:
        key = normalize_vertical(vertical) or vertical.strip().lower()
        async with get_session() as session:
            rows = await ManagerRepository(session).list_subscribers(key)
            return [
                ManagerRepository.manager_snapshot(user, sub)
                for sub, user in rows
            ]


manager_service = ManagerService()
