# Entry point engine — persist flow, route starts, enforce navigation boundaries.

from __future__ import annotations

from typing import Any

from aiogram.types import CallbackQuery, Message, TelegramObject

from database import ensure_user
from database.session import get_session
from repositories.user_vertical_preferences_repository import UserVerticalPreferencesRepository
from services.automotive_localization import normalize_language, t
from services.entry_point_routing import (
    ECOSYSTEM_MENU_BUTTONS,
    ENTRY_POINT_POST_LANGUAGE_STATE,
    FlowState,
    EntryPoint,
    SOURCE_LINK_TO_ENTRY_POINT,
    FLOW_STATE_TO_ENTRY_POINT,
    auto_client_menu_labels,
    flow_for_dealer_step,
    is_auto_client_menu_text,
)
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1
from services.tenant_routing import ENTRY_LINK_REGISTRY, is_owner


class EntryPointEngineV1:
    @staticmethod
    def _resolve_entry_point(ctx: dict[str, Any]) -> EntryPoint | None:
        entry_raw = ctx.get("entry_point")
        if entry_raw:
            try:
                return EntryPoint(entry_raw)
            except ValueError:
                pass
        source_link = ctx.get("source_link")
        if source_link:
            return SOURCE_LINK_TO_ENTRY_POINT.get(source_link)
        return None

    @staticmethod
    async def _ensure_entry_point_persisted(user_id: int, entry_point: EntryPoint) -> None:
        ctx = await EntryPointEngineV1.get_flow_context(user_id)
        if ctx.get("entry_point") == entry_point.value:
            return
        async with get_session() as session:
            await UserVerticalPreferencesRepository(session).upsert(
                telegram_user_id=user_id,
                entry_point=entry_point.value,
            )

    @staticmethod
    async def get_flow_context(telegram_user_id: int) -> dict[str, Any]:
        async with get_session() as session:
            row = await UserVerticalPreferencesRepository(session).get_by_telegram_id(
                telegram_user_id
            )
        if row is None:
            return {
                "entry_point": None,
                "current_flow": None,
                "language": "ru",
            }
        return {
            "entry_point": row.entry_point,
            "current_flow": row.current_flow,
            "language": normalize_language(row.language),
            "source_link": row.source_link,
            "tenant_code": row.tenant_code,
            "vertical": row.vertical,
        }

    @staticmethod
    async def set_entry_point(
        *,
        telegram_user_id: int,
        entry_point: EntryPoint,
        current_flow: FlowState,
        full_name: str = "",
        username: str = "",
        source_link: str | None = None,
        vertical: str | None = None,
        tenant_code: str | None = None,
        reset_onboarding: bool = True,
    ) -> dict[str, Any]:
        ensure_user(telegram_user_id, full_name=full_name, username=username)
        async with get_session() as session:
            row = await UserVerticalPreferencesRepository(session).upsert(
                telegram_user_id=telegram_user_id,
                entry_point=entry_point.value,
                current_flow=current_flow.value,
                source_link=source_link,
                vertical=vertical,
                tenant_code=tenant_code,
                onboarding_step="language" if current_flow == FlowState.LANGUAGE_SELECT else None,
                onboarding_completed=False if reset_onboarding else None,
            )
        return {
            "entry_point": row.entry_point,
            "current_flow": row.current_flow,
            "language": normalize_language(row.language),
        }

    @staticmethod
    async def set_current_flow(telegram_user_id: int, flow: FlowState) -> None:
        async with get_session() as session:
            await UserVerticalPreferencesRepository(session).upsert(
                telegram_user_id=telegram_user_id,
                current_flow=flow.value,
            )

    @staticmethod
    async def begin_auto_client(message: Message) -> None:
        user = message.from_user
        await EntryPointEngineV1._clear_blocked_sessions(user.id)
        result = await VerticalOnboardingEngineV1.save_entry_link(
            telegram_user_id=user.id,
            source_link="auto_client",
            full_name=user.full_name or "",
            username=user.username or "",
        )
        await EntryPointEngineV1._ingest_lead(user, "auto_client", result)
        from keyboards import entry_flow_language_inline

        await message.answer(
            "🇺🇦 Выберите язык",
            reply_markup=entry_flow_language_inline(prefix="auto_client"),
        )

    @staticmethod
    async def begin_auto_dealer(message: Message) -> None:
        user = message.from_user
        await EntryPointEngineV1._clear_blocked_sessions(user.id)
        result = await VerticalOnboardingEngineV1.save_entry_link(
            telegram_user_id=user.id,
            source_link="auto_dealer",
            full_name=user.full_name or "",
            username=user.username or "",
        )
        await EntryPointEngineV1._ingest_lead(user, "auto_dealer", result)
        from keyboards import entry_flow_language_inline

        await message.answer(
            "🇺🇦 Выберите язык",
            reply_markup=entry_flow_language_inline(prefix="auto_dealer"),
        )

    @staticmethod
    async def begin_owner_start(message: Message) -> None:
        user = message.from_user
        await EntryPointEngineV1.set_entry_point(
            telegram_user_id=user.id,
            entry_point=EntryPoint.OWNER,
            current_flow=FlowState.OWNER_DASHBOARD,
            full_name=user.full_name or "",
            username=user.username or "",
            reset_onboarding=False,
        )
        await EntryPointEngineV1._open_owner_dashboard(message, user.id)

    @staticmethod
    async def begin_regular_start(message: Message) -> None:
        user = message.from_user
        await EntryPointEngineV1._clear_blocked_sessions(user.id)
        async with get_session() as session:
            repo = UserVerticalPreferencesRepository(session)
            row = await repo.get_by_telegram_id(user.id)
            if row is None:
                await repo.upsert(
                    telegram_user_id=user.id,
                    onboarding_step="language",
                    onboarding_completed=False,
                    current_flow=FlowState.LANGUAGE_SELECT.value,
                )
            else:
                row.entry_point = None
                row.current_flow = FlowState.LANGUAGE_SELECT.value
                row.onboarding_step = "language"
                row.onboarding_completed = False
                await session.flush()
        await EntryPointEngineV1._show_language_picker(message)

    @staticmethod
    async def begin_from_source_link(message: Message, source_link: str) -> bool:
        entry_point = SOURCE_LINK_TO_ENTRY_POINT.get(source_link)
        if entry_point == EntryPoint.AUTO_CLIENT:
            await EntryPointEngineV1.begin_auto_client(message)
            return True
        if entry_point == EntryPoint.AUTO_DEALER:
            await EntryPointEngineV1.begin_auto_dealer(message)
            return True
        user = message.from_user
        if entry_point is not None:
            cfg = ENTRY_LINK_REGISTRY.get(source_link)
            await EntryPointEngineV1.set_entry_point(
                telegram_user_id=user.id,
                entry_point=entry_point,
                current_flow=FlowState.LANGUAGE_SELECT,
                full_name=user.full_name or "",
                username=user.username or "",
                source_link=source_link,
                vertical=cfg.vertical if cfg else None,
                tenant_code=cfg.tenant_code if cfg else None,
            )
            await VerticalOnboardingEngineV1.save_entry_link(
                telegram_user_id=user.id,
                source_link=source_link,
                full_name=user.full_name or "",
                username=user.username or "",
            )
            await EntryPointEngineV1._show_language_picker(message)
            return True
        return False

    @staticmethod
    async def route_after_language(message: Message, user_id: int, language: str) -> bool:
        ctx = await EntryPointEngineV1.get_flow_context(user_id)
        entry_point = EntryPointEngineV1._resolve_entry_point(ctx)
        if entry_point is None:
            return False

        await EntryPointEngineV1._ensure_entry_point_persisted(user_id, entry_point)
        lang = normalize_language(language)

        if entry_point == EntryPoint.AUTO_CLIENT:
            async with get_session() as session:
                await UserVerticalPreferencesRepository(session).upsert(
                    telegram_user_id=user_id,
                    language=lang,
                    role="buyer",
                    onboarding_step="completed",
                    onboarding_completed=True,
                    entry_point=EntryPoint.AUTO_CLIENT.value,
                    current_flow=FlowState.AUTO_CLIENT_MENU.value,
                )
            await EntryPointEngineV1._show_auto_client_menu(message, lang)
            return True

        if entry_point == EntryPoint.AUTO_DEALER:
            async with get_session() as session:
                await UserVerticalPreferencesRepository(session).upsert(
                    telegram_user_id=user_id,
                    language=lang,
                    role="dealer",
                    onboarding_step="dealer_onboarding",
                    onboarding_completed=False,
                    current_flow=FlowState.DEALER_TYPE_SELECT.value,
                )
            from dealer_onboarding_handlers import present_onboarding_start

            await present_onboarding_start(message, user_id)
            return True

        if entry_point == EntryPoint.OWNER:
            await EntryPointEngineV1.set_current_flow(user_id, FlowState.OWNER_DASHBOARD)
            await EntryPointEngineV1._open_owner_dashboard(message, user_id)
            return True

        post_state = ENTRY_POINT_POST_LANGUAGE_STATE.get(entry_point)
        if post_state:
            await EntryPointEngineV1.set_current_flow(user_id, post_state)
            from vertical_onboarding_handlers import enter_tenant_vertical

            await enter_tenant_vertical(message, user_id, lang)
            return True

        return False

    @staticmethod
    async def sync_dealer_flow_state(user_id: int, dealer_step: str | None) -> None:
        ctx = await EntryPointEngineV1.get_flow_context(user_id)
        if ctx.get("entry_point") != EntryPoint.AUTO_DEALER.value:
            return
        flow = flow_for_dealer_step(dealer_step)
        if flow is not None:
            await EntryPointEngineV1.set_current_flow(user_id, flow)

    @staticmethod
    def is_exempt_event(event: TelegramObject) -> bool:
        if isinstance(event, Message) and event.text:
            text = event.text.strip()
            if text.startswith("/start"):
                return True
            if text in {"/start_auto_client", "/start_auto_dealer"}:
                return True
        if isinstance(event, CallbackQuery) and event.data:
            if event.data.startswith("onboard:lang:"):
                return True
            if event.data.startswith(("auto_client:lang:", "auto_dealer:lang:")):
                return True
        return False

    @staticmethod
    async def check_transition(
        telegram_user_id: int,
        *,
        text: str | None = None,
        callback_data: str | None = None,
    ) -> str | None:
        if is_owner(telegram_user_id):
            return None

        ctx = await EntryPointEngineV1.get_flow_context(telegram_user_id)
        entry_raw = ctx.get("entry_point")
        if not entry_raw:
            return None

        entry_point = EntryPoint(entry_raw)
        lang = ctx.get("language") or "ru"
        current_flow_raw = ctx.get("current_flow")
        if current_flow_raw:
            try:
                current_flow = FlowState(current_flow_raw)
                bound_entry = FLOW_STATE_TO_ENTRY_POINT.get(current_flow)
                if bound_entry is not None and bound_entry != entry_point:
                    return EntryPointEngineV1._denied_message(entry_point, lang)
            except ValueError:
                pass

        normalized = (text or "").strip()

        if entry_point == EntryPoint.AUTO_CLIENT:
            if normalized in ECOSYSTEM_MENU_BUTTONS:
                return EntryPointEngineV1._denied_message(entry_point, lang)
            if normalized == "🤖 AI Sales Assistant" or normalized.lower().startswith("/sales"):
                return EntryPointEngineV1._denied_message(entry_point, lang)
            if callback_data and callback_data.startswith("onboard:") and not callback_data.startswith(
                "onboard:lang:"
            ):
                return EntryPointEngineV1._denied_message(entry_point, lang)
            if callback_data and (
                callback_data.startswith("billing:") or callback_data.startswith("payment:")
            ):
                return EntryPointEngineV1._denied_message(entry_point, lang)
            if normalized and not is_auto_client_menu_text(normalized, lang):
                dealer_markers = ("Dealer Onboarding", "тариф", "оплат", "Automotive")
                if any(marker.lower() in normalized.lower() for marker in dealer_markers):
                    return EntryPointEngineV1._denied_message(entry_point, lang)
            return None

        if entry_point == EntryPoint.AUTO_DEALER:
            allowed_client = auto_client_menu_labels(lang)
            if normalized in ECOSYSTEM_MENU_BUTTONS or normalized in allowed_client:
                return EntryPointEngineV1._denied_message(entry_point, lang)
            if normalized.startswith("🤖 AI"):
                return EntryPointEngineV1._denied_message(entry_point, lang)
            return None

        target_flow = EntryPointEngineV1._target_flow_from_event(text=normalized, callback_data=callback_data)
        if target_flow is None:
            return None
        expected_entry = FLOW_STATE_TO_ENTRY_POINT.get(target_flow)
        if expected_entry is not None and expected_entry != entry_point:
            return EntryPointEngineV1._denied_message(entry_point, lang)
        return None

    @staticmethod
    def _target_flow_from_event(
        *,
        text: str | None,
        callback_data: str | None,
    ) -> FlowState | None:
        if text and text.strip() in ECOSYSTEM_MENU_BUTTONS:
            return FlowState.OWNER_DASHBOARD
        if text and is_auto_client_menu_text(text):
            return FlowState.AUTO_CLIENT_MENU
        if callback_data and callback_data.startswith("onboard:automotive"):
            return FlowState.DEALER_TYPE_SELECT
        if callback_data and callback_data.startswith("billing:plan"):
            return FlowState.PLAN_SELECT
        if callback_data and (
            callback_data.startswith("billing:pricing")
            or callback_data.startswith("billing:pay")
            or callback_data.startswith("payment:")
        ):
            return FlowState.PAYMENT
        return None

    @staticmethod
    def _denied_message(entry_point: EntryPoint, lang: str) -> str:
        labels = {
            EntryPoint.AUTO_CLIENT: "🚘 Auto Client",
            EntryPoint.AUTO_DEALER: "🏢 Dealer Onboarding",
            EntryPoint.AGRO_CLIENT: "🌾 Agro Client",
            EntryPoint.AGRO_SUPPLIER: "🌾 Agro Supplier",
            EntryPoint.OWNER: "👑 Owner",
        }
        title = labels.get(entry_point, entry_point.value)
        if lang == "uk":
            return f"🔒 Доступ заборонено. Ви в потоці {title}."
        return f"🔒 Доступ запрещён. Вы в потоке {title}."

    @staticmethod
    async def reply_markup_for_user(telegram_user_id: int):
        from services.pg_manager_delivery_engine import ManagerDeliveryEngineV1

        return await ManagerDeliveryEngineV1.reply_markup_for_user(telegram_user_id)

    @staticmethod
    async def _reply_markup_for_user_legacy(telegram_user_id: int):
        from keyboards import auto_client_menu, owner_dashboard_menu, owner_main_menu

        ctx = await EntryPointEngineV1.get_flow_context(telegram_user_id)
        entry_raw = ctx.get("entry_point")
        lang = ctx.get("language") or "ru"
        if entry_raw == EntryPoint.AUTO_CLIENT.value:
            return auto_client_menu(lang)
        if entry_raw == EntryPoint.OWNER.value:
            return owner_dashboard_menu()
        if entry_raw == EntryPoint.AUTO_DEALER.value:
            return await __import__(
                "dealer_onboarding_handlers", fromlist=["_main_menu_for"]
            )._main_menu_for(telegram_user_id)
        return owner_main_menu()

    @staticmethod
    async def _ingest_lead(user, source_link: str, result: dict) -> None:
        from services.pg_lead_engine import LeadEngineV1

        await LeadEngineV1.ingest_from_deep_link(
            telegram_user_id=user.id,
            telegram_username=user.username,
            full_name=user.full_name,
            start_args=source_link,
            vertical=result.get("vertical"),
            role=result.get("preset_role"),
            source_link=source_link,
        )

    @staticmethod
    async def _show_language_picker(message: Message) -> None:
        await message.answer(
            t("lang_picker_title", "ru"),
            reply_markup=VerticalOnboardingEngineV1.language_picker_inline(),
        )

    @staticmethod
    async def _show_auto_client_menu(message: Message, lang: str) -> None:
        from keyboards import auto_client_menu

        await message.answer(
            "Выберите действие:",
            reply_markup=auto_client_menu(lang),
        )

    @staticmethod
    async def _open_owner_dashboard(message: Message, user_id: int) -> None:
        from keyboards import owner_dashboard_menu
        from owner_dashboard_handlers import owner_dashboard_active
        from services.pg_owner_dashboard_engine import OwnerDashboardEngineV1

        owner_dashboard_active.add(user_id)
        data = await OwnerDashboardEngineV1.get_dashboard()
        text = OwnerDashboardEngineV1.format_main_dashboard(data)
        await message.answer(text, reply_markup=owner_dashboard_menu())

    @staticmethod
    async def _clear_blocked_sessions(user_id: int) -> None:
        from ai_sales_handlers import sales_assistant_active
        from auto_vertical_handlers import auto_vertical_active

        sales_assistant_active.discard(user_id)
        auto_vertical_active.pop(user_id, None)
