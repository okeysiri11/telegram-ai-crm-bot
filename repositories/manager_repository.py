# Manager repository — vertical subscriptions and manager lookup.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.manager_vertical_subscription import ManagerVerticalSubscription
from database.models.users import User
from src.platform.layers.base_repository import BaseRepository


class ManagerRepository(BaseRepository):
    async def get_primary_for_vertical(
        self,
        vertical: str,
    ) -> tuple[ManagerVerticalSubscription, User] | None:
        result = await self.session.execute(
            select(ManagerVerticalSubscription, User)
            .join(User, User.id == ManagerVerticalSubscription.user_id)
            .where(
                ManagerVerticalSubscription.vertical == vertical,
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
        if row is None:
            return None
        return row[0], row[1]

    async def list_subscribers(self, vertical: str) -> list[tuple[ManagerVerticalSubscription, User]]:
        result = await self.session.execute(
            select(ManagerVerticalSubscription, User)
            .join(User, User.id == ManagerVerticalSubscription.user_id)
            .where(
                ManagerVerticalSubscription.vertical == vertical,
                ManagerVerticalSubscription.is_active.is_(True),
                User.is_active.is_(True),
            )
            .order_by(ManagerVerticalSubscription.is_primary.desc())
        )
        return list(result.all())

    async def upsert_subscription(
        self,
        *,
        user_id: uuid.UUID,
        telegram_user_id: int,
        vertical: str,
        role_code: str,
        is_primary: bool = True,
    ) -> ManagerVerticalSubscription:
        existing = (
            await self.session.execute(
                select(ManagerVerticalSubscription).where(
                    ManagerVerticalSubscription.user_id == user_id,
                    ManagerVerticalSubscription.vertical == vertical,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            existing.is_active = True
            existing.role_code = role_code
            existing.is_primary = is_primary
            existing.telegram_user_id = telegram_user_id
            await self.session.flush()
            return existing

        row = ManagerVerticalSubscription(
            user_id=user_id,
            telegram_user_id=telegram_user_id,
            vertical=vertical,
            role_code=role_code,
            is_active=True,
            is_primary=is_primary,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    @staticmethod
    def manager_snapshot(user: User, sub: ManagerVerticalSubscription | None = None) -> dict[str, Any]:
        return {
            "user_id": str(user.id),
            "telegram_id": user.telegram_id,
            "display_name": user.full_name or user.username or str(user.telegram_id),
            "username": user.username,
            "role_code": sub.role_code if sub else user.role,
            "vertical": sub.vertical if sub else None,
        }
