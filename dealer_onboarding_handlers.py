# Dealer Onboarding Flow v1 — Telegram handlers.

from __future__ import annotations

import logging
import uuid

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from database.models.dealer_onboarding_engine import OnboardingStepName
from keyboards import (
    auto_billing_payment_inline,
    auto_billing_plans_inline,
    auto_billing_pricing_inline,
    dealer_onboarding_automotive_inline,
    dealer_onboarding_resume_inline,
    owner_main_menu,
)
from services.automotive_telegram_access import can_see_automotive_menu_button
from services.pg_commercial_billing_engine import CommercialBillingEngineV1
from services.pg_dealer_onboarding_engine import DealerOnboardingEngineV1

logger = logging.getLogger(__name__)

dealer_onboarding_router = Router()


async def _main_menu_for(user_id: int):
    show = await can_see_automotive_menu_button(user_id)
    return owner_main_menu(show_automotive=show)


async def present_onboarding_start(message: Message, user_id: int) -> None:
    from services.pg_entry_point_engine import EntryPointEngineV1

    session = await DealerOnboardingEngineV1.start_session(user_id)
    await EntryPointEngineV1.sync_dealer_flow_state(user_id, session.get("current_step"))
    await message.answer(
        "🚗 Dealer Onboarding\n\n"
        "Подключите Automotive-модуль для вашего автосалона.\n\n"
        "Шаг 1: выберите направление Automotive.",
        reply_markup=dealer_onboarding_automotive_inline(),
    )
    logger.info("Dealer onboarding started for user %s session %s", user_id, session["id"])


async def present_onboarding_resume(message: Message, session: dict) -> None:
    await message.answer(
        DealerOnboardingEngineV1.resume_message(session),
        reply_markup=dealer_onboarding_resume_inline(session["current_step"]),
    )


async def continue_onboarding_step(message: Message, user_id: int, session: dict) -> None:
    step = session.get("current_step")
    if step == OnboardingStepName.STARTED.value:
        await message.answer(
            "Выберите направление Automotive:",
            reply_markup=dealer_onboarding_automotive_inline(),
        )
        return
    if step == OnboardingStepName.AUTOMOTIVE_SELECTED.value:
        await message.answer(
            "💳 Выберите тариф:",
            reply_markup=auto_billing_plans_inline(),
        )
        return
    if step == OnboardingStepName.TARIFF_SELECTED.value and session.get("plan_code"):
        await message.answer(
            f"Модель оплаты для {session['plan_code']}:",
            reply_markup=auto_billing_pricing_inline(session["plan_code"]),
        )
        return
    if step == OnboardingStepName.PRICING_MODEL_SELECTED.value:
        plan_code = session.get("plan_code")
        pricing_model = session.get("pricing_model")
        if plan_code and pricing_model:
            await message.answer(
                f"Plan: {plan_code}\nModel: {pricing_model}\n\nВыберите способ оплаты:",
                reply_markup=auto_billing_payment_inline(plan_code, pricing_model),
            )
        return
    if step == OnboardingStepName.PAYMENT_CREATED.value:
        await message.answer(
            "📎 Загрузите фото или PDF квитанции об оплате.",
            reply_markup=await _main_menu_for(user_id),
        )
        return
    if step in {
        OnboardingStepName.RECEIPT_UPLOADED.value,
        OnboardingStepName.OWNER_APPROVED.value,
    }:
        await message.answer(
            "⏳ Платёж на проверке у OWNER. После подтверждения будет активирован Automotive-модуль.",
            reply_markup=await _main_menu_for(user_id),
        )
        return

    await message.answer(
        DealerOnboardingEngineV1.resume_message(session),
        reply_markup=dealer_onboarding_resume_inline(step),
    )


@dealer_onboarding_router.callback_query(F.data == "onboard:automotive")
async def onboard_select_automotive(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    session = await DealerOnboardingEngineV1.get_active_session(user_id)
    if not session or session["status"] != "ACTIVE":
        session = await DealerOnboardingEngineV1.start_session(user_id)

    await DealerOnboardingEngineV1.record_step(
        uuid.UUID(session["id"]),
        OnboardingStepName.AUTOMOTIVE_SELECTED.value,
        payload={"vertical": "automotive"},
    )
    from services.pg_entry_point_engine import EntryPointEngineV1

    await EntryPointEngineV1.sync_dealer_flow_state(
        user_id, OnboardingStepName.AUTOMOTIVE_SELECTED.value
    )
    await callback.message.answer(
        "✅ Automotive выбран\n\n"
        f"{CommercialBillingEngineV1.list_plans_text()}\n\n"
        "Выберите тариф:",
        reply_markup=auto_billing_plans_inline(),
    )
    await callback.answer()


@dealer_onboarding_router.callback_query(F.data == "onboard:resume")
async def onboard_resume(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    session = await DealerOnboardingEngineV1.get_active_session(user_id)
    if not session or session["status"] != "ACTIVE":
        await callback.answer("Сессия истекла. Начните заново через /start", show_alert=True)
        return
    await continue_onboarding_step(callback.message, user_id, session)
    await callback.answer()


@dealer_onboarding_router.callback_query(F.data == "onboard:analytics")
async def onboard_analytics(callback: CallbackQuery) -> None:
    from services.automotive_telegram_access import is_billing_owner

    if not await is_billing_owner(callback.from_user.id):
        await callback.answer("Owner only", show_alert=True)
        return
    analytics = await DealerOnboardingEngineV1.get_analytics()
    await callback.message.answer(DealerOnboardingEngineV1.format_analytics(analytics))
    await callback.answer()
