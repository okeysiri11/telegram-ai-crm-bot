# Auto Vertical Telegram UI v2 — Automotive module + commercial billing.

from __future__ import annotations

import logging
import uuid
from decimal import Decimal, InvalidOperation

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from config import BOT_TOKEN, OWNER_ID
from services.handler_auth import log_audit
from keyboards import (
    AUTO_VERTICAL_MAIN_BUTTON,
    auto_billing_owner_actions_inline,
    auto_billing_payment_inline,
    auto_billing_plans_inline,
    auto_billing_pricing_inline,
    auto_vertical_actions_inline,
    auto_vertical_car_list_inline,
    auto_vertical_hub_menu,
    auto_vertical_menu,
    owner_main_menu,
)
from services.automotive_localization import (
    btn,
    category_header,
    hub_screen_to_category,
    is_back_button,
    resolve_auto_screen,
    t,
)
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1
from services.automotive_telegram_access import (
    can_access_automotive_ui,
    can_see_automotive_menu_button,
    is_billing_owner,
)
from services.pg_auto_marketing_engine import AutoMarketingEngineError, AutoMarketingEngineV1
from services.pg_car_engine import CarEngineError, CarEngineV1
from services.dealer_rate_service import DealerRateService
from services.pg_automotive_partner_integration_engine import AutomotivePartnerIntegrationEngineV1
from automotive_partner_handlers import HUB_BUTTON_TO_CATEGORY, show_partner_category
from database.models.automotive_partner_integration import AutomotivePartnerType
from services.pg_commercial_billing_engine import (
    CommercialBillingEngineError,
    CommercialBillingEngineV1,
    PAYMENT_METHOD_LABELS,
    PLAN_MARKETING,
    PRICING_MODEL_LABELS,
)
from database.models.dealer_onboarding_engine import OnboardingStepName
from services.pg_dealer_onboarding_engine import DealerOnboardingEngineV1
from services.pg_lead_automation_engine import LeadAutomationEngineV1
from services.vin_decoder import (
    decode_vin,
    validate_vin,
)
from src.verticals.auto.service import AutoVerticalService

logger = logging.getLogger(__name__)

auto_vertical_router = Router()
auto_router = auto_vertical_router

auto_vertical_active: dict[int, bool] = {}
auto_vertical_section: dict[int, str] = {}
auto_vertical_flow: dict[int, dict] = {}
auto_billing_flow: dict[int, dict] = {}


async def _user_lang(user_id: int) -> str:
    return await VerticalOnboardingEngineV1.get_language(user_id)


def _normalize_screen(text: str) -> str | None:
    return resolve_auto_screen(text)


async def _main_menu_for(user_id: int):
    from keyboards import tenant_scoped_menu
    from services.pg_tenant_entry_registry_engine import TenantRoutingEngineV1

    ctx = await TenantRoutingEngineV1.get_tenant_context(user_id)
    if ctx.get("tenant_scoped"):
        scoped = tenant_scoped_menu(ctx, ctx.get("language"))
        if scoped:
            return scoped
    show = await can_see_automotive_menu_button(user_id)
    return owner_main_menu(show_automotive=show)


def _format_car_card(car: dict) -> str:
    lines = [
        f"🚗 {car.get('year', '—')} {car.get('make', '')} {car.get('model', '')}".strip(),
        f"VIN: {car.get('vin', '—')}",
        f"Status: {car.get('status', '—')}",
    ]
    if car.get("color"):
        lines.append(f"Color: {car['color']}")
    if car.get("mileage") is not None:
        lines.append(f"Mileage: {car['mileage']}")
    if car.get("purchase_price"):
        lines.append(f"Purchase: {car['purchase_price']}")
    if car.get("total_cost"):
        lines.append(f"Total cost: {car['total_cost']}")
    if car.get("sale_price"):
        lines.append(f"Sale: {car['sale_price']}")
    if car.get("expected_profit"):
        lines.append(f"Expected profit: {car['expected_profit']}")
    equivalents = car.get("price_equivalents")
    if equivalents:
        lines.append(
            "FX (dealer): "
            f"UAH {equivalents.get('UAH')} | "
            f"USD {equivalents.get('USD')} | "
            f"EUR {equivalents.get('EUR')} | "
            f"USDT {equivalents.get('USDT')}"
        )
    elif car.get("rates_error"):
        lines.append("FX: dealer rates not configured in Telegram channel")
    return "\n".join(lines)


def _format_profit_breakdown(profit: dict) -> str:
    return (
        "🧮 Profit Calculator\n\n"
        f"Purchase: {profit.get('purchase_price', '0')}\n"
        f"Delivery: {profit.get('delivery_cost', '0')}\n"
        f"Customs: {profit.get('customs_cost', '0')}\n"
        f"Repair: {profit.get('repair_cost', '0')}\n"
        f"Advertising: {profit.get('advertising_cost', '0')}\n"
        f"Total cost: {profit.get('total_cost', '0')}\n"
        f"Sale price: {profit.get('sale_price', '—')}\n"
        f"Expected profit: {profit.get('expected_profit', '—')}"
    )


def _clear_flow(user_id: int) -> None:
    auto_vertical_flow.pop(user_id, None)


async def _show_car_list(message: Message, user_id: int) -> None:
    try:
        cars = await CarEngineV1.list_cars(user_id, limit=50)
        cars = await DealerRateService.enrich_car_listings(user_id, cars)
    except CarEngineError as exc:
        await message.answer(str(exc), reply_markup=auto_vertical_menu(await _user_lang(user_id)))
        return

    if not cars:
        await message.answer(
            "📋 Список авто\n\nИнвентарь пуст. Добавьте автомобиль через «🚗 Добавить авто».",
            reply_markup=auto_vertical_menu(await _user_lang(user_id)),
        )
        return

    await message.answer(
        f"📋 Список авто\n\nВсего: {len(cars)}",
        reply_markup=auto_vertical_car_list_inline(cars),
    )
    await message.answer("Выберите автомобиль:", reply_markup=auto_vertical_menu(await _user_lang(user_id)))


async def _start_add_car(message: Message, user_id: int) -> None:
    auto_vertical_flow[user_id] = {"step": "make", "data": {}}
    await message.answer(
        "🚗 Добавить авто\n\nУкажите марку автомобиля:",
        reply_markup=auto_vertical_menu(await _user_lang(user_id)),
    )


async def _finalize_add_car(message: Message, user_id: int, data: dict) -> None:
    fields = dict(data.get("fields") or {})
    vin = data.get("vin")
    _clear_flow(user_id)
    try:
        car = await CarEngineV1.create_car(
            user_id,
            vin=vin,
            make=data["make"],
            model=data["model"],
            year=data["year"],
            **fields,
        )
    except CarEngineError as exc:
        await message.answer(f"❌ {exc}", reply_markup=auto_vertical_menu(await _user_lang(user_id)))
        return

    if vin:
        await AutoVerticalService.record_vin_intake(
            vin=vin,
            car_id=uuid.UUID(car["id"]),
            created_by=user_id,
        )

    await message.answer(
        "✅ Автомобиль добавлен\n\n" + _format_car_card(car),
        reply_markup=auto_vertical_menu(await _user_lang(user_id)),
    )
    log_audit(user_id, "create", "auto_vertical", vin or car["id"])


async def _start_search(message: Message, user_id: int) -> None:
    auto_vertical_flow[user_id] = {"step": "search", "data": {}}
    await message.answer(
        "🔍 Поиск авто\n\n"
        "Введите VIN, марку, модель, год или статус:",
        reply_markup=auto_vertical_menu(await _user_lang(user_id)),
    )


async def _start_profit_calculator(message: Message, user_id: int) -> None:
    auto_vertical_flow[user_id] = {"step": "profit_vin", "data": {}}
    await message.answer(
        "💰 Калькулятор прибыли\n\n"
        "Введите VIN существующего авто или «-» для ручного расчёта:",
        reply_markup=auto_vertical_menu(await _user_lang(user_id)),
    )


def _format_queue_stats(stats: dict) -> str:
    lines = ["📊 Очереди публикаций:"]
    by_channel = stats.get("by_channel", {})
    channel_labels = {
        "telegram": "Telegram",
        "instagram": "Instagram",
        "facebook": "Facebook",
        "tiktok": "TikTok",
    }
    for channel, label in channel_labels.items():
        channel_stats = by_channel.get(channel, {})
        queued = channel_stats.get("queued", 0) + channel_stats.get("scheduled", 0)
        published = channel_stats.get("published", 0)
        failed = channel_stats.get("failed", 0)
        lines.append(f"• {label}: в очереди {queued}, опубликовано {published}, ошибок {failed}")
    return "\n".join(lines)


def _format_campaign_line(campaign: dict) -> str:
    channels = ", ".join(campaign.get("channels") or [])
    return f"• {campaign.get('name')} [{campaign.get('status')}] — {channels}"


async def _show_marketing(message: Message, user_id: int) -> None:
    try:
        stats = await AutoMarketingEngineV1.get_queue_stats(user_id)
        campaigns = await AutoMarketingEngineV1.list_campaigns(user_id, limit=5)
    except AutoMarketingEngineError as exc:
        await message.answer(str(exc), reply_markup=auto_vertical_menu(await _user_lang(user_id)))
        return

    lines = [
        "📢 Продвижение",
        "",
        "Каналы: Telegram, Instagram, Facebook, TikTok",
        "",
        _format_queue_stats(stats),
    ]
    if campaigns:
        lines.extend(["", "Кампании:"])
        lines.extend(_format_campaign_line(c) for c in campaigns)
    else:
        lines.extend(["", "Кампаний пока нет."])

    await message.answer("\n".join(lines), reply_markup=auto_vertical_menu(await _user_lang(user_id)))
    await message.answer(
        "Для публикации авто отправьте VIN или нажмите «📋 Список авто» "
        "и выберите авто, затем вернитесь в Продвижение.",
        reply_markup=auto_vertical_actions_inline("marketing"),
    )
    auto_vertical_flow[user_id] = {"step": "marketing_vin", "data": {}}
    log_audit(user_id, "open", "auto_vertical", "marketing")


async def _show_analytics(message: Message, user_id: int) -> None:
    try:
        from services.pg_analytics_engine import AnalyticsEngineV1

        tenant_id = await AutoVerticalService.resolve_default_tenant_id()
        if tenant_id is None:
            await message.answer(
                "📊 Аналитика\n\nTenant не настроен.",
                reply_markup=auto_vertical_menu(await _user_lang(user_id)),
            )
            return
        dashboard = await AnalyticsEngineV1.get_dashboard(user_id, tenant_id)
        lead = dashboard.get("lead_statistics") or {}
        sales = dashboard.get("sales_statistics") or {}
        await message.answer(
            "📊 Аналитика\n\n"
            f"Дата: {dashboard.get('metric_date', '—')}\n"
            f"Leads: {lead.get('total_leads', 0)}\n"
            f"CPL: {lead.get('cpl', '—')}\n"
            f"Conversion: {lead.get('conversion_rate', '—')}\n"
            f"Deals won: {sales.get('deals_won', 0)}\n"
            f"Avg deal: {sales.get('average_deal_size', '—')}\n"
            f"Vehicle turnover: {sales.get('vehicle_turnover', '—')}",
            reply_markup=auto_vertical_menu(await _user_lang(user_id)),
        )
    except Exception as exc:
        await message.answer(
            f"📊 Аналитика\n\nДанные временно недоступны: {exc}",
            reply_markup=auto_vertical_menu(await _user_lang(user_id)),
        )


async def _show_ai_manager(message: Message, user_id: int) -> None:
    lang = await _user_lang(user_id)
    auto_vertical_section[user_id] = "ai_manager"
    await message.answer(
        "🤖 AI Менеджер\n\n"
        "Задайте вопрос — AI поможет с подбором авто, услугами и квалификацией заявки.\n"
        "Пример: «Ищу BMW X5 дизель до 40000$ в Одессе»",
        reply_markup=auto_vertical_menu(lang),
    )


async def _show_leads(message: Message, user_id: int) -> None:
    try:
        leads = await LeadAutomationEngineV1.list_leads(user_id, limit=10)
    except Exception as exc:
        await message.answer(
            f"👥 Лиды\n\nОшибка загрузки: {exc}",
            reply_markup=auto_vertical_menu(await _user_lang(user_id)),
        )
        return
    if not leads:
        await message.answer(
            "👥 Лиды\n\nЛидов пока нет.",
            reply_markup=auto_vertical_menu(await _user_lang(user_id)),
        )
        return
    lines = ["👥 Лиды", ""]
    for lead in leads[:10]:
        lines.append(
            f"• {lead.get('source', '—')} | {lead.get('status', '—')} | "
            f"{lead.get('customer_name') or lead.get('phone') or lead.get('id', '')[:8]}"
        )
    await message.answer("\n".join(lines), reply_markup=auto_vertical_menu(await _user_lang(user_id)))


async def _show_billing(message: Message, user_id: int) -> None:
    view = await CommercialBillingEngineV1.get_user_subscription_view(user_id)
    lines = [
        "💳 Тарифы и услуги",
        "",
        CommercialBillingEngineV1.list_plans_text(),
        "",
    ]
    if view.get("active_payment"):
        ap = view["active_payment"]
        lines.append(f"✅ Активный план: {ap['plan_code']} ({ap['status']})")
    elif view.get("pending_payment"):
        pp = view["pending_payment"]
        lines.append(f"⏳ Ожидает подтверждения: {pp['plan_code']}")
    else:
        lines.append("Выберите тариф для подключения:")
    await message.answer("\n".join(lines), reply_markup=auto_vertical_menu(await _user_lang(user_id)))
    await message.answer("Тарифы:", reply_markup=auto_billing_plans_inline())
    if await is_billing_owner(user_id):
        pending = await CommercialBillingEngineV1.list_pending_for_owner(user_id)
        if pending:
            await message.answer(f"🔐 Owner: pending payments — {len(pending)}")


async def _show_settings(message: Message, user_id: int) -> None:
    lang = await _user_lang(user_id)
    dealer_sources = await AutomotivePartnerIntegrationEngineV1.list_dealer_sources(actor_id=user_id)
    sources_text = AutomotivePartnerIntegrationEngineV1.format_dealer_sources_report(dealer_sources)
    await message.answer(
        "⚙ Настройки авто\n\n"
        "• Каналы продвижения: Telegram, Instagram, Facebook, TikTok\n"
        "• Уведомления о SLA и лидах\n"
        "• Интеграция с Car Engine и Marketing Engine\n\n"
        f"{sources_text}\n\n"
        "Расширенные настройки — через админ-панель.",
        reply_markup=auto_vertical_menu(lang),
    )


async def _show_dealer_rates(message: Message, user_id: int) -> None:
    from services.pg_automotive_treasury_engine import AutomotiveTreasuryEngineV1

    lang = await _user_lang(user_id)
    try:
        rates = await DealerRateService.get_authoritative_rates()
        text = AutomotiveTreasuryEngineV1.format_rates_report(rates)
    except Exception as exc:
        text = str(exc)
    await message.answer(text, reply_markup=auto_vertical_menu(lang))


async def _show_treasury(message: Message, user_id: int) -> None:
    from services.pg_dealer_quote_authority_engine import DealerQuoteAuthorityEngineV1

    lang = await _user_lang(user_id)
    try:
        dashboard = await DealerQuoteAuthorityEngineV1.get_treasury_dashboard()
        text = DealerQuoteAuthorityEngineV1.format_treasury_dashboard(dashboard)
    except Exception as exc:
        text = f"{btn('treasury', lang)}\n\n{exc}"
    await message.answer(text, reply_markup=auto_vertical_menu(lang))


async def _open_auto_hub(message: Message, user_id: int) -> None:
    """First entry into Auto Hub."""
    auto_vertical_section[user_id] = "hub"
    lang = await _user_lang(user_id)
    await message.answer(
        t("auto_hub_title", lang),
        reply_markup=auto_vertical_hub_menu(lang),
    )


async def _return_to_auto_hub(message: Message, user_id: int) -> None:
    """Back navigation — reset section/flow and restore hub keyboard (one message)."""
    _clear_flow(user_id)
    auto_billing_flow.pop(user_id, None)
    auto_vertical_section[user_id] = "hub"
    lang = await _user_lang(user_id)
    await message.answer(
        t("auto_hub_title", lang),
        reply_markup=auto_vertical_hub_menu(lang),
    )


async def _return_to_cars_menu(message: Message, user_id: int) -> None:
    """Back from in-flow actions to the cars submenu."""
    _clear_flow(user_id)
    auto_vertical_section[user_id] = "cars"
    lang = await _user_lang(user_id)
    await message.answer(
        t("auto_cars_title", lang),
        reply_markup=auto_vertical_menu(lang),
    )


async def _exit_auto_vertical(message: Message, user_id: int) -> None:
    """Leave Auto vertical entirely — back from hub to platform main menu."""
    _clear_flow(user_id)
    auto_billing_flow.pop(user_id, None)
    auto_vertical_active.pop(user_id, None)
    auto_vertical_section.pop(user_id, None)
    lang = await _user_lang(user_id)
    await message.answer(
        t("main_menu", lang),
        reply_markup=await _main_menu_for(user_id),
    )


async def _open_cars_section(message: Message, user_id: int) -> None:
    lang = await _user_lang(user_id)
    auto_vertical_section[user_id] = "cars"
    await message.answer(
        t("auto_cars_title", lang),
        reply_markup=auto_vertical_menu(lang),
    )
    await message.answer(
        t("auto_quick_actions", lang),
        reply_markup=auto_vertical_actions_inline("overview"),
    )


async def _show_insurance(message: Message, user_id: int) -> None:
    auto_vertical_section[user_id] = "insurance"
    await show_partner_category(message, user_id, AutomotivePartnerType.INSURANCE.value)


async def _show_partner_category(message: Message, user_id: int, category: str) -> None:
    await show_partner_category(message, user_id, category)


async def _notify_owner_payment(bot: Bot, payment: dict, user_id: int) -> None:
    if not BOT_TOKEN:
        return
    try:
        await bot.send_message(
            OWNER_ID,
            "💳 Новый платёж на проверку\n\n"
            f"User: {user_id}\n"
            f"Plan: {payment.get('plan_code')}\n"
            f"Model: {payment.get('pricing_model')}\n"
            f"Method: {payment.get('payment_method')}\n"
            f"Amount: {payment.get('amount')} {payment.get('currency')}\n"
            f"Payment ID: {payment.get('id')}",
            reply_markup=auto_billing_owner_actions_inline(payment["id"]),
        )
    except Exception:
        logger.exception("Failed to notify owner about payment %s", payment.get("id"))


async def _schedule_marketing_for_car(
    message: Message,
    user_id: int,
    car: dict,
) -> None:
    try:
        result = await AutoMarketingEngineV1.schedule_car_campaign(
            user_id,
            car_id=uuid.UUID(car["id"]),
        )
    except AutoMarketingEngineError as exc:
        await message.answer(f"❌ {exc}", reply_markup=auto_vertical_menu(await _user_lang(user_id)))
        return

    campaign = result["campaign"]
    pubs = result["publications"]
    _clear_flow(user_id)
    await message.answer(
        "✅ Кампания создана\n\n"
        f"Название: {campaign['name']}\n"
        f"Каналов: {len(pubs)}\n"
        f"Статус: {campaign['status']}\n\n"
        "Публикации поставлены в очередь. Scheduler обработает их автоматически.",
        reply_markup=auto_vertical_menu(await _user_lang(user_id)),
    )
    log_audit(user_id, "create", "marketing_campaign", campaign["id"])


async def _handle_auto_vertical_screen(message: Message, user_id: int, screen: str) -> None:
    screen_key = _normalize_screen(screen)
    lang = await _user_lang(user_id)
    section = auto_vertical_section.get(user_id, "hub")

    if screen_key == "back":
        _clear_flow(user_id)
        auto_billing_flow.pop(user_id, None)
        if section == "cars":
            await _return_to_auto_hub(message, user_id)
            return
        if section != "hub":
            await _return_to_auto_hub(message, user_id)
            return
        await _exit_auto_vertical(message, user_id)
        return

    if screen_key == "back_to_hub":
        await _return_to_auto_hub(message, user_id)
        return

    if screen_key == "hub_cars":
        await _open_cars_section(message, user_id)
        return

    if screen_key == "hub_insurance":
        try:
            await _show_insurance(message, user_id)
        except Exception as exc:
            await message.answer(
                f"{category_header('INSURANCE', lang)}\n\n{exc}",
                reply_markup=auto_vertical_hub_menu(lang),
            )
        return

    category = hub_screen_to_category(screen_key)
    if category:
        auto_vertical_section[user_id] = category.lower()
        try:
            await _show_partner_category(message, user_id, category)
        except Exception as exc:
            await message.answer(
                f"{category_header(category, lang)}\n\n{exc}",
                reply_markup=auto_vertical_hub_menu(lang),
            )
        return

    if screen_key == "add_car":
        await _start_add_car(message, user_id)
        return

    if screen_key == "list_cars":
        await _show_car_list(message, user_id)
        return

    if screen_key == "search_car":
        await _start_search(message, user_id)
        return

    if screen_key == "profit_calc":
        await _start_profit_calculator(message, user_id)
        return

    if screen_key == "marketing":
        await _show_marketing(message, user_id)
        return

    if screen_key == "analytics":
        await _show_analytics(message, user_id)
        return

    if screen_key == "ai_manager":
        await _show_ai_manager(message, user_id)
        return

    if screen_key == "leads":
        await _show_leads(message, user_id)
        return

    if screen_key == "billing":
        await _show_billing(message, user_id)
        return

    if screen_key == "dealer_rates":
        await _show_dealer_rates(message, user_id)
        return

    if screen_key == "treasury":
        await _show_treasury(message, user_id)
        return

    if screen_key == "auto_settings":
        await _show_settings(message, user_id)
        return


async def handle_auto_menu_request(message: Message) -> None:
    user_id = message.from_user.id
    lang = await _user_lang(user_id)
    logger.info("Auto menu requested by %s", user_id)
    try:
        if not await can_access_automotive_ui(user_id):
            await message.answer(
                t("auto_no_access", lang),
                reply_markup=await _main_menu_for(user_id),
            )
            return

        auto_vertical_active[user_id] = True
        _clear_flow(user_id)
        auto_billing_flow.pop(user_id, None)
        log_audit(user_id, "open", "auto_vertical")
        await _open_auto_hub(message, user_id)
    except Exception:
        logger.exception("Automotive module unavailable for user %s", user_id)
        await message.answer(
            t("auto_unavailable", lang),
            reply_markup=await _main_menu_for(user_id),
        )


def _is_auto_main_entry(message: Message) -> bool:
    return resolve_auto_screen(message.text or "") == "main"


@auto_vertical_router.message(_is_auto_main_entry)
async def open_auto_vertical(message: Message) -> None:
    await handle_auto_menu_request(message)


@auto_vertical_router.message(F.text.in_({"🚗 Cars", "🚗 Auto"}))
async def open_auto_vertical_legacy(message: Message) -> None:
    await handle_auto_menu_request(message)


@auto_vertical_router.callback_query(F.data == "auto")
async def open_auto_vertical_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    logger.info("Auto menu requested by %s (callback)", user_id)
    if callback.message is None:
        await callback.answer("Automotive module temporarily unavailable.", show_alert=True)
        return
    try:
        if not await can_access_automotive_ui(user_id):
            await callback.answer("Нет доступа к модулю.", show_alert=True)
            return
        auto_vertical_active[user_id] = True
        _clear_flow(user_id)
        auto_billing_flow.pop(user_id, None)
        log_audit(user_id, "open", "auto_vertical", "callback")
        await _open_auto_hub(callback.message, user_id)
        await callback.answer()
    except Exception:
        logger.exception("Automotive module unavailable for user %s (callback)", user_id)
        await callback.answer("Automotive module temporarily unavailable.", show_alert=True)


@auto_vertical_router.message(
    lambda m: (
        resolve_auto_screen(m.text or "") is not None
        and resolve_auto_screen(m.text or "") != "main"
        and auto_vertical_active.get(m.from_user.id)
        and not auto_vertical_flow.get(m.from_user.id)
    )
)
async def auto_vertical_screen(message: Message) -> None:
    await _handle_auto_vertical_screen(message, message.from_user.id, message.text)


@auto_vertical_router.message(
    lambda m: auto_vertical_active.get(m.from_user.id) and auto_vertical_flow.get(m.from_user.id)
)
async def auto_vertical_flow_handler(message: Message) -> None:
    user_id = message.from_user.id
    flow = auto_vertical_flow.get(user_id, {})
    step = flow.get("step")
    data = flow.setdefault("data", {})
    text = (message.text or "").strip()
    lang = await _user_lang(user_id)

    screen_key = resolve_auto_screen(text)
    if screen_key is not None:
        _clear_flow(user_id)
        await _handle_auto_vertical_screen(message, user_id, text)
        return

    if is_back_button(text, lang):
        _clear_flow(user_id)
        if auto_vertical_section.get(user_id) == "cars":
            await _return_to_cars_menu(message, user_id)
        else:
            await _return_to_auto_hub(message, user_id)
        return

    if step == "make":
        if not text:
            await message.answer("Укажите марку автомобиля:")
            return
        data["make"] = text
        flow["step"] = "model"
        await message.answer("Укажите модель:")
        return

    if step == "model":
        if not text:
            await message.answer("Укажите модель:")
            return
        data["model"] = text
        flow["step"] = "year"
        await message.answer("Укажите год выпуска:")
        return

    if step == "year":
        if not text.isdigit() or len(text) != 4:
            await message.answer("Укажите год четырёхзначным числом (например 2022):")
            return
        data["year"] = int(text)
        flow["step"] = "color"
        await message.answer("Укажите цвет (или «-» чтобы пропустить):")
        return

    if step == "color":
        if text != "-":
            data["color"] = text
        flow["step"] = "mileage"
        await message.answer("Укажите пробег в км (или «-» чтобы пропустить):")
        return

    if step == "mileage":
        if text != "-":
            digits = "".join(ch for ch in text if ch.isdigit())
            if not digits:
                await message.answer("Укажите пробег числом или «-»:")
                return
            data["mileage"] = int(digits)
        flow["step"] = "purchase_price"
        await message.answer(
            "Введите цену закупки (число) или «-» чтобы пропустить:"
        )
        return

    if step == "purchase_price":
        fields: dict = {}
        if text != "-":
            try:
                fields["purchase_price"] = Decimal(text.replace(",", "."))
            except InvalidOperation:
                await message.answer("Введите число или «-»:")
                return
        if data.get("color"):
            fields["color"] = data["color"]
        if data.get("mileage") is not None:
            fields["mileage"] = data["mileage"]
        data["fields"] = fields
        flow["step"] = "optional_costs"
        await message.answer(
            "Доп. расходы одной строкой через пробел "
            "(delivery customs repair advertising) или «-»:\n"
            "Пример: 800 1200 500 200"
        )
        return

    if step == "optional_costs":
        fields = data.get("fields", {})
        if text != "-":
            parts = text.split()
            labels = ("delivery_cost", "customs_cost", "repair_cost", "advertising_cost")
            try:
                for idx, label in enumerate(labels):
                    if idx < len(parts):
                        fields[label] = Decimal(parts[idx].replace(",", "."))
            except InvalidOperation:
                await message.answer("Введите до 4 чисел или «-»:")
                return
        data["fields"] = fields
        flow["step"] = "vin_optional"
        await message.answer(
            "Хотите добавить VIN автомобиля?\n\n"
            "• Да\n"
            "• Нет"
        )
        return

    if step == "vin_optional":
        lowered = text.lower()
        if lowered in {"нет", "пропустить", "skip", "-"}:
            data["vin"] = None
            logger.info("ADD_CAR VIN_PRESENT=False user=%s", user_id)
            await _finalize_add_car(message, user_id, data)
            return
        if lowered in {"да", "yes", "добавить vin", "vin"}:
            flow["step"] = "vin_input"
            await message.answer("Введите VIN автомобиля:")
            return
        await message.answer("Выберите:\n• Да\n• Нет")
        return

    if step == "vin_input":
        lowered = text.lower()
        if lowered in {"нет", "пропустить", "skip", "-"}:
            data["vin"] = None
            logger.info("ADD_CAR VIN_PRESENT=False user=%s", user_id)
            await _finalize_add_car(message, user_id, data)
            return
        result = validate_vin(text)
        if not result["is_valid"]:
            await message.answer(
                "❌ Некорректный VIN:\n"
                + "\n".join(f"• {err}" for err in result["errors"])
                + "\n\nВведите VIN ещё раз или «Нет»:"
            )
            return
        data["vin"] = result["vin"]
        logger.info("ADD_CAR VIN_PRESENT=True user=%s", user_id)
        await _finalize_add_car(message, user_id, data)
        return

    if step == "search":
        _clear_flow(user_id)
        try:
            matched = await CarEngineV1.search_cars(user_id, text)
        except CarEngineError as exc:
            await message.answer(str(exc), reply_markup=auto_vertical_menu(await _user_lang(user_id)))
            return

        if not matched:
            await message.answer(
                f"🔎 По запросу «{text}» ничего не найдено.",
                reply_markup=auto_vertical_menu(await _user_lang(user_id)),
            )
            return

        await message.answer(
            f"🔎 Найдено: {len(matched)}",
            reply_markup=auto_vertical_car_list_inline(matched),
        )
        await message.answer("Выберите автомобиль:", reply_markup=auto_vertical_menu(await _user_lang(user_id)))
        return

    if step == "marketing_vin":
        try:
            car = await CarEngineV1.get_car_by_vin(user_id, text.upper())
        except CarEngineError:
            await message.answer(
                "Авто не найдено. Введите VIN из инвентаря или «⬅ Назад»:"
            )
            return
        await _schedule_marketing_for_car(message, user_id, car)
        return

    if step == "profit_vin":
        if text == "-":
            flow["step"] = "profit_purchase"
            await message.answer("Введите цену закупки (число):")
            return
        try:
            car = await CarEngineV1.get_car_by_vin(user_id, text.upper())
        except CarEngineError:
            await message.answer("Авто не найдено. Введите другой VIN или «-»:")
            return
        data["car_id"] = car["id"]
        flow["step"] = "profit_sale_for_car"
        await message.answer(
            _format_car_card(car) + "\n\nВведите цену продажи (число):"
        )
        return

    if step == "profit_sale_for_car":
        try:
            sale = Decimal(text.replace(",", "."))
        except InvalidOperation:
            await message.answer("Введите число (цена продажи):")
            return
        car_id = uuid.UUID(data["car_id"])
        _clear_flow(user_id)
        try:
            profit = await CarEngineV1.calculate_profit(
                user_id,
                car_id,
                sale_price=sale,
                persist=True,
            )
        except CarEngineError as exc:
            await message.answer(f"❌ {exc}", reply_markup=auto_vertical_menu(await _user_lang(user_id)))
            return
        await message.answer(
            _format_profit_breakdown(profit),
            reply_markup=auto_vertical_menu(await _user_lang(user_id)),
        )
        return

    if step == "profit_purchase":
        try:
            purchase = Decimal(text.replace(",", "."))
        except InvalidOperation:
            await message.answer("Введите число (цена закупки):")
            return
        data["purchase"] = purchase
        flow["step"] = "profit_extra_costs"
        await message.answer(
            "Доп. расходы (delivery customs repair advertising) или «-»:\n"
            "Пример: 800 1200 500 200"
        )
        return

    if step == "profit_extra_costs":
        delivery = customs = repair = advertising = Decimal("0")
        if text != "-":
            parts = text.split()
            try:
                values = [Decimal(p.replace(",", ".")) for p in parts[:4]]
                while len(values) < 4:
                    values.append(Decimal("0"))
                delivery, customs, repair, advertising = values
            except InvalidOperation:
                await message.answer("Введите до 4 чисел или «-»:")
                return
        data["delivery_cost"] = delivery
        data["customs_cost"] = customs
        data["repair_cost"] = repair
        data["advertising_cost"] = advertising
        flow["step"] = "profit_sale"
        await message.answer("Введите цену продажи (число):")
        return

    if step == "profit_sale":
        try:
            sale = Decimal(text.replace(",", "."))
        except InvalidOperation:
            await message.answer("Введите число (цена продажи):")
            return
        from repositories.car_repository import CarRepository

        profit = CarRepository.calculate_profit(
            purchase_price=data.get("purchase", Decimal("0")),
            delivery_cost=data.get("delivery_cost", Decimal("0")),
            customs_cost=data.get("customs_cost", Decimal("0")),
            repair_cost=data.get("repair_cost", Decimal("0")),
            advertising_cost=data.get("advertising_cost", Decimal("0")),
            sale_price=sale,
        )
        _clear_flow(user_id)
        await message.answer(
            _format_profit_breakdown(
                {key: str(value) if value is not None else None for key, value in profit.items()}
            ),
            reply_markup=auto_vertical_menu(await _user_lang(user_id)),
        )


@auto_vertical_router.callback_query(F.data.startswith("car:"))
async def auto_vertical_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    data = callback.data or ""

    if data == "car:noop:0":
        await callback.answer()
        return

    if not auto_vertical_active.get(user_id):
        await callback.answer("Откройте раздел 🚗 Авто", show_alert=True)
        return

    if data.startswith("car:open:"):
        car_id = data.split(":", 2)[2]
        try:
            car = await CarEngineV1.get_car(user_id, uuid.UUID(car_id))
            enriched = await DealerRateService.enrich_car_listings(user_id, [car])
            car = enriched[0] if enriched else car
        except (ValueError, CarEngineError) as exc:
            await callback.answer(str(exc), show_alert=True)
            return
        await callback.message.answer(
            _format_car_card(car),
            reply_markup=auto_vertical_menu(await _user_lang(user_id)),
        )
        await callback.answer()
        return

    action_map = {
        "car:action:add": "🚗 Добавить авто",
        "car:action:list": "📋 Список авто",
        "car:action:search": "🔍 Поиск авто",
        "car:action:profit": "💰 Калькулятор прибыли",
    }
    if data in action_map:
        await _handle_auto_vertical_screen(
            callback.message,
            user_id,
            action_map[data],
        )
        await callback.answer()
        return

    if data.startswith("car:section:back:"):
        await callback.message.answer(
            "🚗 Авто",
            reply_markup=auto_vertical_menu(await _user_lang(user_id)),
        )
        await callback.answer()
        return

    await callback.answer()


@auto_vertical_router.callback_query(F.data.startswith("billing:"))
async def auto_billing_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    data = callback.data or ""

    if data == "billing:back:menu":
        await callback.message.answer("🚗 Авто", reply_markup=auto_vertical_menu(await _user_lang(user_id)))
        await callback.answer()
        return

    if data == "billing:back:plans":
        await callback.message.answer(
            "💳 Тарифы:",
            reply_markup=auto_billing_plans_inline(),
        )
        await callback.answer()
        return

    if data.startswith("billing:back:pricing:"):
        plan_code = data.split(":")[-1]
        await callback.message.answer(
            f"Модель оплаты для {plan_code}:",
            reply_markup=auto_billing_pricing_inline(plan_code),
        )
        await callback.answer()
        return

    if data.startswith("billing:plan:"):
        plan_code = data.split(":")[2]
        await DealerOnboardingEngineV1.advance_for_user(
            user_id,
            OnboardingStepName.TARIFF_SELECTED.value,
            payload={"plan_code": plan_code},
            plan_code=plan_code,
        )
        text = PLAN_MARKETING.get(plan_code, plan_code)
        await callback.message.answer(
            f"{text}\n\nВыберите модель оплаты:",
            reply_markup=auto_billing_pricing_inline(plan_code),
        )
        await callback.answer()
        return

    if data.startswith("billing:pricing:"):
        _, _, plan_code, pricing_model = data.split(":", 3)
        auto_billing_flow[user_id] = {
            "plan_code": plan_code,
            "pricing_model": pricing_model,
        }
        await DealerOnboardingEngineV1.advance_for_user(
            user_id,
            OnboardingStepName.PRICING_MODEL_SELECTED.value,
            payload={"plan_code": plan_code, "pricing_model": pricing_model},
            plan_code=plan_code,
            pricing_model=pricing_model,
        )
        label = PRICING_MODEL_LABELS.get(pricing_model, pricing_model)
        await callback.message.answer(
            f"Plan: {plan_code}\nModel: {label}\n\nВыберите способ оплаты:",
            reply_markup=auto_billing_payment_inline(plan_code, pricing_model),
        )
        await callback.answer()
        return

    if data.startswith("billing:pay:"):
        _, _, plan_code, pricing_model, payment_method = data.split(":", 4)
        try:
            payment = await CommercialBillingEngineV1.create_payment_intent(
                user_id,
                plan_code=plan_code,
                pricing_model=pricing_model,
                payment_method=payment_method,
            )
        except CommercialBillingEngineError as exc:
            await callback.answer(str(exc), show_alert=True)
            return
        auto_billing_flow[user_id] = {
            "payment_id": payment["id"],
            "plan_code": plan_code,
            "pricing_model": pricing_model,
            "payment_method": payment_method,
            "awaiting_receipt": True,
        }
        await DealerOnboardingEngineV1.bind_payment(
            user_id,
            payment_id=uuid.UUID(payment["id"]),
            plan_code=plan_code,
            pricing_model=pricing_model,
            payment_method=payment_method,
        )
        method_label = PAYMENT_METHOD_LABELS.get(payment_method, payment_method)
        await callback.message.answer(
            "💳 Оплата\n\n"
            f"Plan: {plan_code}\n"
            f"Model: {PRICING_MODEL_LABELS.get(pricing_model, pricing_model)}\n"
            f"Method: {method_label}\n"
            f"Amount: {payment.get('amount')} {payment.get('currency')}\n\n"
            "Загрузите фото или PDF квитанции об оплате.",
            reply_markup=auto_vertical_menu(await _user_lang(user_id)),
        )
        await callback.answer()
        return

    if data.startswith("billing:approve:"):
        if not await is_billing_owner(user_id):
            await callback.answer("Owner only", show_alert=True)
            return
        payment_id = uuid.UUID(data.split(":")[2])
        try:
            result = await CommercialBillingEngineV1.approve_payment(user_id, payment_id)
        except CommercialBillingEngineError as exc:
            await callback.answer(str(exc), show_alert=True)
            return
        payment_row = result.get("payment") or {}
        client_user_id = payment_row.get("user_id")
        if client_user_id:
            onboarding = await DealerOnboardingEngineV1.on_payment_approved(
                payment_id=payment_id,
                tenant_id=uuid.UUID(result["tenant_id"]),
                client_user_id=int(client_user_id),
            )
        else:
            onboarding = None
        completion_note = ""
        if onboarding and onboarding.get("status") == "COMPLETED":
            completion_note = "\n\n🚗 Automotive menu activated for dealer."
        await callback.message.answer(
            "✅ Payment approved\n\n"
            f"Tenant: {result['tenant_id']}\n"
            f"Subscription: {result['subscription']['plan_code']}"
            f"{completion_note}",
        )
        await callback.answer("Approved")
        return

    if data.startswith("billing:reject:"):
        if not await is_billing_owner(user_id):
            await callback.answer("Owner only", show_alert=True)
            return
        payment_id = uuid.UUID(data.split(":")[2])
        try:
            await CommercialBillingEngineV1.reject_payment(user_id, payment_id)
        except CommercialBillingEngineError as exc:
            await callback.answer(str(exc), show_alert=True)
            return
        await callback.message.answer("❌ Payment rejected")
        await callback.answer("Rejected")
        return

    await callback.answer()


@auto_vertical_router.message(
    lambda m: auto_billing_flow.get(m.from_user.id, {}).get("awaiting_receipt")
    and (m.photo or m.document)
)
async def auto_billing_receipt_upload(message: Message, bot: Bot) -> None:
    user_id = message.from_user.id
    flow = auto_billing_flow.get(user_id, {})
    await _process_billing_receipt(message, bot, user_id, uuid.UUID(flow["payment_id"]))
    auto_billing_flow.pop(user_id, None)


@auto_vertical_router.message(F.photo | F.document)
async def auto_billing_receipt_upload_onboarding(message: Message, bot: Bot) -> None:
    user_id = message.from_user.id
    if auto_billing_flow.get(user_id, {}).get("awaiting_receipt"):
        return
    session = await DealerOnboardingEngineV1.get_awaiting_receipt_session(user_id)
    if not session or not session.get("payment_id"):
        return
    await _process_billing_receipt(
        message,
        bot,
        user_id,
        uuid.UUID(session["payment_id"]),
        from_onboarding=True,
    )


async def _process_billing_receipt(
    message: Message,
    bot: Bot,
    user_id: int,
    payment_id: uuid.UUID,
    *,
    from_onboarding: bool = False,
) -> None:

    file_id = None
    file_unique_id = None
    mime_type = None
    if message.photo:
        photo = message.photo[-1]
        file_id = photo.file_id
        file_unique_id = photo.file_unique_id
        mime_type = "image/jpeg"
    elif message.document:
        file_id = message.document.file_id
        file_unique_id = message.document.file_unique_id
        mime_type = message.document.mime_type

    if not file_id:
        await message.answer("Отправьте фото или документ квитанции.")
        return

    try:
        result = await CommercialBillingEngineV1.attach_receipt(
            user_id,
            payment_id,
            telegram_file_id=file_id,
            telegram_file_unique_id=file_unique_id,
            mime_type=mime_type,
        )
        payment_view = await CommercialBillingEngineV1.get_user_subscription_view(user_id)
        pending = payment_view.get("pending_payment") or {}
        await _notify_owner_payment(bot, pending, user_id)
    except CommercialBillingEngineError as exc:
        await message.answer(f"❌ {exc}", reply_markup=auto_vertical_menu(await _user_lang(user_id)))
        return

    if from_onboarding:
        await DealerOnboardingEngineV1.mark_receipt_uploaded(user_id)

    menu = await _main_menu_for(user_id) if from_onboarding else auto_vertical_menu(await _user_lang(user_id))
    await message.answer(
        "✅ Квитанция получена\n\n"
        "Платёж отправлен на ручную проверку. "
        "После подтверждения OWNER будет активирован tenant и подписка.",
        reply_markup=menu,
    )
    log_audit(user_id, "upload", "payment_receipt", result.get("receipt_id"))


@auto_vertical_router.message(
    lambda m: (
        auto_vertical_active.get(m.from_user.id)
        and auto_vertical_section.get(m.from_user.id) == "ai_manager"
        and m.text
        and not m.text.startswith("/")
    )
)
async def auto_vertical_ai_manager_chat(message: Message) -> None:
    user_id = message.from_user.id
    lang = await _user_lang(user_id)
    from services.pg_ai_manager_engine import AiManagerEngineV1

    try:
        result = await AiManagerEngineV1.qualify_message(message.text or "")
        reply = result.get("reply") or "Спасибо за сообщение."
        meta = (
            f"\n\n📊 Score: {result.get('lead_score')} | "
            f"Priority: {result.get('priority')} | "
            f"Dept: {result.get('department')} | "
            f"Intent: {result.get('intent')}"
        )
        await message.answer(reply + meta, reply_markup=auto_vertical_menu(lang))
    except Exception as exc:
        logger.warning("AI manager chat failed user=%s", user_id, exc_info=True)
        await message.answer(
            "AI Manager временно недоступен. Попробуйте позже.",
            reply_markup=auto_vertical_menu(lang),
        )

