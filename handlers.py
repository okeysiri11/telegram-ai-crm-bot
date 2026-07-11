from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from openrouter import ask_openrouter, extract_memory_from_message
from config import OWNER_ID, MANAGER_ID, MANAGERS
from database import (
    get_user_profile,
    save_profile_fields,
    format_memory_context,
    create_request,
    update_request_status,
    assign_manager,
    get_request_client,
    get_request_by_number,
    get_requests_by_status,
    get_requests_by_manager,
    get_all_active_requests,
    ensure_user,
    get_user_roles,
    assign_role,
    has_permission,
    has_module_access,
    log_audit,
    get_ai_settings,
    save_ai_settings,
    add_dialog_message,
    get_dialog_history_for_llm,
    clear_dialog_history,
    format_dialog_history_text,
    format_profile_text,
    format_memory_text,
    format_projects_text,
    format_tasks_text,
    format_ai_settings_text,
    TONE_LABELS,
    SYSTEM_MODULES,
    CALENDAR_SOURCE_MODULES,
    register_calendar_event,
    get_user_audit_log,
    get_user_activity_summary,
    get_module_ai_agent,
    format_users_list_text,
    format_roles_catalog_text,
    format_permissions_text,
    format_audit_log_text,
    SYSTEM_PERMISSIONS,
    create_calendar_event,
    get_calendar_event,
    get_calendar_events,
    update_calendar_event,
    delete_calendar_event,
    complete_calendar_event,
    reschedule_calendar_event,
    format_calendar_events_text,
    REPORT_TYPES,
    REPORT_BUTTON_TO_TYPE,
    build_report_filters,
    format_report_stub_text,
    export_report_excel,
    export_report_pdf,
    can_access_report,
    DRONE_SECTIONS,
    DRONE_BUTTON_TO_SECTION,
    DRONE_AI_CONTEXT_AREAS,
    can_access_drone_section,
    format_drone_section_stub,
    format_drone_ai_engineer_stub,
    format_drone_ai_context_stub,
    get_drone_ai_context,
    NOTIFICATION_CATEGORIES,
    NOTIFICATION_PRIORITIES,
    NOTIFICATION_STATUSES,
    create_notification,
    register_module_notification,
    get_notifications,
    mark_notification_read,
    archive_notification,
    format_notifications_text,
    get_notification_settings,
    format_notification_settings_text,
)
from keyboards import (
    owner_main_menu,
    crypto_otc_menu,
    agro_menu,
    agro_products_menu,
    product_actions_menu,
    manager_request_menu,
    crm_menu,
    law_module_menu,
    drone_module_menu,
    drone_module_actions_inline,
    cafe_beauty_module_menu,
    users_module_menu,
    users_module_actions_inline,
    reports_module_menu,
    reports_module_actions_inline,
    calendar_module_menu,
    calendar_event_actions_inline,
    module_inline_actions,
    ai_assistant_menu,
    ai_settings_menu,
    ai_tone_menu,
    ai_context_depth_menu,
    notifications_module_menu,
    notifications_module_actions_inline,
)
router = Router()

STATUS_NAMES = {
    "NEW": "🆕 Новая",
    "IN_PROGRESS": "⚙️ В работе",
    "DONE": "✅ Завершена"
}

def request_actions_keyboard(request_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶️ Взять в работу",
                    callback_data=f"take_{request_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Завершить",
                    callback_data=f"done_{request_id}"
                )
            ]
        ]
    )

# Память последних сообщений пользователей (legacy, CRM не использует)
dialog_history = {}
selected_product = {}
buy_requests = {}
waiting_buy_request = {}

# Состояния раздела AI Assistant
ai_assistant_active = {}
ai_settings_flow = {}
active_module = {}

MODULE_MENUS = {
    "law": law_module_menu,
    "drone": drone_module_menu,
    "cafe_beauty": cafe_beauty_module_menu,
    "users": users_module_menu,
    "reports": reports_module_menu,
    "calendar": calendar_module_menu,
}

MODULE_STUB_BUTTONS = {
    # Юриспруденция
    "📂 Дела",
    "📑 Документы",
    "📚 Законодательство",
    "⚖ Судебная практика",
    # Cafe & Beauty
    "☕ Cafe",
    "💄 Beauty",
    "📦 Склад",
}

DRONE_MENU_BUTTONS = {
    "📁 Проекты",
    "📋 Спецификации BOM",
    "🔋 Аккумуляторы",
    "⚡ Электроника",
    "📡 Связь и VTX",
    "🛰 Навигация и GPS",
    "🧠 Автопилоты",
    "📐 CAD и чертежи",
    "💰 Себестоимость",
    "📦 Закупки",
    "🤖 AI инженер",
    "⬅ Назад",
}

REPORTS_MENU_BUTTONS = {
    "💰 Финансы",
    "📈 Прибыль",
    "👥 Пользователи",
    "📅 Календарь",
    "🌾 Agro Trading",
    "💵 Crypto OTC",
    "🚁 Drone Engineering",
    "⚖️ Юриспруденция",
    "☕ Cafe & Beauty",
    "🤖 AI аналитика",
    "⬅ Назад",
}

NOTIFICATIONS_MENU_BUTTONS = {
    "📥 Новые",
    "📌 Важные",
    "📅 Напоминания",
    "⚙ Настройки уведомлений",
    "🗑 Архив",
    "⬅ Назад",
}

NOTIFICATIONS_STUB_MESSAGES = {
    "📥 Новые": "Новые уведомления",
    "📌 Важные": "Важные уведомления",
    "📅 Напоминания": "Напоминания",
    "⚙ Настройки уведомлений": "Настройки уведомлений",
    "🗑 Архив": "Архив уведомлений",
}

CALENDAR_MENU_BUTTONS = {
    "📅 Мои события",
    "➕ Новое событие",
    "🔔 Напоминания",
    "📆 Сегодня",
    "📈 Неделя",
    "📂 Все события",
    "⬅ Назад",
}

CALENDAR_STUB_MESSAGES = {
    "📅 Мои события": "Ваши события",
    "➕ Новое событие": "Создание события",
    "🔔 Напоминания": "Напоминания",
    "📆 Сегодня": "События на сегодня",
    "📈 Неделя": "События на неделю",
    "📂 Все события": "Все события системы",
}

USERS_MENU_BUTTONS = {
    "📋 Список пользователей",
    "➕ Добавить пользователя",
    "🛡 Роли",
    "🔐 Права доступа",
    "📊 Активность",
    "📝 Журнал действий",
    "⬅ Назад",
}

USERS_STUB_MESSAGES = {
    "📋 Список пользователей": "Список пользователей",
    "➕ Добавить пользователя": "Добавление пользователя",
    "🛡 Роли": "Управление ролями",
    "🔐 Права доступа": "Права доступа",
    "📊 Активность": "Активность пользователей",
    "📝 Журнал действий": "Журнал действий",
}


def _clear_ai_state(user_id: int):
    ai_settings_flow.pop(user_id, None)
    ai_assistant_active.pop(user_id, None)


async def _open_module(message: Message, module_key: str, title: str):
    _clear_ai_state(message.from_user.id)
    active_module[message.from_user.id] = module_key
    log_audit(message.from_user.id, "open", module_key)

    menu = MODULE_MENUS[module_key]()
    await message.answer(
        f"Раздел {title}\n\nРаздел находится в разработке.",
        reply_markup=menu,
    )
    # TODO: future implementation — module dashboard widgets
    await message.answer(
        f"Модуль: {SYSTEM_MODULES.get(module_key, title)}",
        reply_markup=module_inline_actions(module_key),
    )


async def _module_callback_answer(callback: CallbackQuery, module_key: str, action: str):
    user_id = callback.from_user.id

    if action == "ai":
        agent = get_module_ai_agent(module_key)
        # TODO: future implementation — launch dedicated module AI agent
        text = (
            f"🤖 AI агент модуля «{SYSTEM_MODULES.get(module_key, module_key)}»\n\n"
            "Раздел находится в разработке."
        )
        if agent:
            text += f"\n\nАгент: {agent}"
        await callback.message.answer(text)
        log_audit(user_id, "open_ai_agent", module_key)
    elif action == "back":
        menu_fn = MODULE_MENUS.get(module_key)
        if menu_fn:
            await callback.message.answer(
                f"Раздел {SYSTEM_MODULES.get(module_key, module_key)}",
                reply_markup=menu_fn(),
            )
        log_audit(user_id, "callback_back", module_key)
    else:
        # TODO: future implementation — handle module-specific inline actions
        await callback.message.answer(
            f"Действие «{action}» модуля «{SYSTEM_MODULES.get(module_key, module_key)}» "
            "находится в разработке."
        )

    await callback.answer()

TONE_BY_LABEL = {
    "Нейтральный": "neutral",
    "Формальный": "formal",
    "Дружелюбный": "friendly",
}

CONTEXT_DEPTH_BY_LABEL = {
    "10 сообщений": 10,
    "20 сообщений": 20,
    "40 сообщений": 40,
}

AI_MENU_BUTTONS = {
    "🤖 AI помощник",
    "📁 Мои проекты",
    "✅ Мои задачи",
    "💬 История диалогов",
    "⚙ Настройки AI",
    "⚙️ Настройки AI",
    "◀ Назад",
    "⬅️ К AI помощнику",
    "⬅️ К настройкам AI",
    "🎭 Тон общения",
    "🌐 Язык ответов",
    "📏 Глубина контекста",
    "🗑 Очистить историю",
    "Нейтральный",
    "Формальный",
    "Дружелюбный",
    "10 сообщений",
    "20 сообщений",
    "40 сообщений",
}


def _init_ai_user(message: Message):
    user = message.from_user
    ensure_user(user.id, user.full_name or "", user.username or "")
    if not get_user_roles(user.id):
        assign_role(user.id, "CLIENT")

AGRO_PRODUCTS = [
    "🌾 Пшеница",
    "🌽 Кукуруза",
    "🌻 Подсолнечное масло",
    "🫒 Оливковое масло",
    "🍎 Яблоки",
    "🧂 Сахар",
    "🫘 Нут",
    "🌱 Шрот",
    "🌾 Ячмень",
    "🌱 Рапс"
]

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:

    await message.answer(
        f"Ваш Telegram ID: {message.from_user.id}"
    )

    await message.answer(
        "Добро пожаловать в систему управления.",
        reply_markup=owner_main_menu()
    )

@router.message(F.text == "💰 Crypto OTC")
async def open_crypto_otc(message: Message):
    await message.answer(
        "Раздел Crypto OTC",
        reply_markup=crypto_otc_menu()
    )

@router.message(F.text == "🌾 Agro Trading")
async def open_agro(message: Message):
    await message.answer(
        "Раздел Agro Trading",
        reply_markup=agro_menu()
    ) 

@router.message(F.text == "🌾 Товары")
async def open_agro_products(message: Message):
    await message.answer(
        "Выберите товарную группу:",
        reply_markup=agro_products_menu()
    ) 

@router.message(F.text.in_(AGRO_PRODUCTS))
async def open_product(message: Message):
    user_id = message.from_user.id

    selected_product[user_id] = message.text

    await message.answer(
        f"Выбран товар: {message.text}\n\n"
        "Выберите действие:",
        reply_markup=product_actions_menu()
    )
@router.message(F.text == "🟢 Купить")
async def buy_product(message: Message):
    user_id = message.from_user.id

    product = selected_product.get(user_id, "товар")

    buy_requests[user_id] = {
        "product": product
    }

    await message.answer(
        f"""🟢 Новая заявка на покупку

Товар: {product}

Отправьте одним сообщением:

Страна:
Объем:
Качество:
Условия поставки:
Способ оплаты:

Пример:

Страна: Египет
Объем: 10000 тонн
Качество: 11.5% протеин
Условия: CIF Alexandria
Оплата: LC
"""
    )

    waiting_buy_request[user_id] = True


# ==========================================================
# SYSTEM MODULES (infrastructure stubs)
# ==========================================================

@router.message(F.text == "⚖ Юриспруденция")
async def open_law_module(message: Message):
    # TODO: future implementation — law module business logic
    await _open_module(message, "law", "Юриспруденция")


@router.message(F.text == "🚁 Drone Engineering")
async def open_drone_module(message: Message):
    # TODO: future implementation — drone engineering dashboard
    _clear_ai_state(message.from_user.id)
    active_module[message.from_user.id] = "drone"
    log_audit(message.from_user.id, "open", "drone")

    if not has_module_access(message.from_user.id, "drone"):
        await message.answer(
            "🚁 Drone Engineering\n\n"
            "У вас нет доступа к модулю.\n"
            "Раздел находится в разработке.",
            reply_markup=owner_main_menu(),
        )
        return

    sections = ", ".join(DRONE_SECTIONS.values())
    await message.answer(
        f"🚁 Drone Engineering\n\n"
        f"Инженерный модуль системы.\n"
        f"Разделы: {sections}\n\n"
        "Раздел находится в разработке.",
        reply_markup=drone_module_menu(),
    )
    await message.answer(
        "Дополнительно:",
        reply_markup=drone_module_actions_inline("overview"),
    )


@router.message(
    lambda m: (
        m.text in DRONE_MENU_BUTTONS
        and active_module.get(m.from_user.id) == "drone"
    )
)
async def drone_screen(message: Message):
    screen = message.text
    user_id = message.from_user.id

    if screen == "⬅ Назад":
        active_module.pop(user_id, None)
        await message.answer("Главное меню", reply_markup=owner_main_menu())
        return

    if not has_module_access(user_id, "drone"):
        await message.answer(
            "Нет доступа к модулю «Drone Engineering».",
            reply_markup=owner_main_menu(),
        )
        return

    section_key = DRONE_BUTTON_TO_SECTION.get(screen, "overview")

    if not can_access_drone_section(user_id, section_key):
        await message.answer(
            f"{screen}\n\nНет доступа к этому разделу.",
            reply_markup=drone_module_menu(),
        )
        return

    if section_key == "ai_engineer":
        await message.answer(
            format_drone_ai_engineer_stub(user_id),
            reply_markup=drone_module_menu(),
        )
        await message.answer(
            "Контекст AI инженера:",
            reply_markup=drone_module_actions_inline(section_key),
        )
        log_audit(user_id, "open_stub", "drone", section_key)
        return

    await message.answer(
        format_drone_section_stub(section_key, user_id),
        reply_markup=drone_module_menu(),
    )
    await message.answer(
        "Действия раздела:",
        reply_markup=drone_module_actions_inline(section_key),
    )
    log_audit(user_id, "open_stub", "drone", section_key)


@router.message(F.text == "☕ Cafe & Beauty")
async def open_cafe_beauty_module(message: Message):
    # TODO: future implementation — cafe & beauty module business logic
    await _open_module(message, "cafe_beauty", "Cafe & Beauty")


@router.message(F.text == "👥 Пользователи")
async def open_users_module(message: Message):
    # TODO: future implementation — users dashboard and access overview
    _init_ai_user(message)
    _clear_ai_state(message.from_user.id)
    active_module[message.from_user.id] = "users"
    log_audit(message.from_user.id, "open", "users")

    if not has_permission(message.from_user.id, "users_access"):
        await message.answer(
            "👥 Пользователи\n\n"
            "У вас нет доступа к модулю управления пользователями.\n"
            "Раздел находится в разработке.",
            reply_markup=owner_main_menu(),
        )
        return

    perms = ", ".join(SYSTEM_PERMISSIONS)
    await message.answer(
        f"👥 Пользователи\n\n"
        f"Центральный модуль управления доступом.\n"
        f"Права системы: {perms}\n\n"
        "Раздел находится в разработке.",
        reply_markup=users_module_menu(),
    )
    await message.answer(
        "Дополнительно:",
        reply_markup=users_module_actions_inline(),
    )


@router.message(F.text.in_(USERS_MENU_BUTTONS))
async def users_screen(message: Message):
    screen = message.text
    user_id = message.from_user.id
    active_module[user_id] = "users"

    if screen == "⬅ Назад":
        active_module.pop(user_id, None)
        await message.answer("Главное меню", reply_markup=owner_main_menu())
        return

    if not has_permission(user_id, "users_access"):
        await message.answer(
            "Нет доступа к модулю «Пользователи».",
            reply_markup=owner_main_menu(),
        )
        return

    title = USERS_STUB_MESSAGES.get(screen, screen)

    if screen == "📋 Список пользователей":
        await message.answer(
            f"{title}\n\n{format_users_list_text()}",
            reply_markup=users_module_menu(),
        )
        log_audit(user_id, "open_stub", "users", screen)
        return

    if screen == "🛡 Роли":
        await message.answer(
            f"{title}\n\n{format_roles_catalog_text()}\n\n"
            "Изменение ролей через Telegram пока недоступно.",
            reply_markup=users_module_menu(),
        )
        log_audit(user_id, "open_stub", "users", screen)
        return

    if screen == "🔐 Права доступа":
        await message.answer(
            format_permissions_text(user_id),
            reply_markup=users_module_menu(),
        )
        log_audit(user_id, "open_stub", "users", screen)
        return

    if screen == "📊 Активность":
        await message.answer(
            f"{title}\n\n{get_user_activity_summary(user_id)}",
            reply_markup=users_module_menu(),
        )
        log_audit(user_id, "open_stub", "users", screen)
        return

    if screen == "📝 Журнал действий":
        await message.answer(
            f"{title}\n\n{format_audit_log_text()}",
            reply_markup=users_module_menu(),
        )
        log_audit(user_id, "open_stub", "users", screen)
        return

    # TODO: future implementation — add user wizard
    await message.answer(
        f"{title}\n\n"
        "Добавление пользователей через Telegram пока недоступно.\n"
        "Раздел находится в разработке.",
        reply_markup=users_module_menu(),
    )
    log_audit(user_id, "open_stub", "users", screen)


@router.message(F.text == "📊 Отчеты")
async def open_reports_module(message: Message):
    # TODO: future implementation — reports dashboard and KPI widgets
    _clear_ai_state(message.from_user.id)
    active_module[message.from_user.id] = "reports"
    log_audit(message.from_user.id, "open", "reports")

    if not has_permission(message.from_user.id, "reports_access"):
        await message.answer(
            "📊 Отчеты\n\n"
            "У вас нет доступа к модулю отчетов.\n"
            "Раздел находится в разработке.",
            reply_markup=owner_main_menu(),
        )
        return

    types_list = ", ".join(REPORT_TYPES.values())
    await message.answer(
        f"📊 Отчеты\n\n"
        f"Центральный модуль отчетности.\n"
        f"Доступные отчеты: {types_list}\n\n"
        "Раздел находится в разработке.",
        reply_markup=reports_module_menu(),
    )
    await message.answer(
        "Дополнительно:",
        reply_markup=reports_module_actions_inline("summary"),
    )


@router.message(
    lambda m: (
        m.text in REPORTS_MENU_BUTTONS
        and active_module.get(m.from_user.id) == "reports"
    )
)
async def reports_screen(message: Message):
    screen = message.text
    user_id = message.from_user.id

    if screen == "⬅ Назад":
        active_module.pop(user_id, None)
        await message.answer("Главное меню", reply_markup=owner_main_menu())
        return

    if not has_permission(user_id, "reports_access"):
        await message.answer(
            "Нет доступа к модулю «Отчеты».",
            reply_markup=owner_main_menu(),
        )
        return

    report_type = REPORT_BUTTON_TO_TYPE.get(screen, "summary")

    if not can_access_report(user_id, report_type):
        await message.answer(
            f"{screen}\n\nНет доступа к этому отчету.",
            reply_markup=reports_module_menu(),
        )
        return

    filters = build_report_filters()
    await message.answer(
        format_report_stub_text(report_type, user_id, filters),
        reply_markup=reports_module_menu(),
    )
    await message.answer(
        "Действия с отчетом:",
        reply_markup=reports_module_actions_inline(report_type),
    )
    log_audit(user_id, "open_stub", "reports", report_type)


@router.message(F.text == "🔔 Уведомления")
async def open_notifications_module(message: Message):
    # TODO: future implementation — notifications dashboard and unread badge
    _init_ai_user(message)
    _clear_ai_state(message.from_user.id)
    active_module[message.from_user.id] = "notifications"
    log_audit(message.from_user.id, "open", "notifications")

    categories = ", ".join(NOTIFICATION_CATEGORIES.values())
    await message.answer(
        f"🔔 Уведомления\n\n"
        f"Центральный модуль уведомлений.\n"
        f"Категории: {categories}\n"
        f"Приоритеты: {', '.join(NOTIFICATION_PRIORITIES)}\n"
        f"Статусы: {', '.join(NOTIFICATION_STATUSES)}\n\n"
        "Раздел находится в разработке.",
        reply_markup=notifications_module_menu(),
    )
    await message.answer(
        "Дополнительно:",
        reply_markup=notifications_module_actions_inline(),
    )


@router.message(
    lambda m: (
        m.text in NOTIFICATIONS_MENU_BUTTONS
        and active_module.get(m.from_user.id) == "notifications"
    )
)
async def notifications_screen(message: Message):
    screen = message.text
    user_id = message.from_user.id

    if screen == "⬅ Назад":
        active_module.pop(user_id, None)
        await message.answer("Главное меню", reply_markup=owner_main_menu())
        return

    title = NOTIFICATIONS_STUB_MESSAGES.get(screen, screen)

    if screen == "📥 Новые":
        text = format_notifications_text(user_id, status="NEW")
        await message.answer(
            f"{title}\n\n{text}",
            reply_markup=notifications_module_menu(),
        )
        log_audit(user_id, "open_stub", "notifications", "new")
        return

    if screen == "📌 Важные":
        text = format_notifications_text(user_id, important_only=True)
        await message.answer(
            f"{title}\n\n{text}",
            reply_markup=notifications_module_menu(),
        )
        log_audit(user_id, "open_stub", "notifications", "important")
        return

    if screen == "📅 Напоминания":
        text = format_notifications_text(user_id, reminders_only=True)
        await message.answer(
            f"{title}\n\n{text}",
            reply_markup=notifications_module_menu(),
        )
        log_audit(user_id, "open_stub", "notifications", "reminders")
        return

    if screen == "⚙ Настройки уведомлений":
        await message.answer(
            format_notification_settings_text(user_id),
            reply_markup=notifications_module_menu(),
        )
        log_audit(user_id, "open_stub", "notifications", "settings")
        return

    if screen == "🗑 Архив":
        text = format_notifications_text(user_id, status="ARCHIVED")
        await message.answer(
            f"{title}\n\n{text}",
            reply_markup=notifications_module_menu(),
        )
        log_audit(user_id, "open_stub", "notifications", "archive")
        return

    await message.answer(
        f"{title}\n\nРаздел находится в разработке.",
        reply_markup=notifications_module_menu(),
    )
    log_audit(user_id, "open_stub", "notifications", screen)


@router.message(F.text == "📅 Календарь")
async def open_calendar_module(message: Message):
    # TODO: future implementation — calendar dashboard and widgets
    _clear_ai_state(message.from_user.id)
    active_module[message.from_user.id] = "calendar"
    log_audit(message.from_user.id, "open", "calendar")

    sources = ", ".join(CALENDAR_SOURCE_MODULES)
    await message.answer(
        f"📅 Календарь\n\n"
        f"Центральный модуль системы.\n"
        f"Источники событий: {sources}\n\n"
        "Раздел находится в разработке.",
        reply_markup=calendar_module_menu(),
    )
    await message.answer(
        "Дополнительно:",
        reply_markup=module_inline_actions("calendar"),
    )


@router.message(F.text.in_(CALENDAR_MENU_BUTTONS))
async def calendar_screen(message: Message):
    screen = message.text
    user_id = message.from_user.id
    active_module[user_id] = "calendar"

    if screen == "⬅ Назад":
        active_module.pop(user_id, None)
        await message.answer("Главное меню", reply_markup=owner_main_menu())
        return

    title = CALENDAR_STUB_MESSAGES.get(screen, screen)

    if screen == "📅 Мои события":
        text = format_calendar_events_text(user_id)
        await message.answer(
            f"{title}\n\n{text}\n\n"
            f"Источники: {', '.join(CALENDAR_SOURCE_MODULES)}",
            reply_markup=calendar_module_menu(),
        )
        log_audit(user_id, "open_stub", "calendar", screen)
        return

    if screen == "📂 Все события":
        # TODO: future implementation — all events across modules and users
        text = format_calendar_events_text(user_id, limit=20)
        await message.answer(
            f"{title}\n\n{text}\n\nРаздел находится в разработке.",
            reply_markup=calendar_module_menu(),
        )
        log_audit(user_id, "open_stub", "calendar", screen)
        return

    if screen == "➕ Новое событие":
        # TODO: future implementation — interactive event creation wizard
        await message.answer(
            f"{title}\n\n"
            "Создание, редактирование, удаление, завершение и перенос событий "
            "будут доступны в следующих версиях.\n\n"
            "Раздел находится в разработке.",
            reply_markup=calendar_module_menu(),
        )
        await message.answer(
            "Действия с событиями (заглушка):",
            reply_markup=calendar_event_actions_inline(0),
        )
        log_audit(user_id, "open_stub", "calendar", screen)
        return

    # TODO: future implementation — today, week, reminders filters
    await message.answer(
        f"{title}\n\nРаздел находится в разработке.",
        reply_markup=calendar_module_menu(),
    )
    log_audit(user_id, "open_stub", "calendar", screen)


@router.message(F.text.in_(MODULE_STUB_BUTTONS))
async def module_stub_screen(message: Message):
    screen = message.text
    module_key = active_module.get(message.from_user.id, "unknown")

    log_audit(message.from_user.id, "open_stub", module_key, screen)
    await message.answer(
        f"{screen}\n\nРаздел находится в разработке.",
        reply_markup=MODULE_MENUS.get(module_key, owner_main_menu)(),
    )


@router.callback_query(F.data.startswith("mod:law:"))
async def law_module_callback(callback: CallbackQuery):
    action = callback.data.split(":", 2)[2]
    await _module_callback_answer(callback, "law", action)


@router.callback_query(F.data.startswith("mod:drone:"))
async def drone_module_callback(callback: CallbackQuery):
    action = callback.data.split(":", 2)[2]
    await _module_callback_answer(callback, "drone", action)


@router.callback_query(F.data == "drn:ai:open")
async def drone_ai_engineer_callback(callback: CallbackQuery):
    # TODO: future implementation — launch drone AI engineer chat
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.answer(
        format_drone_ai_engineer_stub(user_id),
        reply_markup=drone_module_menu(),
    )
    log_audit(user_id, "drone_stub", "drone", "ai_engineer")


@router.callback_query(F.data.startswith("drn:ai:context:"))
async def drone_ai_context_callback(callback: CallbackQuery):
    # TODO: future implementation — load AI context for projects, BOM, etc.
    area = callback.data.split(":")[-1]
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.answer(
        format_drone_ai_context_stub(area, user_id),
        reply_markup=drone_module_menu(),
    )
    log_audit(user_id, "drone_stub", "drone", f"ai_context:{area}")


@router.callback_query(F.data.startswith("drn:section:back:"))
async def drone_section_back_callback(callback: CallbackQuery):
    # TODO: future implementation — restore section state
    await callback.answer()
    await callback.message.answer(
        "🚁 Drone Engineering",
        reply_markup=drone_module_menu(),
    )
    log_audit(callback.from_user.id, "drone_stub", "drone", "section_back")


@router.callback_query(F.data.startswith("mod:cafe_beauty:"))
async def cafe_beauty_module_callback(callback: CallbackQuery):
    action = callback.data.split(":", 2)[2]
    await _module_callback_answer(callback, "cafe_beauty", action)


@router.callback_query(F.data.startswith("mod:users:"))
async def users_module_callback(callback: CallbackQuery):
    action = callback.data.split(":", 2)[2]
    await _module_callback_answer(callback, "users", action)


@router.callback_query(F.data == "usr:user:add")
async def users_add_callback(callback: CallbackQuery):
    # TODO: future implementation — add user via Telegram
    await callback.answer()
    await callback.message.answer(
        "➕ Добавить пользователя\n\n"
        "Изменение пользователей через Telegram пока недоступно.\n"
        "Раздел находится в разработке.",
        reply_markup=users_module_menu(),
    )
    log_audit(callback.from_user.id, "users_stub", "users", "add")


@router.callback_query(F.data == "usr:roles:view")
async def users_roles_callback(callback: CallbackQuery):
    # TODO: future implementation — assign_role / revoke_role via Telegram
    await callback.answer()
    await callback.message.answer(
        f"🛡 Роли\n\n{format_roles_catalog_text()}\n\n"
        "Назначение и отзыв ролей через Telegram пока недоступны.",
        reply_markup=users_module_menu(),
    )
    log_audit(callback.from_user.id, "users_stub", "users", "roles")


@router.callback_query(F.data == "usr:permissions:view")
async def users_permissions_callback(callback: CallbackQuery):
    # TODO: future implementation — edit permission matrix
    await callback.answer()
    await callback.message.answer(
        format_permissions_text(callback.from_user.id),
        reply_markup=users_module_menu(),
    )
    log_audit(callback.from_user.id, "users_stub", "users", "permissions")


@router.callback_query(F.data == "usr:audit:view")
async def users_audit_callback(callback: CallbackQuery):
    # TODO: future implementation — audit log filters
    await callback.answer()
    await callback.message.answer(
        f"📝 Журнал действий\n\n{format_audit_log_text()}",
        reply_markup=users_module_menu(),
    )
    log_audit(callback.from_user.id, "users_stub", "users", "audit")


@router.callback_query(F.data.startswith("mod:reports:"))
async def reports_module_callback(callback: CallbackQuery):
    action = callback.data.split(":", 2)[2]
    await _module_callback_answer(callback, "reports", action)


@router.callback_query(F.data.startswith("rpt:filter:date:"))
async def reports_filter_date_callback(callback: CallbackQuery):
    # TODO: future implementation — date range picker
    report_type = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"📅 Фильтр по датам\n\n"
        f"Отчет: {REPORT_TYPES.get(report_type, report_type)}\n\n"
        "Выбор периода находится в разработке.",
        reply_markup=reports_module_menu(),
    )
    log_audit(callback.from_user.id, "reports_stub", "reports", f"filter_date:{report_type}")


@router.callback_query(F.data.startswith("rpt:filter:user:"))
async def reports_filter_user_callback(callback: CallbackQuery):
    # TODO: future implementation — user filter selector
    report_type = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"👤 Фильтр по пользователю\n\n"
        f"Отчет: {REPORT_TYPES.get(report_type, report_type)}\n\n"
        "Фильтрация по пользователям находится в разработке.",
        reply_markup=reports_module_menu(),
    )
    log_audit(callback.from_user.id, "reports_stub", "reports", f"filter_user:{report_type}")


@router.callback_query(F.data.startswith("rpt:filter:department:"))
async def reports_filter_department_callback(callback: CallbackQuery):
    # TODO: future implementation — department filter selector
    report_type = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"🏢 Фильтр по отделу\n\n"
        f"Отчет: {REPORT_TYPES.get(report_type, report_type)}\n\n"
        "Фильтрация по отделам находится в разработке.",
        reply_markup=reports_module_menu(),
    )
    log_audit(callback.from_user.id, "reports_stub", "reports", f"filter_department:{report_type}")


@router.callback_query(F.data.startswith("rpt:export:excel:"))
async def reports_export_excel_callback(callback: CallbackQuery):
    # TODO: future implementation — send Excel file to user
    report_type = callback.data.split(":")[-1]
    user_id = callback.from_user.id
    await callback.answer()
    path = export_report_excel(report_type, user_id, build_report_filters())
    await callback.message.answer(
        f"📊 Экспорт Excel\n\n"
        f"Отчет: {REPORT_TYPES.get(report_type, report_type)}\n\n"
        f"{'Файл: ' + path if path else 'Экспорт в Excel находится в разработке.'}",
        reply_markup=reports_module_menu(),
    )
    log_audit(user_id, "reports_stub", "reports", f"export_excel:{report_type}")


@router.callback_query(F.data.startswith("rpt:export:pdf:"))
async def reports_export_pdf_callback(callback: CallbackQuery):
    # TODO: future implementation — send PDF file to user
    report_type = callback.data.split(":")[-1]
    user_id = callback.from_user.id
    await callback.answer()
    path = export_report_pdf(report_type, user_id, build_report_filters())
    await callback.message.answer(
        f"📄 Экспорт PDF\n\n"
        f"Отчет: {REPORT_TYPES.get(report_type, report_type)}\n\n"
        f"{'Файл: ' + path if path else 'Экспорт в PDF находится в разработке.'}",
        reply_markup=reports_module_menu(),
    )
    log_audit(user_id, "reports_stub", "reports", f"export_pdf:{report_type}")


@router.callback_query(F.data == "ntf:action:read_all")
async def notifications_read_all_callback(callback: CallbackQuery):
    # TODO: future implementation — mark all notifications as READ
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.answer(
        "✅ Прочитать все\n\n"
        "Массовая отметка прочитанными находится в разработке.",
        reply_markup=notifications_module_menu(),
    )
    log_audit(user_id, "notifications_stub", "notifications", "read_all")


@router.callback_query(F.data == "ntf:action:archive_all")
async def notifications_archive_all_callback(callback: CallbackQuery):
    # TODO: future implementation — archive all read notifications
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.answer(
        "🗑 В архив\n\n"
        "Массовая архивация находится в разработке.",
        reply_markup=notifications_module_menu(),
    )
    log_audit(user_id, "notifications_stub", "notifications", "archive_all")


@router.callback_query(F.data == "ntf:settings:open")
async def notifications_settings_callback(callback: CallbackQuery):
    # TODO: future implementation — interactive notification settings
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.answer(
        format_notification_settings_text(user_id),
        reply_markup=notifications_module_menu(),
    )
    log_audit(user_id, "notifications_stub", "notifications", "settings")


@router.callback_query(F.data.startswith("mod:calendar:"))
async def calendar_module_callback(callback: CallbackQuery):
    action = callback.data.split(":", 2)[2]
    await _module_callback_answer(callback, "calendar", action)


@router.callback_query(F.data == "cal:event:create")
async def calendar_event_create_callback(callback: CallbackQuery):
    # TODO: future implementation — event creation flow
    await callback.answer()
    await callback.message.answer(
        "➕ Создание события\n\nРаздел находится в разработке.",
        reply_markup=calendar_module_menu(),
    )
    log_audit(callback.from_user.id, "calendar_stub", "calendar", "create")


@router.callback_query(F.data.startswith("cal:event:edit:"))
async def calendar_event_edit_callback(callback: CallbackQuery):
    # TODO: future implementation — event edit flow
    event_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"✏️ Редактирование события #{event_id}\n\n"
        "Раздел находится в разработке.",
        reply_markup=calendar_module_menu(),
    )
    log_audit(callback.from_user.id, "calendar_stub", "calendar", f"edit:{event_id}")


@router.callback_query(F.data.startswith("cal:event:delete:"))
async def calendar_event_delete_callback(callback: CallbackQuery):
    # TODO: future implementation — event delete confirmation
    event_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"🗑 Удаление события #{event_id}\n\n"
        "Раздел находится в разработке.",
        reply_markup=calendar_module_menu(),
    )
    log_audit(callback.from_user.id, "calendar_stub", "calendar", f"delete:{event_id}")


@router.callback_query(F.data.startswith("cal:event:complete:"))
async def calendar_event_complete_callback(callback: CallbackQuery):
    # TODO: future implementation — event completion workflow
    event_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"✅ Завершение события #{event_id}\n\n"
        "Раздел находится в разработке.",
        reply_markup=calendar_module_menu(),
    )
    log_audit(callback.from_user.id, "calendar_stub", "calendar", f"complete:{event_id}")


@router.callback_query(F.data.startswith("cal:event:reschedule:"))
async def calendar_event_reschedule_callback(callback: CallbackQuery):
    # TODO: future implementation — event reschedule flow
    event_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"📅 Перенос события #{event_id}\n\n"
        "Раздел находится в разработке.",
        reply_markup=calendar_module_menu(),
    )
    log_audit(callback.from_user.id, "calendar_stub", "calendar", f"reschedule:{event_id}")


# ==========================================================
# AI ASSISTANT
# ==========================================================

@router.message(F.text == "🤖 AI помощник")
async def open_ai_assistant(message: Message):
    _init_ai_user(message)
    ai_settings_flow.pop(message.from_user.id, None)
    ai_assistant_active[message.from_user.id] = True

    await message.answer(
        "Раздел AI помощника",
        reply_markup=ai_assistant_menu(),
    )
    log_audit(message.from_user.id, "open", "ai_assistant")


@router.message(F.text == "⬅️ К AI помощнику")
async def back_to_ai_assistant(message: Message):
    ai_settings_flow.pop(message.from_user.id, None)
    ai_assistant_active[message.from_user.id] = True
    await message.answer(
        "Раздел AI помощника",
        reply_markup=ai_assistant_menu(),
    )


@router.message(F.text == "👤 Мой профиль")
async def show_ai_profile(message: Message):
    _init_ai_user(message)
    await message.answer(format_profile_text(message.from_user.id))


@router.message(F.text == "🧠 Моя память")
async def show_ai_memory(message: Message):
    _init_ai_user(message)
    await message.answer(format_memory_text(message.from_user.id))


@router.message(F.text == "📁 Мои проекты")
async def show_ai_projects(message: Message):
    _init_ai_user(message)
    await message.answer(format_projects_text(message.from_user.id))


@router.message(F.text == "✅ Мои задачи")
async def show_ai_tasks(message: Message):
    _init_ai_user(message)
    await message.answer(format_tasks_text(message.from_user.id))


@router.message(F.text == "💬 История диалогов")
async def show_ai_history(message: Message):
    _init_ai_user(message)
    text = format_dialog_history_text(message.from_user.id, limit=10)
    if len(text) > 4000:
        text = text[:4000] + "\n\n… (показаны последние сообщения)"
    await message.answer(text)


@router.message((F.text == "⚙ Настройки AI") | (F.text == "⚙️ Настройки AI"))
async def open_ai_settings(message: Message):
    _init_ai_user(message)
    await message.answer(
        format_ai_settings_text(message.from_user.id),
        reply_markup=ai_settings_menu(),
    )


@router.message(F.text == "⬅️ К настройкам AI")
async def back_to_ai_settings(message: Message):
    ai_settings_flow.pop(message.from_user.id, None)
    await message.answer(
        format_ai_settings_text(message.from_user.id),
        reply_markup=ai_settings_menu(),
    )


@router.message(F.text == "🎭 Тон общения")
async def ai_tone_settings(message: Message):
    await message.answer(
        "Выберите тон общения AI:",
        reply_markup=ai_tone_menu(),
    )


@router.message(F.text.in_(TONE_BY_LABEL.keys()))
async def ai_set_tone(message: Message):
    tone = TONE_BY_LABEL[message.text]
    save_ai_settings(message.from_user.id, tone=tone)
    label = TONE_LABELS.get(tone, tone)
    await message.answer(
        f"Тон общения: {label}",
        reply_markup=ai_settings_menu(),
    )


@router.message(F.text == "🌐 Язык ответов")
async def ai_language_settings(message: Message):
    ai_settings_flow[message.from_user.id] = "language"
    await message.answer(
        "Отправьте код языка: ru, uk или en"
    )


@router.message(F.text == "📏 Глубина контекста")
async def ai_context_settings(message: Message):
    await message.answer(
        "Сколько последних сообщений учитывать в диалоге:",
        reply_markup=ai_context_depth_menu(),
    )


@router.message(F.text.in_(CONTEXT_DEPTH_BY_LABEL.keys()))
async def ai_set_context_depth(message: Message):
    depth = CONTEXT_DEPTH_BY_LABEL[message.text]
    save_ai_settings(message.from_user.id, context_depth=depth)
    await message.answer(
        f"Глубина контекста: {depth} сообщений",
        reply_markup=ai_settings_menu(),
    )


@router.message(F.text == "🗑 Очистить историю")
async def ai_clear_history(message: Message):
    clear_dialog_history(message.from_user.id)
    dialog_history.pop(message.from_user.id, None)
    log_audit(message.from_user.id, "clear_history", "ai_assistant")
    await message.answer(
        "История диалогов очищена.",
        reply_markup=ai_settings_menu(),
    )


@router.message(lambda m: ai_settings_flow.get(m.from_user.id) == "language" and m.text not in AI_MENU_BUTTONS)
async def save_ai_language(message: Message):
    language = message.text.strip().lower()
    if language not in {"ru", "uk", "en"}:
        await message.answer("Допустимые значения: ru, uk, en")
        return

    save_ai_settings(message.from_user.id, language=language)
    ai_settings_flow.pop(message.from_user.id, None)
    await message.answer(
        f"Язык ответов: {language}",
        reply_markup=ai_settings_menu(),
    )


@router.message(F.text == "◀ Назад")
async def ai_back_to_main(message: Message):
    _clear_ai_state(message.from_user.id)
    active_module.pop(message.from_user.id, None)
    await message.answer(
        "Главное меню",
        reply_markup=owner_main_menu()
    )


@router.message(
    lambda m: (
        ai_assistant_active.get(m.from_user.id)
        and m.text not in AI_MENU_BUTTONS
        and m.text not in MODULE_STUB_BUTTONS
        and m.text not in CALENDAR_MENU_BUTTONS
        and m.text not in USERS_MENU_BUTTONS
        and m.text not in REPORTS_MENU_BUTTONS
        and m.text not in DRONE_MENU_BUTTONS
        and m.text not in NOTIFICATIONS_MENU_BUTTONS
        and not ai_settings_flow.get(m.from_user.id)
    )
)
async def ai_chat_message(message: Message):
    user_id = message.from_user.id
    _init_ai_user(message)

    profile = get_user_profile(user_id)
    extracted = await extract_memory_from_message(message.text, profile)
    if extracted:
        save_profile_fields(user_id, extracted)

    settings = get_ai_settings(user_id)
    memory_context = format_memory_context(user_id)
    history = get_dialog_history_for_llm(user_id, settings["context_depth"])

    history.append({"role": "user", "content": message.text})
    add_dialog_message(user_id, "user", message.text)

    answer = await ask_openrouter(
        history,
        user_memory=memory_context,
        ai_settings=settings,
    )

    add_dialog_message(user_id, "assistant", answer)
    await message.answer(answer)
    log_audit(user_id, "chat", "ai_assistant")


@router.message(F.text == "⬅️ Назад")
async def back_to_main(message: Message):
    _clear_ai_state(message.from_user.id)
    active_module.pop(message.from_user.id, None)
    await message.answer(
        "Главное меню",
        reply_markup=owner_main_menu()
    )

@router.message(F.text)
async def handle_text(message: Message) -> None:
    user_id = message.from_user.id

    text_lower = message.text.lower()

    if text_lower.startswith("в работу "):
        number = int(text_lower.replace("в работу ", ""))

        update_request_status(
            number,
            "IN_PROGRESS",
            message.from_user.id
        )

        await message.answer(
            f"✅ Заявка #{number} взята в работу"
        )
        return

    if text_lower.startswith("завершить "):
        number = int(text_lower.replace("завершить ", ""))

        update_request_status(
            number,
            "DONE",
            message.from_user.id
        )

        await message.answer(
            f"✅ Заявка #{number} завершена"
        )
        return

    if text_lower.startswith("отменить "):
        number = int(text_lower.replace("отменить ", ""))

        update_request_status(
            number,
            "CANCELLED",
            message.from_user.id
        )

        await message.answer(
            f"❌ Заявка #{number} отменена"
        )
        return

    print(f"Получено сообщение: [{message.text}]")

    # ===== Открытие заявки по номеру =====
    if message.text.isdigit():

        request = get_request_by_number(int(message.text))

        if not request:
            await message.answer("Заявка не найдена.")
            return

        text = (
            f"📋 Заявка #{request[1]}\n\n"
            f"👤 Клиент: {request[3]}\n"
            f"🆔 ID клиента: {request[2]}\n"
            f"📦 Товар: {request[4]}\n\n"
            f"📝 Текст заявки:\n{request[5]}\n\n"
            f"📊 Статус: {request[6]}\n"
            f"👨‍💼 Менеджер ID: {request[7]}\n"
            f"🕒 Создана: {request[8]}"
        )

        await message.answer(text)
        return

    if message.from_user.id == MANAGER_ID:
        ...

        if message.text.lower() == "crm":
            await message.answer(
                 "CRM менеджера",
                 reply_markup=crm_menu()
            )
            return

        if "активные" in message.text.lower():

            requests = get_all_active_requests()

            if not requests:
                await message.answer("Активных заявок нет.")
                return

            text = "📁 Активные заявки\n\n"

            for req in requests:
                manager_name = MANAGERS.get(req[3], "Не назначен")
                status_name = STATUS_NAMES.get(req[4], req[4])

                text += (
                    f"#{req[0]} | "
                    f"{status_name} | "
                    f"{req[2]} | "
                    f"{manager_name}\n"
                )

            await message.answer(text)
            return
            if "заверш" in message.text.lower():
                requests = get_requests_by_status("DONE")

                if not requests:
                    await message.answer("Завершенных заявок нет.")
                    return

                text = "✅ Завершенные заявки\n\n"

                for req in requests:
                    text += (
                        f"#{req[0]} | "
                        f"{req[3]} | "
                        f"{req[2]} | "
                        f"{req[1]}\n"
                    )

                await message.answer(text)
                return
            if message.text.lower() in ["новые заявки", "новые"]:
                requests = get_requests_by_status("NEW")

            if not requests:
                await message.answer("Новых заявок нет.")
                return

        text = "🆕 Новые заявки\n\n"

        for req in requests:
            text += (
                f"#{req[0]} | "
                f"{req[3]} | "
                f"{req[2]} | "
                f"{req[1]}\n"
            )

        await message.answer(text)
        return

        if message.text.lower() in ["завершенные заявки", "завершенные"]:
            requests = get_requests_by_status("DONE")

        if not requests:
            await message.answer("Завершенных заявок нет.")
            return

        text = "✅ Завершенные заявки\n\n"

        for req in requests:
            text += (
                f"#{req[0]} | "
                f"{req[3]} | "
                f"{req[2]} | "
                f"{req[1]}\n"
            )

        await message.answer(text)
        return

        if message.text.lower() in ["отмененные заявки", "отмененные"]:
            requests = get_requests_by_status("CANCELED")

        if not requests:
            await message.answer("Отмененных заявок нет.")
            return

        text = "❌ Отмененные заявки\n\n"

        for req in requests:
            text += (
                f"#{req[0]} | "
                f"{req[3]} | "
                f"{req[2]} | "
                f"{req[1]}\n"
            )

        await message.answer(text)
        return
    # обработка заявки на покупку
    if waiting_buy_request.get(user_id):
        product = buy_requests[user_id]["product"]

        request_number = create_request(
            client_id=user_id,
            client_name=message.from_user.full_name,
            product=product,
            request_text=message.text,
            manager_id=MANAGER_ID
        )

        await message.answer(
            f"""
✅ Заявка #{request_number} принята.

📦 Товар: {product}

📝 Ваше сообщение:
{message.text}

Менеджер свяжется с вами.
"""
        )

        await message.bot.send_message(
    MANAGER_ID,
    f"""
Новая заявка на покупку

Заявка №{request_number}
Статус: 🆕 NEW

Клиент: {message.from_user.full_name}
Telegram ID: {user_id}

Товар: {product}

Сообщение клиента:
{message.text}
""",
    reply_markup=manager_request_menu(request_number)
)

        waiting_buy_request.pop(user_id, None)
        return

@router.message(F.text.startswith("/work "))
async def take_request(message: Message):

    if message.from_user.id != MANAGER_ID:
        return

    try:
        request_number = int(message.text.split()[1])
    except:
        await message.answer("Использование: /work 1001")
        return

    update_request_status(request_number, "IN_PROGRESS")

    client_id = get_request_client(request_number)

    if client_id:
        await message.bot.send_message(
            client_id,
            f"""
🟡 Заявка №{request_number}

Статус изменён:
В работе.

Менеджер приступил к обработке заявки.
"""
        )

    await message.answer(
        f"Заявка {request_number} переведена в статус IN_PROGRESS."
    )
@router.message(F.text.startswith("/done "))
async def complete_request(message: Message):

    if message.from_user.id != MANAGER_ID:
        return

    try:
        request_number = int(message.text.split()[1])
    except:
        await message.answer("Использование: /done 1001")
        return

    update_request_status(request_number, "COMPLETED")

    client_id = get_request_client(request_number)

    if client_id:
        await message.bot.send_message(
            client_id,
            f"""
🟢 Заявка №{request_number}

Статус изменён:
Выполнена.

Спасибо за обращение.
"""
        )

    await message.answer(
        f"Заявка {request_number} завершена."
    )
@router.message(F.text.startswith("/cancel "))
async def cancel_request(message: Message):

    if message.from_user.id != MANAGER_ID:
        return

    try:
        request_number = int(message.text.split()[1])
    except:
        await message.answer("Использование: /cancel 1001")
        return

    update_request_status(request_number, "CANCELED")

    client_id = get_request_client(request_number)

    if client_id:
        await message.bot.send_message(
            client_id,
            f"""
🔴 Заявка №{request_number}

Статус изменён:
Отменена.

Для уточнения деталей свяжитесь с менеджером.
"""
        )

    await message.answer(
        f"Заявка {request_number} отменена."
    )
@router.callback_query(F.data.startswith("work_"))
async def work_request(callback: CallbackQuery):

    request_number = int(callback.data.split("_")[1])

    request = get_request_by_number(request_number)

    if request[7]:
        await callback.answer(
        "Заявка уже закреплена за менеджером.",
        show_alert=True
        )
        return

    assign_manager(request_number, callback.from_user.id)

    update_request_status(request_number, "IN_PROGRESS")

    client_id = get_request_client(request_number)

    if client_id:
        await callback.bot.send_message(
            client_id,
            f"""
🟡 Заявка №{request_number}

Статус изменён:
В работе.

Менеджер приступил к обработке заявки.
"""
        )

    await callback.answer("Заявка взята в работу.")


@router.callback_query(F.data.startswith("done_"))
async def done_request(callback: CallbackQuery):

    request_number = int(callback.data.split("_")[1])

    update_request_status(request_number, "DONE")

    client_id = get_request_client(request_number)

    if client_id:
        await callback.bot.send_message(
            client_id,
            f"""
🟢 Заявка №{request_number}

Статус изменён:
Завершена.

Спасибо за обращение.
"""
        )

    await callback.answer("Заявка завершена.")


@router.callback_query(F.data.startswith("cancel_"))
async def cancel_request(callback: CallbackQuery):

    request_number = int(callback.data.split("_")[1])

    update_request_status(request_number, "CANCELED")

    client_id = get_request_client(request_number)

    if client_id:
        await callback.bot.send_message(
            client_id,
            f"""
🔴 Заявка №{request_number}

Статус изменён:
Отменена.
"""
        )

    await callback.answer("Заявка отменена.")

@router.message(
    (F.text == "📋 CRM") |
    (F.text.lower() == "crm")
)
async def open_crm(message: Message):

    if message.from_user.id != MANAGER_ID:
        return

    await message.answer(
        "CRM менеджера",
        reply_markup=crm_menu()
    )
@router.message(
    (F.text == "📂 Активные заявки") |
    (F.text.lower() == "активные")
)
async def active_requests(message: Message):

    if message.from_user.id != MANAGER_ID:
        return

    requests = get_all_active_requests()

    if not requests:
        await message.answer("Активных заявок нет.")
        return

    text = "📂 Активные заявки\n\n"

    for req in requests:
        text += (
            f"№{req[0]} | "
            f"{req[3]} | "
            f"{req[2]} | "
            f"{req[1]}\n"
        )

    await message.answer(text)
@router.message(
    (F.text == "👤 Мои заявки") |
    (F.text.lower() == "мои")
)
async def my_requests(message: Message):

    if message.from_user.id != MANAGER_ID:
        return

    requests = get_requests_by_manager(message.from_user.id)

    if not requests:
        await message.answer(
            "У вас пока нет закрепленных заявок."
        )
        return

    text = "👤 Мои заявки:\n\n"

    for req in requests:
        text += (
            f"📄 Заявка №{req[1]}\n"
            f"📦 Товар: {req[4]}\n"
            f"📌 Статус: {req[6]}\n"
            f"👨‍💼 Менеджер: {req[7]}\n\n"
        )

    await message.answer(text)    
@router.message(
    (F.text == "🆕 Новые заявки") |
    (F.text.lower() == "новые")
)
async def new_requests(message: Message):

    if message.from_user.id != MANAGER_ID:
        return

    requests = get_requests_by_status("NEW")

    if not requests:
        await message.answer("Новых заявок нет.")
        return

    text = "🆕 Новые заявки\n\n"

    for req in requests:
        text += (
            f"№{req[0]} | "
            f"{req[3]} | "
            f"{req[2]}\n"
        )

    await message.answer(text)

@router.message(
    (F.text == "✅ Завершенные") |
    (F.text.lower() == "завершенные")
)
async def completed_requests(message: Message):

    if message.from_user.id != MANAGER_ID:
        return

    requests = get_requests_by_status("DONE")

    if not requests:
        await message.answer("Завершенных заявок нет.")
        return

    text = "✅ Завершенные заявки\n\n"

    for req in requests:
        text += (
            f"№{req[0]} | "
            f"{req[3]} | "
            f"{req[2]}\n"
        )

    await message.answer(text)
@router.message(
    (F.text == "❌ Отмененные") |
    (F.text.lower() == "отмененные")
)
async def cancelled_requests(message: Message):

    if message.from_user.id != MANAGER_ID:
        return

    requests = get_requests_by_status("CANCELLED")

    if not requests:
        await message.answer("Отмененных заявок нет.")
        return

    text = "❌ Отмененные заявки\n\n"

    for req in requests:
        text += (
            f"№{req[0]} | "
            f"{req[3]} | "
            f"{req[2]}\n"
        )

    await message.answer(text)