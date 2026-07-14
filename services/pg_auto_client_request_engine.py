# Auto Client request engine — create, assign AUTO_MANAGER, notify.

from __future__ import annotations

import logging
import uuid
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from config import BOT_TOKEN
from database.models.auto_client_request import (
    AutoClientRequestStatus,
    AutoClientRequestType,
)
from database.models.role import Role
from database.session import get_session
from repositories.auto_client_request_repository import AutoClientRequestRepository
from repositories.user_role_repository import UserRoleRepository
from repositories.users_repository import UsersRepository
from services.pg_auto_dealer_manager_engine import (
    BORIS_FULL_NAME,
    BORIS_TELEGRAM_ID,
    BORIS_USERNAME,
)

logger = logging.getLogger(__name__)

AUTO_MANAGER_ROLE_CODE = "AUTO_MANAGER"

FLOW_TYPE_TO_DB: dict[str, str] = {
    "buy_car": AutoClientRequestType.AUTO_SEARCH.value,
    "sell_car": AutoClientRequestType.AUTO_SELL.value,
    "listing": AutoClientRequestType.AUTO_LISTING.value,
    "manager_callback": AutoClientRequestType.AUTO_MANAGER_CALLBACK.value,
}

MANAGER_NOTIFICATION_TITLES: dict[str, str] = {
    AutoClientRequestType.AUTO_SEARCH.value: "🚗 Новая заявка на поиск автомобиля",
    AutoClientRequestType.AUTO_SELL.value: "💰 Новая заявка на продажу автомобиля",
    AutoClientRequestType.AUTO_LISTING.value: "📢 Новое объявление от клиента",
    AutoClientRequestType.AUTO_MANAGER_CALLBACK.value: "📞 Клиент запросил менеджера",
}


class AutoClientRequestEngineV1:
    @staticmethod
    async def ensure_auto_manager() -> uuid.UUID | None:
        """Provision Boris with permission-engine role AUTO_MANAGER."""
        try:
            async with get_session() as session:
                users = UsersRepository(session)
                roles = UserRoleRepository(session)

                manager = await users.ensure_user(
                    telegram_id=BORIS_TELEGRAM_ID,
                    username=BORIS_USERNAME,
                    full_name=BORIS_FULL_NAME,
                    is_active=True,
                )

                role = await roles.get_role_by_code(AUTO_MANAGER_ROLE_CODE)
                if role is None:
                    role = Role(
                        code=AUTO_MANAGER_ROLE_CODE,
                        name="Auto Manager",
                        description="Automotive operations manager",
                    )
                    session.add(role)
                    await session.flush()

                await roles.assign_role_by_code(manager.id, AUTO_MANAGER_ROLE_CODE)
                logger.info(
                    "AUTO_MANAGER ensured user_id=%s telegram_id=%s",
                    manager.id,
                    BORIS_TELEGRAM_ID,
                )
                return manager.id
        except Exception:
            logger.exception("Failed to ensure AUTO_MANAGER")
            return None

    @staticmethod
    async def find_auto_manager() -> tuple[uuid.UUID, int, str] | None:
        """Return (user_uuid, telegram_id, display_name)."""
        await AutoClientRequestEngineV1.ensure_auto_manager()

        async with get_session() as session:
            manager = await UserRoleRepository(session).find_user_by_role_code(
                AUTO_MANAGER_ROLE_CODE
            )
            if manager is None:
                manager = await UsersRepository(session).get_by_telegram_id(
                    BORIS_TELEGRAM_ID
                )
            if manager is None or manager.telegram_id is None:
                logger.error("AUTO_MANAGER NOT FOUND")
                return None

            display = manager.full_name or BORIS_FULL_NAME
            logger.info(f"MANAGER FOUND {manager.id}")
            return manager.id, manager.telegram_id, display

    @staticmethod
    async def _next_request_number(session) -> str:
        repo = AutoClientRequestRepository(session)
        return f"AUTO-{await repo.count_all() + 1:04d}"

    @staticmethod
    async def submit(
        *,
        flow_request_type: str,
        client_telegram_id: int,
        client_username: str | None = None,
        client_full_name: str | None = None,
        description: str | None = None,
        photo_file_id: str | None = None,
    ) -> dict[str, Any]:
        db_type = FLOW_TYPE_TO_DB.get(
            flow_request_type,
            AutoClientRequestType.AUTO_SEARCH.value,
        )

        manager_info = await AutoClientRequestEngineV1.find_auto_manager()
        if manager_info is None:
            raise RuntimeError("AUTO_MANAGER NOT FOUND")

        manager_uuid, manager_telegram_id, manager_name = manager_info

        async with get_session() as session:
            request_number = await AutoClientRequestEngineV1._next_request_number(session)
            row = await AutoClientRequestRepository(session).create(
                request_number=request_number,
                request_type=db_type,
                status=AutoClientRequestStatus.NEW.value,
                client_telegram_id=client_telegram_id,
                client_username=client_username,
                client_full_name=client_full_name,
                description=description,
                photo_file_id=photo_file_id,
                manager_id=manager_uuid,
            )
            request_id = row.id
            created_number = row.request_number

        logger.info(f"REQUEST CREATED {request_id}")

        await AutoClientRequestEngineV1._notify_manager(
            manager_telegram_id=manager_telegram_id,
            request_type=db_type,
            request_number=created_number,
            client_username=client_username,
            client_full_name=client_full_name,
            description=description,
            photo_file_id=photo_file_id,
        )

        return {
            "id": str(request_id),
            "request_number": created_number,
            "request_type": db_type,
            "manager_id": str(manager_uuid),
            "manager_name": manager_name,
            "manager_telegram_id": manager_telegram_id,
        }

    @staticmethod
    async def _notify_manager(
        *,
        manager_telegram_id: int,
        request_type: str,
        request_number: str,
        client_username: str | None,
        client_full_name: str | None,
        description: str | None,
        photo_file_id: str | None,
    ) -> None:
        if not BOT_TOKEN:
            logger.error("SEND MESSAGE FAILED: BOT_TOKEN missing")
            return

        title = MANAGER_NOTIFICATION_TITLES.get(
            request_type,
            "🔔 Новая заявка Auto Client",
        )
        client_ref = f"@{client_username}" if client_username else (client_full_name or "—")
        lines = [
            title,
            "",
            "Клиент:",
            client_ref,
        ]
        if description:
            lines.extend(["", "Запрос:", description[:3500]])
        lines.extend(["", f"Заявка:", request_number])
        text = "\n".join(lines)

        bot = Bot(token=BOT_TOKEN)
        try:
            if photo_file_id:
                await bot.send_photo(
                    chat_id=manager_telegram_id,
                    photo=photo_file_id,
                    caption=text[:1024],
                )
                if len(text) > 1024:
                    await bot.send_message(chat_id=manager_telegram_id, text=text[1024:])
            else:
                await bot.send_message(chat_id=manager_telegram_id, text=text)
            logger.info("REQUEST SENT TO MANAGER")
        except TelegramForbiddenError:
            logger.error(
                "SEND MESSAGE FAILED: Forbidden — bot was blocked by the user "
                f"(manager_telegram_id={manager_telegram_id}). "
                "Manager must start the bot at least once."
            )
        except Exception:
            logger.exception("SEND MESSAGE FAILED")
        finally:
            await bot.session.close()
