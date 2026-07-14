# Tenant navigation guard — block cross-vertical access for scoped users.

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import BaseFilter
from aiogram.types import Message

from keyboards import tenant_scoped_menu
from services.pg_tenant_entry_registry_engine import TenantRoutingEngineV1
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1
from services.tenant_routing import is_owner, module_for_button_text

tenant_guard_router = Router()

_BLOCKED_MAIN_BUTTONS = frozenset({
    "💰 Crypto OTC",
    "🚁 Drone Engineering",
    "⚖ Юриспруденция",
    "☕ Cafe & Beauty",
    "🌾 Agro Trading",
    "🏢 Company Core",
    "🚗 Авто",
    "👥 Пользователи",
    "📅 Календарь",
    "📊 Аналитика",
    "🤖 AI Агенты",
    "🤖 AI помощник",
    "🔔 Уведомления",
    "✅ Задачи",
    "📂 Файлы",
    "🔎 Поиск",
    "📊 Отчеты",
    "📁 Файлы и документы",
    "🔎 Глобальный поиск",
    "⚙️ Бизнес-процессы",
    "⚙ Администрирование",
    "👑 Owner Panel",
    "🧪 Тестовый центр",
    "❤️ System Health",
})


class TenantAccessDeniedFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user_id = message.from_user.id
        if is_owner(user_id):
            return False
        ctx = await TenantRoutingEngineV1.get_tenant_context(user_id)
        if not ctx.get("tenant_scoped"):
            return False
        module_key = module_for_button_text(message.text)
        if module_key is None:
            return False
        allowed = await TenantRoutingEngineV1.can_access_module(user_id, module_key)
        return not allowed


@tenant_guard_router.message(F.text.in_(_BLOCKED_MAIN_BUTTONS), TenantAccessDeniedFilter())
async def tenant_navigation_guard(message: Message) -> None:
    user_id = message.from_user.id
    lang = await VerticalOnboardingEngineV1.get_language(user_id)
    ctx = await TenantRoutingEngineV1.get_tenant_context(user_id)
    scoped = tenant_scoped_menu(ctx, lang)
    await message.answer(
        await TenantRoutingEngineV1.tenant_denied_message(user_id, lang),
        reply_markup=scoped,
    )
