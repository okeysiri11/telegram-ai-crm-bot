# Tenant navigation guard — block cross-vertical access for scoped users.

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import BaseFilter
from aiogram.types import Message

from keyboards import auto_client_menu, tenant_scoped_menu
from services.entry_point_routing import EntryPoint, ECOSYSTEM_MENU_BUTTONS
from services.pg_entry_point_engine import EntryPointEngineV1
from services.pg_tenant_entry_registry_engine import TenantRoutingEngineV1
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1
from services.tenant_routing import is_owner, module_for_button_text

tenant_guard_router = Router()

_BLOCKED_MAIN_BUTTONS = ECOSYSTEM_MENU_BUTTONS


class TenantAccessDeniedFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user_id = message.from_user.id
        if is_owner(user_id):
            return False
        ctx_flow = await EntryPointEngineV1.get_flow_context(user_id)
        if ctx_flow.get("entry_point") in {
            EntryPoint.AUTO_CLIENT.value,
            EntryPoint.AUTO_DEALER.value,
        }:
            return True
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
    ctx_flow = await EntryPointEngineV1.get_flow_context(user_id)
    if ctx_flow.get("entry_point") == EntryPoint.AUTO_CLIENT.value:
        await message.answer(
            await EntryPointEngineV1.check_transition(user_id, text=message.text)
            or "🔒 Доступ запрещён. Вы в потоке Auto Client.",
            reply_markup=auto_client_menu(lang),
        )
        return
    if ctx_flow.get("entry_point") == EntryPoint.AUTO_DEALER.value:
        denial = await EntryPointEngineV1.check_transition(user_id, text=message.text)
        await message.answer(
            denial or "🔒 Доступ запрещён. Вы в потоке Dealer Onboarding.",
            reply_markup=await EntryPointEngineV1.reply_markup_for_user(user_id),
        )
        return
    ctx = await TenantRoutingEngineV1.get_tenant_context(user_id)
    scoped = tenant_scoped_menu(ctx, lang)
    await message.answer(
        await TenantRoutingEngineV1.tenant_denied_message(user_id, lang),
        reply_markup=scoped,
    )
