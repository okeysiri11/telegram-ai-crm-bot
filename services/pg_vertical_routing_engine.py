# Vertical CRM routing — assign leads to managers by subscription / role.

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select

from config import (
    DEFAULT_AGRO_MANAGER_ID,
    DEFAULT_AUTO_MANAGER_ID,
    OWNER_ID,
)
from database.models.manager_vertical_subscription import ManagerVerticalSubscription
from database.models.users import User
from database.session import get_session
from services.system_roles import (
    ROLE_DEFAULT_VERTICALS,
    SystemRole,
    Vertical,
    normalize_vertical,
)

logger = logging.getLogger(__name__)


class VerticalRoutingEngineV1:
    """Resolve managers for a vertical without changing client FSM flows."""

    @staticmethod
    async def ensure_platform_actors() -> dict[str, Any]:
        """Seed SUPER_ADMIN / AUTO_MANAGER / AGRO_MANAGER users + subscriptions."""
        from repositories.user_role_repository import UserRoleRepository
        from repositories.users_repository import UsersRepository
        from database.models.role import PermissionRole

        seeded: dict[str, Any] = {"users": [], "subscriptions": []}

        actors = [
            (
                OWNER_ID,
                SystemRole.SUPER_ADMIN.value,
                "Ton",
                None,
                ROLE_DEFAULT_VERTICALS[SystemRole.SUPER_ADMIN.value],
            ),
            (
                DEFAULT_AUTO_MANAGER_ID,
                SystemRole.AUTO_MANAGER.value,
                "Борода",
                "Boroda_0003",
                ROLE_DEFAULT_VERTICALS[SystemRole.AUTO_MANAGER.value],
            ),
            (
                DEFAULT_AGRO_MANAGER_ID,
                SystemRole.AGRO_MANAGER.value,
                "Christopher Moltisanti",
                None,
                ROLE_DEFAULT_VERTICALS[SystemRole.AGRO_MANAGER.value],
            ),
        ]

        async with get_session() as session:
            users = UsersRepository(session)
            roles = UserRoleRepository(session)

            for telegram_id, role_code, full_name, username, verticals in actors:
                if telegram_id is None:
                    continue
                user = await users.ensure_user(
                    telegram_id=telegram_id,
                    username=username,
                    full_name=full_name,
                    is_active=True,
                )
                user.role = role_code
                user.verticals = list(verticals)
                seeded["users"].append(
                    {"telegram_id": telegram_id, "role": role_code, "verticals": list(verticals)}
                )

                role = await roles.get_role_by_code(role_code)
                if role is None:
                    role = PermissionRole(
                        code=role_code,
                        name=role_code.replace("_", " ").title(),
                        description=f"System role {role_code}",
                    )
                    session.add(role)
                    await session.flush()
                # SUPER_ADMIN also keeps OWNER for legacy gates
                await roles.assign_role_by_code(user.id, role_code)
                if role_code == SystemRole.SUPER_ADMIN.value:
                    await roles.assign_role_by_code(user.id, "OWNER")

                for vertical in verticals:
                    if role_code == SystemRole.SUPER_ADMIN.value:
                        # Super admin sees all but is not a lead assignee by default.
                        continue
                    existing = (
                        await session.execute(
                            select(ManagerVerticalSubscription).where(
                                ManagerVerticalSubscription.user_id == user.id,
                                ManagerVerticalSubscription.vertical == vertical,
                            )
                        )
                    ).scalar_one_or_none()
                    if existing is None:
                        session.add(
                            ManagerVerticalSubscription(
                                user_id=user.id,
                                telegram_user_id=telegram_id,
                                vertical=vertical,
                                role_code=role_code,
                                is_active=True,
                                is_primary=True,
                            )
                        )
                        seeded["subscriptions"].append(
                            {"telegram_id": telegram_id, "vertical": vertical}
                        )
                    else:
                        existing.is_active = True
                        existing.role_code = role_code

        logger.info("Vertical routing actors seeded: %s", seeded)
        return seeded

    @staticmethod
    async def resolve_manager_for_vertical(
        vertical: str | None,
    ) -> tuple[uuid.UUID, int, str] | None:
        """
        Return (user_uuid, telegram_id, display_name) for the primary manager
        subscribed to the vertical.
        """
        key = normalize_vertical(vertical) or (vertical or "").strip().lower()
        if not key:
            return None

        async with get_session() as session:
            result = await session.execute(
                select(ManagerVerticalSubscription, User)
                .join(User, User.id == ManagerVerticalSubscription.user_id)
                .where(
                    ManagerVerticalSubscription.vertical == key,
                    ManagerVerticalSubscription.is_active.is_(True),
                    User.is_active.is_(True),
                )
                .order_by(
                    ManagerVerticalSubscription.is_primary.desc(),
                    ManagerVerticalSubscription.created_at.asc(),
                )
                .limit(1)
            )
            row = result.first()
            if row is not None:
                sub, user = row
                name = user.full_name or user.username or f"manager:{user.telegram_id}"
                if user.telegram_id is None:
                    return None
                logger.info(
                    "VERTICAL_ROUTE vertical=%s manager_telegram_id=%s role=%s",
                    key,
                    user.telegram_id,
                    sub.role_code,
                )
                return user.id, user.telegram_id, name

        # Config fallbacks — keep AUTO scenarios working before subscriptions exist
        if key == Vertical.AUTO.value and DEFAULT_AUTO_MANAGER_ID is not None:
            return await VerticalRoutingEngineV1._fallback_user(DEFAULT_AUTO_MANAGER_ID)
        if key == Vertical.AGRO.value and DEFAULT_AGRO_MANAGER_ID is not None:
            return await VerticalRoutingEngineV1._fallback_user(DEFAULT_AGRO_MANAGER_ID)
        return None

    @staticmethod
    async def _fallback_user(telegram_id: int) -> tuple[uuid.UUID, int, str] | None:
        async with get_session() as session:
            from repositories.users_repository import UsersRepository

            user = await UsersRepository(session).get_by_telegram_id(telegram_id)
            if user is None or user.telegram_id is None:
                return None
            return user.id, user.telegram_id, user.full_name or user.username or str(telegram_id)

    @staticmethod
    async def list_managers_for_vertical(vertical: str) -> list[dict[str, Any]]:
        key = normalize_vertical(vertical) or vertical.strip().lower()
        async with get_session() as session:
            result = await session.execute(
                select(ManagerVerticalSubscription, User)
                .join(User, User.id == ManagerVerticalSubscription.user_id)
                .where(
                    ManagerVerticalSubscription.vertical == key,
                    ManagerVerticalSubscription.is_active.is_(True),
                )
                .order_by(ManagerVerticalSubscription.is_primary.desc())
            )
            out: list[dict[str, Any]] = []
            for sub, user in result.all():
                out.append(
                    {
                        "user_id": str(user.id),
                        "telegram_user_id": user.telegram_id,
                        "full_name": user.full_name,
                        "role": user.role or sub.role_code,
                        "vertical": sub.vertical,
                        "is_primary": sub.is_primary,
                    }
                )
            return out

    @staticmethod
    async def resolve_system_role(telegram_user_id: int) -> str | None:
        async with get_session() as session:
            from repositories.users_repository import UsersRepository

            user = await UsersRepository(session).get_by_telegram_id(telegram_user_id)
            if user is not None and user.role:
                return user.role
        if OWNER_ID is not None and telegram_user_id == OWNER_ID:
            return SystemRole.SUPER_ADMIN.value
        if DEFAULT_AUTO_MANAGER_ID is not None and telegram_user_id == DEFAULT_AUTO_MANAGER_ID:
            return SystemRole.AUTO_MANAGER.value
        if DEFAULT_AGRO_MANAGER_ID is not None and telegram_user_id == DEFAULT_AGRO_MANAGER_ID:
            return SystemRole.AGRO_MANAGER.value
        return SystemRole.CLIENT.value
