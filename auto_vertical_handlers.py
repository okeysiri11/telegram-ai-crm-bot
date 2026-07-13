# Auto Vertical Telegram UI v2 — Automotive module + commercial billing.

from __future__ import annotations

import logging
import uuid
from decimal import Decimal, InvalidOperation

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from config import BOT_TOKEN, OWNER_ID
from database import log_audit
from keyboards import (
    AUTO_VERTICAL_LEGACY_BUTTONS,
    AUTO_VERTICAL_MAIN_BUTTON,
    AUTO_VERTICAL_MENU_BUTTONS,
    auto_billing_owner_actions_inline,
    auto_billing_payment_inline,
    auto_billing_plans_inline,
    auto_billing_pricing_inline,
    auto_vertical_actions_inline,
    auto_vertical_car_list_inline,
    auto_vertical_menu,
    owner_main_menu,
)
from services.automotive_telegram_access import (
    can_access_automotive_ui,
    can_see_automotive_menu_button,
    is_billing_owner,
)
from services.pg_auto_marketing_engine import AutoMarketingEngineError, AutoMarketingEngineV1
from services.pg_car_engine import CarEngineError, CarEngineV1
from services.dealer_rate_service import DealerRateService
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
    build_auction_reference,
    build_history_event,
    decode_vin,
    validate_vin,
)
from database.session import get_session
from repositories.vin_repository import VinRepository

logger = logging.getLogger(__name__)

auto_vertical_router = Router()

auto_vertical_active: dict[int, bool] = {}
auto_vertical_flow: dict[int, dict] = {}
auto_billing_flow: dict[int, dict] = {}


def _normalize_screen(text: str) -> str:
    return AUTO_VERTICAL_LEGACY_BUTTONS.get(text, text)


async def _main_menu_for(user_id: int):
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
        await message.answer(str(exc), reply_markup=auto_vertical_menu())
        return

    if not cars:
        await message.answer(
            "📋 Список авто\n\nИнвентарь пуст. Добавьте автомобиль через «🚗 Добавить авто».",
            reply_markup=auto_vertical_menu(),
        )
        return

    await message.answer(
        f"📋 Список авто\n\nВсего: {len(cars)}",
        reply_markup=auto_vertical_car_list_inline(cars),
    )
    await message.answer("Выберите автомобиль:", reply_markup=auto_vertical_menu())


async def _start_add_car(message: Message, user_id: int) -> None:
    auto_vertical_flow[user_id] = {"step": "vin", "data": {}}
    await message.answer(
        "🚗 Добавить авто\n\nВведите VIN автомобиля (17 символов):",
        reply_markup=auto_vertical_menu(),
    )


async def _start_search(message: Message, user_id: int) -> None:
    auto_vertical_flow[user_id] = {"step": "search", "data": {}}
    await message.answer(
        "🔍 Поиск авто\n\n"
        "Введите VIN, марку, модель, год или статус:",
        reply_markup=auto_vertical_menu(),
    )


async def _start_profit_calculator(message: Message, user_id: int) -> None:
    auto_vertical_flow[user_id] = {"step": "profit_vin", "data": {}}
    await message.answer(
        "💰 Калькулятор прибыли\n\n"
        "Введите VIN существующего авто или «-» для ручного расчёта:",
        reply_markup=auto_vertical_menu(),
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
        await message.answer(str(exc), reply_markup=auto_vertical_menu())
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

    await message.answer("\n".join(lines), reply_markup=auto_vertical_menu())
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
        from database.models.partner_tenant_engine import PartnerTenant
        from sqlalchemy import select

        async with get_session() as session:
            result = await session.execute(select(PartnerTenant).limit(1))
            tenant = result.scalar_one_or_none()
        if tenant is None:
            await message.answer(
                "📊 Аналитика\n\nTenant не настроен.",
                reply_markup=auto_vertical_menu(),
            )
            return
        dashboard = await AnalyticsEngineV1.get_dashboard(user_id, tenant.id)
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
            reply_markup=auto_vertical_menu(),
        )
    except Exception as exc:
        await message.answer(
            f"📊 Аналитика\n\nДанные временно недоступны: {exc}",
            reply_markup=auto_vertical_menu(),
        )


async def _show_ai_manager(message: Message, user_id: int) -> None:
    await message.answer(
        "🤖 AI Менеджер\n\n"
        "AI Sales Agent: квалификация лидов, рекомендации авто, "
        "генерация офферов и follow-up.\n\n"
        "Клиенты получают AI Sales Assistant через /start.\n"
        "Менеджеры работают с лидами в разделе «👥 Лиды».",
        reply_markup=auto_vertical_menu(),
    )


async def _show_leads(message: Message, user_id: int) -> None:
    try:
        leads = await LeadAutomationEngineV1.list_leads(user_id, limit=10)
    except Exception as exc:
        await message.answer(
            f"👥 Лиды\n\nОшибка загрузки: {exc}",
            reply_markup=auto_vertical_menu(),
        )
        return
    if not leads:
        await message.answer(
            "👥 Лиды\n\nЛидов пока нет.",
            reply_markup=auto_vertical_menu(),
        )
        return
    lines = ["👥 Лиды", ""]
    for lead in leads[:10]:
        lines.append(
            f"• {lead.get('source', '—')} | {lead.get('status', '—')} | "
            f"{lead.get('customer_name') or lead.get('phone') or lead.get('id', '')[:8]}"
        )
    await message.answer("\n".join(lines), reply_markup=auto_vertical_menu())


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
    await message.answer("\n".join(lines), reply_markup=auto_vertical_menu())
    await message.answer("Тарифы:", reply_markup=auto_billing_plans_inline())
    if await is_billing_owner(user_id):
        pending = await CommercialBillingEngineV1.list_pending_for_owner(user_id)
        if pending:
            await message.answer(f"🔐 Owner: pending payments — {len(pending)}")


async def _show_settings(message: Message, user_id: int) -> None:
    await message.answer(
        "⚙ Настройки авто\n\n"
        "• Каналы продвижения: Telegram, Instagram, Facebook, TikTok\n"
        "• Уведомления о SLA и лидах\n"
        "• Интеграция с Car Engine и Marketing Engine\n\n"
        "Расширенные настройки — через админ-панель.",
        reply_markup=auto_vertical_menu(),
    )


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
        await message.answer(f"❌ {exc}", reply_markup=auto_vertical_menu())
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
        reply_markup=auto_vertical_menu(),
    )
    log_audit(user_id, "create", "marketing_campaign", campaign["id"])


async def _handle_auto_vertical_screen(message: Message, user_id: int, screen: str) -> None:
    screen = _normalize_screen(screen)
    if screen == "⬅ Назад":
        auto_vertical_active.pop(user_id, None)
        _clear_flow(user_id)
        auto_billing_flow.pop(user_id, None)
        await message.answer("Главное меню", reply_markup=await _main_menu_for(user_id))
        return

    if screen == "🚗 Добавить авто":
        await _start_add_car(message, user_id)
        return

    if screen == "📋 Список авто":
        await _show_car_list(message, user_id)
        return

    if screen == "🔍 Поиск авто":
        await _start_search(message, user_id)
        return

    if screen == "💰 Калькулятор прибыли":
        await _start_profit_calculator(message, user_id)
        return

    if screen == "📢 Продвижение":
        await _show_marketing(message, user_id)
        return

    if screen == "📊 Аналитика":
        await _show_analytics(message, user_id)
        return

    if screen == "🤖 AI Менеджер":
        await _show_ai_manager(message, user_id)
        return

    if screen == "👥 Лиды":
        await _show_leads(message, user_id)
        return

    if screen == "💳 Тарифы и услуги":
        await _show_billing(message, user_id)
        return

    if screen == "⚙ Настройки авто":
        await _show_settings(message, user_id)
        return


@auto_vertical_router.message(F.text.in_({AUTO_VERTICAL_MAIN_BUTTON, "🚗 Cars"}))
async def open_auto_vertical(message: Message) -> None:
    user_id = message.from_user.id
    if not await can_access_automotive_ui(user_id):
        await message.answer(
            "🚗 Авто\n\nНет доступа к модулю.",
            reply_markup=await _main_menu_for(user_id),
        )
        return

    auto_vertical_active[user_id] = True
    _clear_flow(user_id)
    auto_billing_flow.pop(user_id, None)
    log_audit(user_id, "open", "auto_vertical")

    await message.answer(
        "🚗 Авто\n\n"
        "Автомобильный модуль — инвентарь, продвижение, аналитика, "
        "AI менеджер, лиды и тарифы.\n\n"
        "Выберите раздел:",
        reply_markup=auto_vertical_menu(),
    )
    await message.answer(
        "Быстрые действия:",
        reply_markup=auto_vertical_actions_inline("overview"),
    )


@auto_vertical_router.message(
    lambda m: (
        (_normalize_screen(m.text or "") in AUTO_VERTICAL_MENU_BUTTONS
         or (m.text or "") in AUTO_VERTICAL_LEGACY_BUTTONS)
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

    if text == "⬅ Назад":
        _clear_flow(user_id)
        await message.answer("🚗 Авто", reply_markup=auto_vertical_menu())
        return

    if step == "vin":
        result = validate_vin(text)
        if not result["is_valid"]:
            await message.answer(
                "❌ Некорректный VIN:\n"
                + "\n".join(f"• {err}" for err in result["errors"])
                + "\n\nВведите корректный VIN (17 символов):"
            )
            return
        data["vin"] = result["vin"]
        decoded = decode_vin(result["vin"])
        data["decoded"] = decoded.get("decoded")
        flow["step"] = "make_model_year"
        hint = ""
        if decoded.get("decoded", {}).get("model_year"):
            hint = f"\n\nПодсказка по VIN: год {decoded['decoded']['model_year']}"
        await message.answer(
            "Введите марку, модель и год через пробел:\n"
            "Пример: Toyota Camry 2022" + hint
        )
        return

    if step == "make_model_year":
        parts = text.split()
        if len(parts) < 3 or not parts[-1].isdigit():
            await message.answer(
                "Формат: Make Model Year\nПример: Toyota Camry 2022"
            )
            return
        data["year"] = int(parts[-1])
        data["model"] = parts[-2]
        data["make"] = " ".join(parts[:-2])
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
        _clear_flow(user_id)
        try:
            car = await CarEngineV1.create_car(
                user_id,
                vin=data["vin"],
                make=data["make"],
                model=data["model"],
                year=data["year"],
                **fields,
            )
        except CarEngineError as exc:
            await message.answer(f"❌ {exc}", reply_markup=auto_vertical_menu())
            return

        async with get_session() as session:
            repo = VinRepository(session)
            report = await repo.upsert_from_decoder(
                data["vin"],
                car_id=uuid.UUID(car["id"]),
                created_by=user_id,
            )
            await repo.append_history(
                data["vin"],
                build_history_event(
                    "car_created",
                    source="telegram",
                    description="Car added via Telegram Cars module",
                    metadata={"car_id": car["id"]},
                ),
            )
            if not report.auction_references:
                await repo.add_auction_reference(
                    data["vin"],
                    build_auction_reference(
                        "manual_intake",
                        metadata={"channel": "telegram"},
                    ),
                )

        await message.answer(
            "✅ Автомобиль добавлен\n\n" + _format_car_card(car),
            reply_markup=auto_vertical_menu(),
        )
        log_audit(user_id, "create", "auto_vertical", data["vin"])
        return

    if step == "search":
        _clear_flow(user_id)
        try:
            matched = await CarEngineV1.search_cars(user_id, text)
        except CarEngineError as exc:
            await message.answer(str(exc), reply_markup=auto_vertical_menu())
            return

        if not matched:
            await message.answer(
                f"🔎 По запросу «{text}» ничего не найдено.",
                reply_markup=auto_vertical_menu(),
            )
            return

        await message.answer(
            f"🔎 Найдено: {len(matched)}",
            reply_markup=auto_vertical_car_list_inline(matched),
        )
        await message.answer("Выберите автомобиль:", reply_markup=auto_vertical_menu())
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
            await message.answer(f"❌ {exc}", reply_markup=auto_vertical_menu())
            return
        await message.answer(
            _format_profit_breakdown(profit),
            reply_markup=auto_vertical_menu(),
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
            reply_markup=auto_vertical_menu(),
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
            reply_markup=auto_vertical_menu(),
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
            reply_markup=auto_vertical_menu(),
        )
        await callback.answer()
        return

    await callback.answer()


@auto_vertical_router.callback_query(F.data.startswith("billing:"))
async def auto_billing_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    data = callback.data or ""

    if data == "billing:back:menu":
        await callback.message.answer("🚗 Авто", reply_markup=auto_vertical_menu())
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
            reply_markup=auto_vertical_menu(),
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
        await message.answer(f"❌ {exc}", reply_markup=auto_vertical_menu())
        return

    if from_onboarding:
        await DealerOnboardingEngineV1.mark_receipt_uploaded(user_id)

    menu = await _main_menu_for(user_id) if from_onboarding else auto_vertical_menu()
    await message.answer(
        "✅ Квитанция получена\n\n"
        "Платёж отправлен на ручную проверку. "
        "После подтверждения OWNER будет активирован tenant и подписка.",
        reply_markup=menu,
    )
    log_audit(user_id, "upload", "payment_receipt", result.get("receipt_id"))
