# User vertical preferences repository.

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user_vertical_preferences import UserVerticalPreferences


class UserVerticalPreferencesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_user_id: int) -> UserVerticalPreferences | None:
        result = await self._session.execute(
            select(UserVerticalPreferences).where(
                UserVerticalPreferences.telegram_user_id == telegram_user_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        telegram_user_id: int,
        vertical: str | None = None,
        tenant_code: str | None = None,
        source_link: str | None = None,
        language: str | None = None,
        role: str | None = None,
        onboarding_step: str | None = None,
        onboarding_completed: bool | None = None,
    ) -> UserVerticalPreferences:
        row = await self.get_by_telegram_id(telegram_user_id)
        if row is None:
            row = UserVerticalPreferences(
                telegram_user_id=telegram_user_id,
                vertical=vertical,
                tenant_code=tenant_code,
                source_link=source_link,
                language=language or "ru",
                role=role,
                onboarding_step=onboarding_step,
                onboarding_completed=onboarding_completed or False,
            )
            self._session.add(row)
        else:
            if vertical is not None:
                row.vertical = vertical
            if tenant_code is not None:
                row.tenant_code = tenant_code
            if source_link is not None:
                row.source_link = source_link
            if language is not None:
                row.language = language
            if role is not None:
                row.role = role
            if onboarding_step is not None:
                row.onboarding_step = onboarding_step
            if onboarding_completed is not None:
                row.onboarding_completed = onboarding_completed
        await self._session.flush()
        return row
