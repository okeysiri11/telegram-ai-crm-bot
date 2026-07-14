# Auto Client flow handlers — menu actions within AUTO_CLIENT entry point.

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from keyboards import auto_client_menu
from services.automotive_localization import btn, normalize_language
from services.entry_point_routing import EntryPoint, FlowState, is_auto_client_menu_text
from services.pg_entry_point_engine import EntryPointEngineV1
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1

auto_client_router = Router()


def _auto_client_text_filter(message: Message) -> bool:
    if not message.from_user or not message.text:
        return False
    return is_auto_client_menu_text(message.text)


@auto_client_router.message(_auto_client_text_filter)
async def auto_client_menu_action(message: Message) -> None:
    user_id = message.from_user.id
    ctx = await EntryPointEngineV1.get_flow_context(user_id)
    if ctx.get("entry_point") != EntryPoint.AUTO_CLIENT.value:
        return

    lang = await VerticalOnboardingEngineV1.get_language(user_id)
    text = (message.text or "").strip()
    await EntryPointEngineV1.set_current_flow(user_id, FlowState.AUTO_CLIENT_MENU)

    replies = {
        btn("client_buy_car", lang): "🚘 Поиск автомобиля. Опишите марку, бюджет и город.",
        btn("client_sell_car", lang): "💰 Продажа автомобиля. Укажите марку, год и пробег.",
        btn("client_listing", lang): "📢 Размещение объявления. Пришлите фото и описание авто.",
        btn("client_services", lang): "🛠 Автоуслуги: сервис, страхование, кредит, логистика.",
        btn("client_manager", lang): "📞 Менеджер получил запрос и свяжется с вами.",
    }
    reply = replies.get(text, "Выберите действие в меню Auto Client.")
    await message.answer(reply, reply_markup=auto_client_menu(lang))
