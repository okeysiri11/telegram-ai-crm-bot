# ManagerService — vertical lead routing via smart assignment engine.

from __future__ import annotations

import logging
import uuid
from typing import Any

from config import OWNER_ID
from database.session import get_session
from repositories.manager_repository import ManagerRepository
from repositories.user_repository import UserRepository
from services.smart_assignment_service import smart_assignment_service
from services.system_roles import SystemRole, Vertical, normalize_vertical

logger = logging.getLogger(__name__)

NON_ASSIGNABLE_ROLES = frozenset({SystemRole.SUPER_ADMIN.value, "OWNER", "ADMIN"})


class ManagerService:
    @staticmethod
    async def resolve_manual_manager(telegram_id: int) -> dict[str, Any] | None:
        async with get_session() as session:
            user = await UserRepository(session).get_by_telegram_id(int(telegram_id))
            if user is None:
                return None
            return ManagerRepository.manager_snapshot(user)

    @staticmethod
    async def resolve_manager_for_vertical(
        vertical: str,
        *,
        request_type: str | None = None,
        request_id: str | None = None,
        request_number: str | None = None,
    ) -> dict[str, Any] | None:
        """Resolve primary manager via SmartAssignmentService pipeline."""
        key = normalize_vertical(vertical) or vertical.strip().lower()
        mgr = await smart_assignment_service.assign_for_request(
            vertical=key,
            request_type=request_type,
            request_id=request_id,
            request_number=request_number,
        )
        if mgr is not None:
            return mgr

        logger.warning("No manager available for vertical=%s", key)
        return None

    @staticmethod
    async def resolve_manager_triple(
        vertical: str,
        *,
        request_type: str | None = None,
    ) -> tuple[uuid.UUID, int, str] | None:
        """Return (user_uuid, telegram_id, display_name) for engines expecting tuple."""
        info = await ManagerService.resolve_manager_for_vertical(
            vertical,
            request_type=request_type,
        )
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

    @staticmethod
    async def resolve_alternate_manager_for_vertical(
        vertical: str,
        *,
        exclude_manager_id: uuid.UUID | str | None = None,
        request_type: str | None = None,
    ) -> dict[str, Any] | None:
        """Pick another manager for the vertical, excluding the current assignee."""
        key = normalize_vertical(vertical) or vertical.strip().lower()
        exclude_tid: set[int] = set()
        if exclude_manager_id:
            async with get_session() as session:
                user = await UserRepository(session).get_by_id(
                    uuid.UUID(str(exclude_manager_id))
                )
                if user and user.telegram_id is not None:
                    exclude_tid.add(int(user.telegram_id))

        return await smart_assignment_service.assign_for_request(
            vertical=key,
            request_type=request_type,
            exclude_telegram_ids=exclude_tid or None,
        )


manager_service = ManagerService()
