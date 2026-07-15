# Automotive Partner Branding UI v1 — partner cards, CTAs, lead flow.

from __future__ import annotations

import logging
import re
from typing import Any

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from database.models.automotive_partner_integration import AutomotivePartnerType
from keyboards import (
    auto_insurance_products_inline,
    auto_partner_cards_inline,
    auto_partner_cta_inline,
    auto_vertical_hub_menu,
)
from services.automotive_telegram_access import can_access_automotive_ui
from services.pg_automotive_partner_branding_engine import (
    AutomotivePartnerBrandingEngineV1,
    AutomotivePartnerBrandingError,
)
from services.pg_automotive_partner_integration_engine import (
    AutomotivePartnerIntegrationEngineV1,
    AutomotivePartnerIntegrationError,
)

logger = logging.getLogger(__name__)

automotive_partner_router = Router()

partner_lead_flow: dict[int, dict] = {}

HUB_BUTTON_TO_CATEGORY = {
    "INSURANCE": AutomotivePartnerType.INSURANCE.value,
    "CREDIT": AutomotivePartnerType.CREDIT.value,
    "LEASING": AutomotivePartnerType.LEASING.value,
    "LOGISTICS": AutomotivePartnerType.LOGISTICS.value,
    "LEGAL": AutomotivePartnerType.LEGAL.value,
}


async def show_partner_category(
    message: Message,
    user_id: int,
    category: str,
    *,
    reply_markup=None,
) -> None:
    from services.automotive_localization import category_header, t
    from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1

    lang = await VerticalOnboardingEngineV1.get_language(user_id)
    menu = reply_markup or auto_vertical_hub_menu(lang)
    cards = await AutomotivePartnerBrandingEngineV1.list_category_cards(category, actor_id=user_id)
    if not cards:
        await message.answer(
            f"{AutomotivePartnerBrandingEngineV1.format_category_header(category, lang=lang)}\n\n"
            f"{t('no_partners', lang)}",
            reply_markup=menu,
        )
        return
    header = AutomotivePartnerBrandingEngineV1.format_category_header(category, lang=lang)
    await message.answer(header, reply_markup=menu)
    await message.answer(
        t("partner_cards", lang),
        reply_markup=auto_partner_cards_inline(cards, category=category, lang=lang),
    )


async def _send_partner_card(message: Message, card: dict[str, Any]) -> None:
    text = AutomotivePartnerBrandingEngineV1.format_partner_card_text(card)
    markup = auto_partner_cta_inline(card["code"], card.get("ctas") or [])
    photo = AutomotivePartnerBrandingEngineV1.partner_photo(card)
    if photo:
        try:
            await message.answer_photo(photo=photo, caption=text, reply_markup=markup)
            return
        except Exception:
            logger.warning("Partner logo send failed for %s", card.get("code"))
    await message.answer(text, reply_markup=markup)


async def _handle_cta_action(callback: CallbackQuery, partner_code: str, cta_code: str) -> None:
    user_id = callback.from_user.id
    card = await AutomotivePartnerBrandingEngineV1.get_partner_card(partner_code, actor_id=user_id)
    cta = next((item for item in card.get("ctas", []) if item["cta_code"] == cta_code), None)
    if cta is None:
        await callback.answer("Action not found", show_alert=True)
        return

    action_type = cta.get("action_type")
    if action_type == "url":
        url = cta.get("action_value") or card.get("website") or ""
        await callback.answer(url[:200], show_alert=True)
        if callback.message and url:
            await callback.message.answer(f"🌐 {url}")
        return

    if action_type == "products":
        if card.get("partner_type") != AutomotivePartnerType.INSURANCE.value:
            await callback.answer("Products unavailable", show_alert=True)
            return
        try:
            products = await AutomotivePartnerIntegrationEngineV1.list_insurance_products(
                partner_code=partner_code,
                actor_id=user_id,
            )
            text = AutomotivePartnerIntegrationEngineV1.format_insurance_menu_text(card, products)
            if callback.message:
                await callback.message.answer(text)
                await callback.message.answer(
                    "Insurance products:",
                    reply_markup=auto_insurance_products_inline(products),
                )
        except AutomotivePartnerIntegrationError as exc:
            await callback.answer(str(exc), show_alert=True)
            return
        await callback.answer()
        return

    if action_type == "lead":
        partner_lead_flow[user_id] = {
            "step": "phone",
            "partner_code": partner_code,
            "cta_code": cta_code,
        }
        if callback.message:
            await callback.message.answer(
                f"📞 Request callback — {card.get('name')}\n\n"
                "Send your phone number (e.g. +380XXXXXXXXX):",
                reply_markup=auto_vertical_hub_menu(),
            )
        await callback.answer()
        return

    await callback.answer("Unsupported action", show_alert=True)


@automotive_partner_router.callback_query(F.data.startswith("partner:card:"))
async def partner_card_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if not await can_access_automotive_ui(user_id):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    parts = (callback.data or "").split(":", 3)
    if len(parts) < 4:
        await callback.answer("Invalid partner", show_alert=True)
        return
    partner_code = parts[3]
    try:
        card = await AutomotivePartnerBrandingEngineV1.get_partner_card(partner_code, actor_id=user_id)
    except AutomotivePartnerBrandingError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    if callback.message:
        await _send_partner_card(callback.message, card)
    await callback.answer()


@automotive_partner_router.callback_query(F.data.startswith("partner:cta:"))
async def partner_cta_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if not await can_access_automotive_ui(user_id):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    parts = (callback.data or "").split(":", 3)
    if len(parts) < 4:
        await callback.answer("Invalid action", show_alert=True)
        return
    partner_code, cta_code = parts[2], parts[3]
    try:
        await _handle_cta_action(callback, partner_code, cta_code)
    except AutomotivePartnerBrandingError as exc:
        await callback.answer(str(exc), show_alert=True)


@automotive_partner_router.callback_query(F.data.startswith("partner:back:"))
async def partner_category_back(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if not await can_access_automotive_ui(user_id):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    category = (callback.data or "").split(":", 2)[2]
    if callback.message:
        await show_partner_category(callback.message, user_id, category)
    await callback.answer()


@automotive_partner_router.callback_query(F.data == "partner:hub")
async def partner_hub_back(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.answer("🚗 Auto", reply_markup=auto_vertical_hub_menu())
    await callback.answer()


@automotive_partner_router.callback_query(F.data.startswith("insurance:product:"))
async def insurance_product_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if not await can_access_automotive_ui(user_id):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    product_code = (callback.data or "").split(":", 2)[2]
    try:
        detail = await AutomotivePartnerIntegrationEngineV1.get_insurance_product_detail(
            product_code,
            actor_id=user_id,
        )
        text = AutomotivePartnerIntegrationEngineV1.format_insurance_product_text(detail)
    except AutomotivePartnerIntegrationError as exc:
        await callback.answer(str(exc), show_alert=True)
        return

    if callback.message:
        await callback.message.answer(text, reply_markup=auto_vertical_hub_menu())
    await callback.answer()


@automotive_partner_router.callback_query(F.data == "insurance:back")
async def insurance_back_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if not await can_access_automotive_ui(user_id):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await show_partner_category(callback.message, user_id, AutomotivePartnerType.INSURANCE.value)
    await callback.answer()


@automotive_partner_router.message(
    lambda m: partner_lead_flow.get(m.from_user.id, {}).get("step") == "phone"
    and m.text
    and not m.text.startswith("/")
)
async def partner_lead_phone(message: Message) -> None:
    user_id = message.from_user.id
    flow = partner_lead_flow.pop(user_id, {})
    phone = (message.text or "").strip()
    if not re.match(r"^\+?\d{9,15}$", phone.replace(" ", "").replace("-", "")):
        partner_lead_flow[user_id] = flow
        await message.answer(
            "Invalid phone format. Send digits with country code, e.g. +380971234567",
            reply_markup=auto_vertical_hub_menu(),
        )
        return

    name = message.from_user.full_name or f"User {user_id}"
    try:
        lead = await AutomotivePartnerBrandingEngineV1.create_partner_lead(
            partner_code=flow.get("partner_code", ""),
            actor_id=user_id,
            customer_name=name,
            phone=phone,
            cta_code=flow.get("cta_code"),
        )
    except Exception as exc:
        await message.answer(f"Lead creation failed: {exc}", reply_markup=auto_vertical_hub_menu())
        return

    if lead.get("duplicate_detected"):
        await message.answer(
            "✅ We already have your request. A manager will contact you soon.",
            reply_markup=auto_vertical_hub_menu(),
        )
        return

    await message.answer(
        f"✅ Lead created #{lead.get('id', '—')[:8]}\n"
        f"Manager assigned. Score: {lead.get('score', '—')}",
        reply_markup=auto_vertical_hub_menu(),
    )
