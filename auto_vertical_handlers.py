# Auto Vertical Telegram UI v1 — Cars module handlers.

from __future__ import annotations

import uuid
from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from database import log_audit
from keyboards import (
    AUTO_VERTICAL_MAIN_BUTTON,
    AUTO_VERTICAL_MENU_BUTTONS,
    auto_vertical_actions_inline,
    auto_vertical_car_list_inline,
    auto_vertical_menu,
    owner_main_menu,
)
from services.pg_automotive_inventory_engine import (
    AutomotiveInventoryEngineError,
    AutomotiveInventoryEngineV1,
)

auto_vertical_router = Router()

auto_vertical_active: dict[int, bool] = {}
auto_vertical_flow: dict[int, dict] = {}


def _format_vehicle_card(vehicle: dict) -> str:
    lines = [
        f"🚗 {vehicle.get('year', '—')} {vehicle.get('make', '')} {vehicle.get('model', '')}".strip(),
        f"VIN: {vehicle.get('vin', '—')}",
        f"Stock: {vehicle.get('stock_number', '—')}",
        f"Status: {vehicle.get('status', '—')}",
    ]
    if vehicle.get("mileage") is not None:
        lines.append(f"Mileage: {vehicle['mileage']}")
    if vehicle.get("purchase_price"):
        lines.append(f"Purchase: {vehicle['purchase_price']} {vehicle.get('currency', '')}".strip())
    if vehicle.get("target_price"):
        lines.append(f"Target: {vehicle['target_price']} {vehicle.get('currency', '')}".strip())
    if vehicle.get("sale_price"):
        lines.append(f"Sale: {vehicle['sale_price']} {vehicle.get('currency', '')}".strip())
    return "\n".join(lines)


def _format_profit_result(
    *,
    purchase: Decimal,
    sale: Decimal,
    currency: str = "USD",
) -> str:
    margin = sale - purchase
    margin_pct = (margin / purchase * Decimal("100")) if purchase > 0 else Decimal("0")
    roi_pct = margin_pct
    return (
        "🧮 Profit Calculator\n\n"
        f"Purchase: {purchase} {currency}\n"
        f"Sale: {sale} {currency}\n"
        f"Margin: {margin} {currency}\n"
        f"Margin %: {margin_pct.quantize(Decimal('0.01'))}%\n"
        f"ROI %: {roi_pct.quantize(Decimal('0.01'))}%"
    )


def _clear_flow(user_id: int) -> None:
    auto_vertical_flow.pop(user_id, None)


async def _show_car_list(message: Message, user_id: int) -> None:
    try:
        vehicles = await AutomotiveInventoryEngineV1.list_vehicles(user_id, limit=50)
    except AutomotiveInventoryEngineError as exc:
        await message.answer(str(exc), reply_markup=auto_vertical_menu())
        return

    if not vehicles:
        await message.answer(
            "📋 Car List\n\nИнвентарь пуст. Добавьте автомобиль через «➕ Add Car».",
            reply_markup=auto_vertical_menu(),
        )
        return

    await message.answer(
        f"📋 Car List\n\nВсего: {len(vehicles)}",
        reply_markup=auto_vertical_car_list_inline(vehicles),
    )
    await message.answer("Выберите автомобиль:", reply_markup=auto_vertical_menu())


async def _start_add_car(message: Message, user_id: int) -> None:
    auto_vertical_flow[user_id] = {"step": "vin", "data": {}}
    await message.answer(
        "➕ Add Car\n\nВведите VIN автомобиля:",
        reply_markup=auto_vertical_menu(),
    )


async def _start_search(message: Message, user_id: int) -> None:
    auto_vertical_flow[user_id] = {"step": "search", "data": {}}
    await message.answer(
        "🔎 Search Car\n\n"
        "Введите VIN, stock number, марку или модель:",
        reply_markup=auto_vertical_menu(),
    )


async def _start_profit_calculator(message: Message, user_id: int) -> None:
    auto_vertical_flow[user_id] = {"step": "profit_purchase", "data": {}}
    await message.answer(
        "🧮 Profit Calculator\n\nВведите цену закупки (число):",
        reply_markup=auto_vertical_menu(),
    )


async def _show_marketing(message: Message, user_id: int) -> None:
    await message.answer(
        "📣 Marketing\n\n"
        "Маркетинговый модуль:\n"
        "• публикация объявлений на площадках\n"
        "• синхронизация цен и фото\n"
        "• marketplace import jobs\n\n"
        "Раздел находится в разработке.",
        reply_markup=auto_vertical_menu(),
    )
    await message.answer(
        "Действия:",
        reply_markup=auto_vertical_actions_inline("marketing"),
    )
    log_audit(user_id, "open_stub", "auto_vertical", "marketing")


async def _handle_auto_vertical_screen(message: Message, user_id: int, screen: str) -> None:
    if screen == "⬅ Назад":
        auto_vertical_active.pop(user_id, None)
        _clear_flow(user_id)
        await message.answer("Главное меню", reply_markup=owner_main_menu())
        return

    if screen == "➕ Add Car":
        await _start_add_car(message, user_id)
        return

    if screen == "📋 Car List":
        await _show_car_list(message, user_id)
        return

    if screen == "🔎 Search Car":
        await _start_search(message, user_id)
        return

    if screen == "🧮 Profit Calculator":
        await _start_profit_calculator(message, user_id)
        return

    if screen == "📣 Marketing":
        await _show_marketing(message, user_id)


@auto_vertical_router.message(F.text == AUTO_VERTICAL_MAIN_BUTTON)
async def open_auto_vertical(message: Message) -> None:
    user_id = message.from_user.id
    if not await AutomotiveInventoryEngineV1.user_can_access(user_id):
        await message.answer(
            "🚗 Cars\n\nНет доступа к модулю.",
            reply_markup=owner_main_menu(),
        )
        return

    auto_vertical_active[user_id] = True
    _clear_flow(user_id)
    log_audit(user_id, "open", "auto_vertical")

    await message.answer(
        "🚗 Cars\n\n"
        "Автомобильный вертикаль — инвентарь, поиск, маржа и маркетинг.\n\n"
        "Выберите раздел:",
        reply_markup=auto_vertical_menu(),
    )
    await message.answer(
        "Быстрые действия:",
        reply_markup=auto_vertical_actions_inline("overview"),
    )


@auto_vertical_router.message(
    lambda m: (
        m.text in AUTO_VERTICAL_MENU_BUTTONS
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
        await message.answer("🚗 Cars", reply_markup=auto_vertical_menu())
        return

    if step == "vin":
        if len(text) < 5:
            await message.answer("VIN слишком короткий. Введите корректный VIN:")
            return
        data["vin"] = text.upper()
        flow["step"] = "make_model_year"
        await message.answer(
            "Введите марку, модель и год через пробел:\n"
            "Пример: Toyota Camry 2022"
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
        flow["step"] = "stock_number"
        await message.answer("Введите stock number (инвентарный номер):")
        return

    if step == "stock_number":
        data["stock_number"] = text
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
        _clear_flow(user_id)
        try:
            vehicle = await AutomotiveInventoryEngineV1.create_vehicle(
                user_id,
                vin=data["vin"],
                stock_number=data["stock_number"],
                make=data["make"],
                model=data["model"],
                year=data["year"],
                **fields,
            )
        except AutomotiveInventoryEngineError as exc:
            await message.answer(f"❌ {exc}", reply_markup=auto_vertical_menu())
            return

        await message.answer(
            "✅ Автомобиль добавлен\n\n" + _format_vehicle_card(vehicle),
            reply_markup=auto_vertical_menu(),
        )
        log_audit(user_id, "create", "auto_vertical", data["vin"])
        return

    if step == "search":
        _clear_flow(user_id)
        query = text.lower()
        try:
            vehicles = await AutomotiveInventoryEngineV1.list_vehicles(user_id, limit=200)
        except AutomotiveInventoryEngineError as exc:
            await message.answer(str(exc), reply_markup=auto_vertical_menu())
            return

        matched = [
            v
            for v in vehicles
            if query in (v.get("vin") or "").lower()
            or query in (v.get("stock_number") or "").lower()
            or query in (v.get("make") or "").lower()
            or query in (v.get("model") or "").lower()
        ]
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

    if step == "profit_purchase":
        try:
            purchase = Decimal(text.replace(",", "."))
        except InvalidOperation:
            await message.answer("Введите число (цена закупки):")
            return
        data["purchase"] = purchase
        flow["step"] = "profit_sale"
        await message.answer("Введите цену продажи (число):")
        return

    if step == "profit_sale":
        try:
            sale = Decimal(text.replace(",", "."))
        except InvalidOperation:
            await message.answer("Введите число (цена продажи):")
            return
        purchase = data.get("purchase", Decimal("0"))
        _clear_flow(user_id)
        await message.answer(
            _format_profit_result(purchase=purchase, sale=sale),
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
        await callback.answer("Откройте раздел 🚗 Cars", show_alert=True)
        return

    if data.startswith("car:open:"):
        vehicle_id = data.split(":", 2)[2]
        try:
            vid = uuid.UUID(vehicle_id)
            detail = await AutomotiveInventoryEngineV1.get_vehicle(user_id, vid)
        except (ValueError, AutomotiveInventoryEngineError) as exc:
            await callback.answer(str(exc), show_alert=True)
            return
        await callback.message.answer(
            _format_vehicle_card(detail["vehicle"]),
            reply_markup=auto_vertical_menu(),
        )
        await callback.answer()
        return

    action_map = {
        "car:action:add": "➕ Add Car",
        "car:action:list": "📋 Car List",
        "car:action:search": "🔎 Search Car",
        "car:action:profit": "🧮 Profit Calculator",
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
            "🚗 Cars",
            reply_markup=auto_vertical_menu(),
        )
        await callback.answer()
        return

    await callback.answer()
