# Manager delivery — lead assignment, Telegram notifications, diagnostics.

from __future__ import annotations

import logging
import uuid
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import BOT_TOKEN, DEFAULT_AUTO_MANAGER_ID, DEFAULT_DEALER_MANAGER_ID
from database.session import get_session
from repositories.rbac_repository import RbacRepository
from repositories.user_role_repository import UserRoleRepository
from repositories.users_repository import UsersRepository
from services.pg_auto_dealer_manager_engine import (
    BORIS_FULL_NAME,
    BORIS_USERNAME,
)

logger = logging.getLogger(__name__)

MANAGER_ROLE_CODES = frozenset({
    "AUTO_MANAGER",
    "manager",
    "sales_manager",
    "MANAGER",
    "SUPER_MANAGER",
})


class ManagerDeliveryEngineV1:
    @staticmethod
    async def ensure_boris() -> uuid.UUID | None:
        from services.pg_auto_client_request_engine import AutoClientRequestEngineV1
        from services.pg_auto_dealer_manager_engine import AutoDealerManagerEngineV1

        auto_mgr = await AutoClientRequestEngineV1.ensure_auto_manager()
        rbac_mgr = await AutoDealerManagerEngineV1.ensure_default_manager()
        return auto_mgr or rbac_mgr

    @staticmethod
    async def get_manager_user(*, telegram_id: int | None = None) -> Any | None:
        tid = telegram_id or DEFAULT_AUTO_MANAGER_ID
        if tid is None:
            return None
        async with get_session() as session:
            return await UsersRepository(session).get_by_telegram_id(tid)

    @staticmethod
    async def list_role_codes_for_user(user_id: uuid.UUID) -> list[str]:
        codes: set[str] = set()
        async with get_session() as session:
            for role in await UserRoleRepository(session).get_user_roles(user_id):
                codes.add(role.code)
            from sqlalchemy import select
            from database.models.roles import RbacRole, UserRoleLink

            result = await session.execute(
                select(RbacRole.code)
                .join(UserRoleLink, UserRoleLink.role_id == RbacRole.id)
                .where(UserRoleLink.user_id == user_id)
            )
            codes.update(row[0] for row in result.all())
        return sorted(codes)

    @staticmethod
    async def is_platform_manager(telegram_user_id: int) -> bool:
        if DEFAULT_AUTO_MANAGER_ID is not None and telegram_user_id == DEFAULT_AUTO_MANAGER_ID:
            return True
        if DEFAULT_DEALER_MANAGER_ID is not None and telegram_user_id == DEFAULT_DEALER_MANAGER_ID:
            return True
        user = await ManagerDeliveryEngineV1.get_manager_user(telegram_id=telegram_user_id)
        if user is None:
            return False
        roles = await ManagerDeliveryEngineV1.list_role_codes_for_user(user.id)
        return bool(set(roles) & MANAGER_ROLE_CODES)

    @staticmethod
    async def resolve_default_manager() -> tuple[uuid.UUID, int, str] | None:
        await ManagerDeliveryEngineV1.ensure_boris()
        if DEFAULT_AUTO_MANAGER_ID is None:
            logger.error("DEFAULT_AUTO_MANAGER_ID is not configured")
            return None
        user = await ManagerDeliveryEngineV1.get_manager_user(telegram_id=DEFAULT_AUTO_MANAGER_ID)
        if user is None or user.telegram_id is None:
            logger.error("MANAGER_NOT_FOUND lead_id=%s", "—")
            return None
        name = user.full_name or BORIS_FULL_NAME
        return user.id, user.telegram_id, name

    @staticmethod
    async def startup_diagnostics() -> dict[str, Any]:
        await ManagerDeliveryEngineV1.ensure_boris()
        if DEFAULT_AUTO_MANAGER_ID is None:
            logger.warning("DEFAULT_AUTO_MANAGER_ID is not configured — manager diagnostics limited")
            manager = None
        else:
            manager = await ManagerDeliveryEngineV1.get_manager_user(
                telegram_id=DEFAULT_AUTO_MANAGER_ID,
            )
        logger.info(
            "MANAGER_CHECK exists=%s username=%s user_id=%s",
            bool(manager),
            manager.username if manager else None,
            manager.id if manager else None,
        )
        roles: list[str] = []
        if manager is not None:
            roles = await ManagerDeliveryEngineV1.list_role_codes_for_user(manager.id)
        logger.info("MANAGER_ROLES %s", roles)

        assigned_leads = 0
        assigned_requests = 0
        if manager is not None:
            from sqlalchemy import func, select
            from database.models.lead_engine import LeadEngineLead

            try:
                async with get_session() as session:
                    lead_count = await session.execute(
                        select(func.count())
                        .select_from(LeadEngineLead)
                        .where(LeadEngineLead.assigned_manager_id == manager.id)
                    )
                    assigned_leads = int(lead_count.scalar_one())
                    try:
                        from database.models.auto_client_request import AutoClientRequest

                        req_count = await session.execute(
                            select(func.count())
                            .select_from(AutoClientRequest)
                            .where(AutoClientRequest.manager_id == manager.id)
                        )
                        assigned_requests = int(req_count.scalar_one())
                    except Exception:
                        logger.warning(
                            "auto_client_requests_v1 unavailable — run alembic upgrade head",
                            exc_info=True,
                        )
            except Exception:
                logger.warning("Lead count diagnostics failed", exc_info=True)

        is_mgr = (
            await ManagerDeliveryEngineV1.is_platform_manager(DEFAULT_AUTO_MANAGER_ID)
            if DEFAULT_AUTO_MANAGER_ID is not None
            else False
        )
        menu_type = (
            await ManagerDeliveryEngineV1.resolve_menu_type(DEFAULT_AUTO_MANAGER_ID)
            if DEFAULT_AUTO_MANAGER_ID is not None
            else "default"
        )

        return {
            "telegram_id": DEFAULT_AUTO_MANAGER_ID,
            "internal_user_id": str(manager.id) if manager else None,
            "username": manager.username if manager else BORIS_USERNAME,
            "roles": roles,
            "is_manager": is_mgr,
            "assigned_leads_count": assigned_leads,
            "assigned_requests_count": assigned_requests,
            "menu_type": menu_type,
            "default_manager_enabled": manager is not None,
        }

    @staticmethod
    async def resolve_menu_type(telegram_user_id: int) -> str:
        from services.pg_entry_point_engine import EntryPointEngineV1
        from services.entry_point_routing import EntryPoint

        if await ManagerDeliveryEngineV1.is_platform_manager(telegram_user_id):
            menu_type = "manager_crm"
        else:
            ctx = await EntryPointEngineV1.get_flow_context(telegram_user_id)
            entry = ctx.get("entry_point")
            if entry == EntryPoint.AUTO_CLIENT.value:
                menu_type = "auto_client"
            elif entry == EntryPoint.AUTO_DEALER.value:
                menu_type = "auto_dealer"
            elif entry == EntryPoint.OWNER.value:
                menu_type = "owner"
            else:
                menu_type = "default"
        logger.info(
            "MENU_BUILD telegram_id=%s roles=%s menu_type=%s",
            telegram_user_id,
            await ManagerDeliveryEngineV1._role_codes_for_telegram(telegram_user_id),
            menu_type,
        )
        return menu_type

    @staticmethod
    async def _role_codes_for_telegram(telegram_user_id: int) -> list[str]:
        user = await ManagerDeliveryEngineV1.get_manager_user(telegram_id=telegram_user_id)
        if user is None:
            return []
        return await ManagerDeliveryEngineV1.list_role_codes_for_user(user.id)

    @staticmethod
    async def reply_markup_for_user(telegram_user_id: int):
        from keyboards import auto_client_menu, crm_menu, owner_dashboard_menu, owner_main_menu
        from services.automotive_telegram_access import can_see_automotive_menu_button
        from services.pg_entry_point_engine import EntryPointEngineV1
        from services.entry_point_routing import EntryPoint

        menu_type = await ManagerDeliveryEngineV1.resolve_menu_type(telegram_user_id)
        ctx = await EntryPointEngineV1.get_flow_context(telegram_user_id)
        lang = ctx.get("language") or "ru"

        if menu_type == "manager_crm":
            if ctx.get("entry_point") == EntryPoint.AUTO_CLIENT.value:
                logger.warning(
                    "WRONG_MENU_FOR_MANAGER telegram_id=%s",
                    telegram_user_id,
                )
            show_auto = await can_see_automotive_menu_button(telegram_user_id)
            return crm_menu() if not show_auto else owner_main_menu(show_automotive=True)

        if ctx.get("entry_point") == EntryPoint.AUTO_CLIENT.value:
            from keyboards import auto_client_menu as acm
            return acm(lang)
        if ctx.get("entry_point") == EntryPoint.OWNER.value:
            return owner_dashboard_menu()
        if ctx.get("entry_point") == EntryPoint.AUTO_DEALER.value:
            return await __import__(
                "dealer_onboarding_handlers", fromlist=["_main_menu_for"]
            )._main_menu_for(telegram_user_id)
        show_auto = await can_see_automotive_menu_button(telegram_user_id)
        return owner_main_menu(show_automotive=show_auto)

    @staticmethod
    async def assign_lead_manager(
        *,
        lead_id: uuid.UUID,
        snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        from services.pg_lead_engine import LeadEngineV1

        manager_info = await ManagerDeliveryEngineV1.resolve_default_manager()
        if manager_info is None:
            logger.error("MANAGER_NOT_FOUND lead_id=%s", lead_id)
            return snapshot

        manager_uuid, manager_telegram_id, manager_name = manager_info

        if snapshot.get("assigned_manager_id"):
            assigned_manager = await ManagerDeliveryEngineV1.get_manager_user(
                telegram_id=manager_telegram_id,
            )
            logger.info(
                "MANAGER_ASSIGNMENT lead_id=%s manager_id=%s manager_telegram_id=%s (already_assigned)",
                lead_id,
                assigned_manager.id if assigned_manager else manager_uuid,
                manager_telegram_id,
            )
            return snapshot

        result = await LeadEngineV1.assign_manager(lead_id, manager_uuid)
        if result is None:
            logger.error("MANAGER_NOT_FOUND lead_id=%s", lead_id)
            return snapshot

        assigned_manager = await ManagerDeliveryEngineV1.get_manager_user(
            telegram_id=manager_telegram_id,
        )
        logger.info(
            "MANAGER_ASSIGNMENT lead_id=%s manager_id=%s manager_telegram_id=%s",
            lead_id,
            assigned_manager.id if assigned_manager else manager_uuid,
            manager_telegram_id,
        )
        return result

    @staticmethod
    def lead_notification_keyboard(*, request_number: str | None = None, lead_id: str | None = None):
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

        buttons = []
        if request_number:
            buttons.append([
                InlineKeyboardButton(
                    text=f"📋 {request_number}",
                    callback_data=f"mgr:req:{request_number}",
                )
            ])
            buttons.append([
                InlineKeyboardButton(text="✅ Take", callback_data=f"mgr:take:{request_number}"),
                InlineKeyboardButton(text="🟡 In Progress", callback_data=f"mgr:status:{request_number}:IN_PROGRESS"),
            ])
            buttons.append([
                InlineKeyboardButton(text="✔ Complete", callback_data=f"mgr:status:{request_number}:COMPLETED"),
                InlineKeyboardButton(text="❌ Cancel", callback_data=f"mgr:status:{request_number}:CANCELLED"),
            ])
        elif lead_id:
            buttons.append([
                InlineKeyboardButton(
                    text="📋 Открыть лид",
                    callback_data=f"mgr:lead:{lead_id[:8]}",
                )
            ])
        if not buttons:
            return None
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def request_action_keyboard(request_number: str):
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Take Lead", callback_data=f"mgr:take:{request_number}"),
                    InlineKeyboardButton(text="📞 Call Client", callback_data=f"mgr:call:{request_number}"),
                ],
                [
                    InlineKeyboardButton(text="💬 Message", callback_data=f"mgr:msg:{request_number}"),
                    InlineKeyboardButton(text="🔄 Reassign", callback_data=f"mgr:reassign:{request_number}"),
                ],
                [
                    InlineKeyboardButton(text="✔ Complete", callback_data=f"mgr:status:{request_number}:COMPLETED"),
                    InlineKeyboardButton(text="❌ Cancel", callback_data=f"mgr:status:{request_number}:CANCELLED"),
                ],
                [
                    InlineKeyboardButton(text="🟡 In Progress", callback_data=f"mgr:status:{request_number}:IN_PROGRESS"),
                    InlineKeyboardButton(text="⏳ Waiting Client", callback_data=f"mgr:status:{request_number}:WAITING_CLIENT"),
                ],
            ]
        )

    @staticmethod
    async def send_to_manager(
        *,
        manager_telegram_id: int,
        text: str,
        lead_id: str | uuid.UUID | None = None,
        request_number: str | None = None,
        photo_file_id: str | None = None,
        photo_file_ids: list[str] | None = None,
    ) -> bool:
        if not BOT_TOKEN:
            logger.error(
                "SEND_TO_MANAGER_FAILED telegram_id=%s lead_id=%s reason=BOT_TOKEN_missing",
                manager_telegram_id,
                lead_id,
            )
            return False

        logger.info(
            "SEND_TO_MANAGER telegram_id=%s lead_id=%s request=%s",
            manager_telegram_id,
            lead_id,
            request_number,
        )

        markup = ManagerDeliveryEngineV1.lead_notification_keyboard(
            request_number=request_number,
            lead_id=str(lead_id) if lead_id else None,
        )

        bot = Bot(token=BOT_TOKEN)
        try:
            photos = list(photo_file_ids or [])
            if not photos and photo_file_id:
                photos = [photo_file_id]

            # Always send text first, then photos (spec: text → media group).
            await bot.send_message(
                chat_id=manager_telegram_id,
                text=text,
                reply_markup=markup,
            )

            if photos:
                from aiogram.types import InputMediaPhoto

                batch_size = 10
                for offset in range(0, len(photos), batch_size):
                    batch = photos[offset : offset + batch_size]
                    if len(batch) == 1:
                        await bot.send_photo(chat_id=manager_telegram_id, photo=batch[0])
                    else:
                        media = [InputMediaPhoto(media=fid) for fid in batch]
                        await bot.send_media_group(chat_id=manager_telegram_id, media=media)
            logger.info("REQUEST SENT TO MANAGER")
            return True
        except TelegramForbiddenError:
            logger.error(
                "SEND_TO_MANAGER_FAILED telegram_id=%s lead_id=%s — "
                "Forbidden: bot was blocked by the user. Manager must /start the bot.",
                manager_telegram_id,
                lead_id,
            )
            return False
        except Exception:
            logger.exception(
                "SEND_TO_MANAGER_FAILED telegram_id=%s lead_id=%s",
                manager_telegram_id,
                lead_id,
            )
            return False
        finally:
            await bot.session.close()

    @staticmethod
    async def notify_auto_client_request(
        *,
        request_number: str,
        request_type: str,
        description: str | None,
        user_description: str | None = None,
        client_username: str | None,
        client_full_name: str | None,
        client_phone: str | None = None,
        client_telegram_id: int | None = None,
        photo_file_id: str | None = None,
        photo_file_ids: list[str] | None = None,
        flow_request_type: str | None = None,
        vin: str | None = None,
        brand: str | None = None,
        model: str | None = None,
        year: int | None = None,
        mileage: int | None = None,
        budget: float | None = None,
        price: float | None = None,
        service_type: str | None = None,
        lead_id: str | uuid.UUID | None = None,
    ) -> bool:
        from services.auto_client_flow_engine import (
            REQUEST_TYPE_LABELS,
            build_manager_notification_lines,
        )
        from services.pg_auto_client_request_engine import FLOW_TYPE_TO_DB

        db_type = FLOW_TYPE_TO_DB.get(request_type, request_type)
        if db_type == request_type and request_type in FLOW_TYPE_TO_DB.values():
            db_type = request_type

        manager_info = await ManagerDeliveryEngineV1.resolve_default_manager()
        if manager_info is None:
            return False

        _, manager_telegram_id, _ = manager_info

        flow_key = flow_request_type or request_type
        if flow_key in FLOW_TYPE_TO_DB:
            pass
        else:
            for k, v in FLOW_TYPE_TO_DB.items():
                if v == db_type:
                    flow_key = k
                    break

        data = {
            "brand": brand,
            "model": model,
            "year": year,
            "mileage": mileage,
            "budget": budget,
            "price": price,
            "vin": vin,
            "service_type": service_type,
            "user_description": user_description or description,
            "photo_file_ids": photo_file_ids or ([photo_file_id] if photo_file_id else []),
        }
        lines = build_manager_notification_lines(
            flow_type=flow_key,
            request_number=request_number,
            data=data,
            client_username=client_username,
            client_full_name=client_full_name,
            client_phone=client_phone,
        )
        if client_telegram_id and flow_key not in REQUEST_TYPE_LABELS:
            lines.insert(4, f"Telegram ID: {client_telegram_id}")

        return await ManagerDeliveryEngineV1.send_to_manager(
            manager_telegram_id=manager_telegram_id,
            text="\n".join(lines),
            lead_id=lead_id,
            request_number=request_number,
            photo_file_id=photo_file_id,
            photo_file_ids=photo_file_ids,
        )

    @staticmethod
    async def debug_report(telegram_user_id: int) -> str:
        user = await ManagerDeliveryEngineV1.get_manager_user(telegram_id=telegram_user_id)
        roles = await ManagerDeliveryEngineV1.list_role_codes_for_user(user.id) if user else []
        is_mgr = await ManagerDeliveryEngineV1.is_platform_manager(telegram_user_id)
        menu_type = await ManagerDeliveryEngineV1.resolve_menu_type(telegram_user_id)

        assigned_leads = 0
        assigned_requests = 0
        if user is not None:
            from sqlalchemy import func, select
            from database.models.auto_client_request import AutoClientRequest
            from database.models.lead_engine import LeadEngineLead

            async with get_session() as session:
                assigned_leads = int(
                    (
                        await session.execute(
                            select(func.count())
                            .select_from(LeadEngineLead)
                            .where(LeadEngineLead.assigned_manager_id == user.id)
                        )
                    ).scalar_one()
                )
                assigned_requests = int(
                    (
                        await session.execute(
                            select(func.count())
                            .select_from(AutoClientRequest)
                            .where(AutoClientRequest.manager_id == user.id)
                        )
                    ).scalar_one()
                )

        from services.pg_entry_point_engine import EntryPointEngineV1

        ctx = await EntryPointEngineV1.get_flow_context(telegram_user_id)
        default_mgr = await ManagerDeliveryEngineV1.get_manager_user(
            telegram_id=DEFAULT_AUTO_MANAGER_ID,
        )

        lines = [
            "🛠 /debug_manager",
            "",
            f"telegram_id: {telegram_user_id}",
            f"internal_user_id: {user.id if user else '—'}",
            f"username: @{user.username}" if user and user.username else f"username: {user.username if user else '—'}",
            f"roles: {roles or '[]'}",
            f"is_manager: {is_mgr}",
            f"assigned_leads_count: {assigned_leads}",
            f"assigned_requests_count: {assigned_requests}",
            f"menu_type: {menu_type}",
            f"entry_point: {ctx.get('entry_point')}",
            f"current_flow: {ctx.get('current_flow')}",
            f"default_manager_enabled: {default_mgr is not None}",
            f"default_manager_telegram_id: {DEFAULT_AUTO_MANAGER_ID}",
        ]
        return "\n".join(lines)
