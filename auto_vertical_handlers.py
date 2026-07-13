# Auto Vertical Telegram UI v1 — Cars module handlers (Car Entity Engine).

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
from services.pg_car_engine import CarEngineError, CarEngineV1

auto_vertical_router = Router()

auto_vertical_active: dict[int, bool] = {}
auto_vertical_flow: dict[int, dict] = {}


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
    except CarEngineError as exc:
        await message.answer(str(exc), reply_markup=auto_vertical_menu())
        return

    if not cars:
        await message.answer(
            "📋 Car List\n\nИнвентарь пуст. Добавьте автомобиль через «➕ Add Car».",
            reply_markup=auto_vertical_menu(),
        )
        return

    await message.answer(
        f"📋 Car List\n\nВсего: {len(cars)}",
        reply_markup=auto_vertical_car_list_inline(cars),
    )
    await message.answer("Выберите автомобиль:", reply_markup=auto_vertical_menu())


async def _start_add_car(message: Message, user_id: int) -> None:
    auto_vertical_flow[user_id] = {"step": "vin", "data": {}}
    await message.answer(
        "➕ Add Car\n\nВведите VIN автомобиля (17 символов):",
        reply_markup=auto_vertical_menu(),
    )


async def _start_search(message: Message, user_id: int) -> None:
    auto_vertical_flow[user_id] = {"step": "search", "data": {}}
    await message.answer(
        "🔎 Search Car\n\n"
        "Введите VIN, марку, модель, год или статус:",
        reply_markup=auto_vertical_menu(),
    )


async def _start_profit_calculator(message: Message, user_id: int) -> None:
    auto_vertical_flow[user_id] = {"step": "profit_vin", "data": {}}
    await message.answer(
        "🧮 Profit Calculator\n\n"
        "Введите VIN существующего авто или «-» для ручного расчёта:",
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
    if not await CarEngineV1.user_can_access(user_id):
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
        await callback.answer("Откройте раздел 🚗 Cars", show_alert=True)
        return

    if data.startswith("car:open:"):
        car_id = data.split(":", 2)[2]
        try:
            car = await CarEngineV1.get_car(user_id, uuid.UUID(car_id))
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
