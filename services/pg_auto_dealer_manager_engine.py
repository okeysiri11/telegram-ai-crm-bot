# Auto dealer default manager — Boris provisioning and lead assignment.

from __future__ import annotations

import logging
import uuid
from typing import Any

from database.models.roles import RbacRole
from database.session import get_session
from repositories.rbac_repository import RbacRepository
from repositories.users_repository import UsersRepository
from services.pg_lead_engine import LeadEngineV1

logger = logging.getLogger(__name__)

BORIS_TELEGRAM_ID = 393792086
BORIS_USERNAME = "Boroda_0003"
BORIS_FULL_NAME = "Борис"
BORIS_ROLE_CODE = "manager"
BORIS_ROLE_NAME = "Manager"
BORIS_ROLE_DESCRIPTION = "CRM manager"


class AutoDealerManagerEngineV1:
    @staticmethod
    def is_auto_dealer_lead(*, source_link: str | None, vertical: str | None) -> bool:
        if source_link in {"auto_dealer", "auto_client"}:
            return True
        return vertical in {"automotive", "auto"}

    @staticmethod
    async def ensure_default_manager() -> uuid.UUID | None:
        try:
            async with get_session() as session:
                user = await UsersRepository(session).ensure_user(
                    telegram_id=BORIS_TELEGRAM_ID,
                    username=BORIS_USERNAME,
                    full_name=BORIS_FULL_NAME,
                    is_active=True,
                )
                rbac = RbacRepository(session)
                role = await rbac.get_role_by_code(BORIS_ROLE_CODE)
                if role is None:
                    role = RbacRole(
                        code=BORIS_ROLE_CODE,
                        name=BORIS_ROLE_NAME,
                        description=BORIS_ROLE_DESCRIPTION,
                    )
                    session.add(role)
                    await session.flush()
                await rbac.assign_role(user.id, BORIS_ROLE_CODE)
                return user.id
        except Exception:
            logger.warning(
                "Auto dealer manager provisioning failed for telegram_id=%s",
                BORIS_TELEGRAM_ID,
                exc_info=True,
            )
            return None

    @staticmethod
    async def resolve_manager_uuid() -> uuid.UUID | None:
        async with get_session() as session:
            user = await UsersRepository(session).get_by_telegram_id(BORIS_TELEGRAM_ID)
            if user is None:
                return None
            return user.id

    @staticmethod
    async def auto_assign_dealer_lead(snapshot: dict[str, Any]) -> dict[str, Any] | None:
        if not AutoDealerManagerEngineV1.is_auto_dealer_lead(
            source_link=snapshot.get("source_link"),
            vertical=snapshot.get("vertical"),
        ):
            return None

        if snapshot.get("assigned_manager_id"):
            return None

        manager_uuid = await AutoDealerManagerEngineV1.ensure_default_manager()
        if manager_uuid is None:
            manager_uuid = await AutoDealerManagerEngineV1.resolve_manager_uuid()
        if manager_uuid is None:
            logger.warning(
                "AUTO DEALER: manager missing in system telegram_id=%s — lead=%s not assigned",
                BORIS_TELEGRAM_ID,
                snapshot.get("id"),
            )
            return None

        try:
            lead_id = uuid.UUID(str(snapshot["id"]))
        except (KeyError, TypeError, ValueError):
            logger.warning(
                "AUTO DEALER: invalid lead id in snapshot — assignment skipped: %s",
                snapshot.get("id"),
            )
            return None

        try:
            result = await LeadEngineV1.assign_manager(lead_id, manager_uuid)
        except Exception:
            logger.warning(
                "AUTO DEALER: assign_manager failed lead=%s manager=%s",
                lead_id,
                manager_uuid,
                exc_info=True,
            )
            return None

        if result is None:
            logger.warning(
                "AUTO DEALER: assign_manager returned None lead=%s manager=%s",
                lead_id,
                manager_uuid,
            )
            return None

        logger.info(
            "AUTO DEALER:\nlead=%s\nassigned_manager=%s\nmanager_name=%s",
            lead_id,
            manager_uuid,
            BORIS_FULL_NAME,
        )
        return result

    @staticmethod
    def request_type_label(request_type: str | None) -> str:
        labels = {
            "buy_car": "🚗 Поиск автомобиля",
            "sell_car": "💰 Продажа автомобиля",
            "listing": "📢 Размещение объявления",
            "manager_callback": "📞 Связаться с менеджером",
        }
        return labels.get(request_type or "", request_type or "—")

    @staticmethod
    async def notify_manager_for_lead(snapshot: dict[str, Any]) -> None:
        from aiogram import Bot

        from config import BOT_TOKEN

        if not BOT_TOKEN:
            return

        request_type = snapshot.get("client_request_type")
        description = (snapshot.get("client_description") or "").strip()
        photo_file_id = snapshot.get("client_photo_file_id")
        username = snapshot.get("telegram_username")
        full_name = snapshot.get("full_name")
        telegram_user_id = snapshot.get("telegram_user_id")
        lead_id = snapshot.get("id")

        client_line = full_name or "—"
        if username:
            client_line = f"{client_line} (@{username})"
        if telegram_user_id:
            client_line = f"{client_line} [id: {telegram_user_id}]"

        label = AutoDealerManagerEngineV1.request_type_label(request_type)
        text_lines = [
            "🔔 Новая заявка — Auto Client",
            "",
            f"Тип: {label}",
            f"Клиент: {client_line}",
            f"Lead: {lead_id}",
        ]
        if description:
            text_lines.extend(["", "Описание:", description[:3500]])
        text = "\n".join(text_lines)

        bot = Bot(token=BOT_TOKEN)
        try:
            if photo_file_id:
                caption = text[:1024]
                await bot.send_photo(
                    chat_id=BORIS_TELEGRAM_ID,
                    photo=photo_file_id,
                    caption=caption,
                )
                if len(text) > 1024:
                    await bot.send_message(chat_id=BORIS_TELEGRAM_ID, text=text[1024:])
            else:
                await bot.send_message(chat_id=BORIS_TELEGRAM_ID, text=text)
        except Exception:
            logger.exception(
                "Failed to notify manager telegram_id=%s for lead=%s",
                BORIS_TELEGRAM_ID,
                lead_id,
            )
        finally:
            await bot.session.close()
