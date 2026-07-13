# Automotive Partner Integration v1 — insurance product callbacks.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from keyboards import auto_insurance_products_inline, auto_vertical_hub_menu
from services.automotive_telegram_access import can_access_automotive_ui
from services.pg_automotive_partner_integration_engine import (
    AutomotivePartnerIntegrationEngineV1,
    AutomotivePartnerIntegrationError,
)

logger = logging.getLogger(__name__)

automotive_partner_router = Router()


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
    try:
        partner = await AutomotivePartnerIntegrationEngineV1.get_insurance_partner()
        products = await AutomotivePartnerIntegrationEngineV1.list_insurance_products(actor_id=user_id)
        text = AutomotivePartnerIntegrationEngineV1.format_insurance_menu_text(partner, products)
        markup = auto_insurance_products_inline(products)
    except AutomotivePartnerIntegrationError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    if callback.message:
        await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()
