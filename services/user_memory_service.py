"""User memory service — canonical get_user_profile / save_profile_fields API.

Replaces SQLite ``database_legacy`` user_memory helpers under POSTGRES_ONLY.
"""

from __future__ import annotations

from typing import Any

from database.session import get_session
from repositories.user_memory_repository import UserMemoryRepository

# Original MEMORY_FIELDS from database_legacy.get_user_profile
MEMORY_FIELDS: dict[str, str] = {
    "name": "Имя",
    "company": "Компания",
    "city": "Город",
    "country": "Страна",
    "activity": "Сфера деятельности",
    "interests": "Интересы",
}


class UserMemoryService:
    """PostgreSQL-backed Telegram user profile memory."""

    @staticmethod
    async def load_memory(telegram_id: int) -> dict[str, str]:
        async with get_session() as session:
            rows = await UserMemoryRepository(session).list_by_telegram(telegram_id)
            return {row.memory_key: row.memory_value for row in rows if row.memory_value}

    @staticmethod
    async def get_memory(telegram_id: int, key: str) -> str | None:
        async with get_session() as session:
            row = await UserMemoryRepository(session).get(telegram_id, key)
            return row.memory_value if row else None

    @staticmethod
    async def save_memory(telegram_id: int, key: str, value: str) -> None:
        async with get_session() as session:
            await UserMemoryRepository(session).upsert(telegram_id, key, str(value))

    @staticmethod
    async def get_user_profile(telegram_id: int) -> dict[str, str]:
        profile = await UserMemoryService.load_memory(telegram_id)
        return {key: profile[key] for key in MEMORY_FIELDS if key in profile and profile[key]}

    @staticmethod
    async def save_profile_fields(telegram_id: int, fields: dict[str, Any]) -> None:
        async with get_session() as session:
            repo = UserMemoryRepository(session)
            for key, value in fields.items():
                if key not in MEMORY_FIELDS:
                    continue
                if value and str(value).strip():
                    await repo.upsert(telegram_id, key, str(value).strip())

    @staticmethod
    async def format_memory_text(telegram_id: int) -> str:
        memory = await UserMemoryService.load_memory(telegram_id)
        if not memory:
            return "🧠 Память пуста. AI запомнит данные из будущих диалогов."
        lines = ["🧠 Моя память:\n"]
        for key, value in memory.items():
            label = MEMORY_FIELDS.get(key, key)
            lines.append(f"• {label}: {value}")
        return "\n".join(lines)

    @staticmethod
    async def format_memory_context(telegram_id: int) -> str:
        profile = await UserMemoryService.get_user_profile(telegram_id)
        if not profile:
            return ""
        lines = [f"- {MEMORY_FIELDS[key]}: {value}" for key, value in profile.items()]
        return "Известная информация о пользователе:\n" + "\n".join(lines)

    @staticmethod
    async def format_profile_text(telegram_id: int) -> str:
        profile = await UserMemoryService.get_user_profile(telegram_id)
        if not profile:
            return "Профиль пока пуст. AI запомнит данные из диалога."
        lines = [f"• {MEMORY_FIELDS[key]}: {value}" for key, value in profile.items()]
        return "👤 Ваш профиль:\n\n" + "\n".join(lines)


user_memory_service = UserMemoryService()


def _sync(coro):
    """Run async SoR from sync scripts/tests (no running event loop)."""
    import asyncio

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # Shared AsyncEngine may be bound to a previous closed loop — recreate.
        import database.engine as eng
        import database.session as sess

        eng._engine = None
        sess._session_factory = None
        return asyncio.run(coro)

    raise RuntimeError(
        "Sync user-memory helpers cannot run inside an active event loop. "
        "Await UserMemoryService async methods instead "
        "(e.g. await UserMemoryService.get_user_profile(user_id))."
    )


def load_memory(user_id: int) -> dict:
    return _sync(UserMemoryService.load_memory(user_id)) or {}


def get_memory(user_id: int, key: str):
    return _sync(UserMemoryService.get_memory(user_id, key))


def save_memory(user_id: int, key: str, value: str) -> None:
    _sync(UserMemoryService.save_memory(user_id, key, value))


def get_user_profile(user_id: int) -> dict:
    return _sync(UserMemoryService.get_user_profile(user_id)) or {}


def save_profile_fields(user_id: int, fields: dict) -> None:
    _sync(UserMemoryService.save_profile_fields(user_id, fields))


def format_memory_text(user_id: int) -> str:
    result = _sync(UserMemoryService.format_memory_text(user_id))
    return result if isinstance(result, str) else "🧠 Память пуста. AI запомнит данные из будущих диалогов."


def format_memory_context(user_id: int) -> str:
    result = _sync(UserMemoryService.format_memory_context(user_id))
    return result if isinstance(result, str) else ""


def format_profile_text(user_id: int) -> str:
    result = _sync(UserMemoryService.format_profile_text(user_id))
    return result if isinstance(result, str) else "Профиль пока пуст. AI запомнит данные из диалога."
