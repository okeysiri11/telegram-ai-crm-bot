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
from services.request_auth import RequestAuthService
from services.permissions import PermissionService
from services.statuses import normalize_status
from services.agro_deal_lifecycle import AgroDealLifecycle
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
    TASK_MODULES,
    TASK_STATUSES,
    TASK_PRIORITIES,
    create_system_task,
    register_module_task,
    get_system_tasks,
    format_system_tasks_text,
    format_task_filters_text,
    get_tasks_for_report,
    FILE_MODULES,
    create_system_file,
    register_module_file,
    get_system_files,
    format_system_files_text,
    format_file_modules_text,
    format_file_search_text,
    format_file_tags_text,
    get_files_for_report,
    AGRO_COUNTERPARTY_TYPES,
    AGRO_CONTRACT_TYPES,
    AGRO_CONTRACT_STATUSES,
    AGRO_DELIVERY_STATUSES,
    AGRO_DOCUMENT_TYPES,
    AGRO_CALENDAR_EVENT_TYPES,
    AGRO_CRM_SECTIONS,
    AGRO_COUNTERPARTY_BUTTON_TO_TYPE,
    AGRO_AI_CONTEXT_AREAS,
    can_access_agro_section,
    format_agro_counterparties_text,
    format_agro_contracts_text,
    format_agro_logistics_text,
    format_agro_documents_text,
    format_agro_finance_text,
    format_agro_calendar_text,
    format_agro_reports_text,
    format_agro_section_stub,
    format_agro_ai_assistant_stub,
    format_agro_ai_context_stub,
    get_agro_ai_context,
    format_agro_deal_text,
    get_agro_deal_by_request,
    SEARCH_DOMAINS,
    SEARCH_SCOPES,
    global_search,
    format_search_hub_text,
    format_global_search_text,
    get_search_scope_for_button,
    WORKFLOW_MODULES,
    WORKFLOW_STATUSES,
    WORKFLOW_ACTION_TYPES,
    create_workflow_process,
    register_module_workflow,
    get_workflow_processes,
    format_workflow_processes_text,
    format_workflow_templates_text,
    format_workflow_stats_text,
    pause_workflow_process,
    complete_workflow_process,
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
    tasks_module_menu,
    tasks_module_actions_inline,
    files_module_menu,
    files_module_actions_inline,
    agro_counterparties_menu,
    agro_module_actions_inline,
    agro_deal_actions_inline,
    search_module_menu,
    search_module_actions_inline,
    workflow_module_menu,
    workflow_module_actions_inline,
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
active_agro_sub = {}

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

TASKS_MENU_BUTTONS = {
    "📥 Мои задачи",
    "🆕 Новая задача",
    "👥 Назначенные",
    "📅 Просроченные",
    "🏁 Завершенные",
    "⚙ Фильтры",
    "⬅ Назад",
}

TASKS_STUB_MESSAGES = {
    "📥 Мои задачи": "Мои задачи",
    "🆕 Новая задача": "Новая задача",
    "👥 Назначенные": "Назначенные задачи",
    "📅 Просроченные": "Просроченные задачи",
    "🏁 Завершенные": "Завершенные задачи",
    "⚙ Фильтры": "Фильтры задач",
}

FILES_MENU_BUTTONS = {
    "📥 Входящие",
    "📤 Исходящие",
    "⭐ Избранное",
    "🗂 По модулям",
    "📎 Вложения к задачам",
    "🔍 Поиск",
    "🏷 Теги",
    "🕒 Последние файлы",
    "⬅ Назад",
}

FILES_STUB_MESSAGES = {
    "📥 Входящие": "Входящие файлы",
    "📤 Исходящие": "Исходящие файлы",
    "⭐ Избранное": "Избранные файлы",
    "🗂 По модулям": "Файлы по модулям",
    "📎 Вложения к задачам": "Вложения к задачам",
    "🔍 Поиск": "Поиск файлов",
    "🏷 Теги": "Теги файлов",
    "🕒 Последние файлы": "Последние файлы",
}

SEARCH_MENU_BUTTONS = {
    "🔍 Поиск по всему",
    "👥 Пользователи",
    "📅 Календарь",
    "✅ Задачи",
    "📁 Файлы",
    "💰 Crypto OTC",
    "🌾 Agro Trading",
    "⚖️ Юриспруденция",
    "🚁 Drone Engineering",
    "☕ Cafe & Beauty",
    "⬅ Назад",
}

SEARCH_STUB_MESSAGES = {
    "🔍 Поиск по всему": "Поиск по всему",
    "👥 Пользователи": "Поиск пользователей",
    "📅 Календарь": "Поиск в календаре",
    "✅ Задачи": "Поиск задач",
    "📁 Файлы": "Поиск файлов",
    "💰 Crypto OTC": "Поиск в Crypto OTC",
    "🌾 Agro Trading": "Поиск в Agro Trading",
    "⚖️ Юриспруденция": "Поиск в Юриспруденции",
    "🚁 Drone Engineering": "Поиск в Drone Engineering",
    "☕ Cafe & Beauty": "Поиск в Cafe & Beauty",
}

WORKFLOW_MENU_BUTTONS = {
    "📋 Шаблоны процессов",
    "▶️ Активные процессы",
    "⏸ Приостановленные",
    "✅ Завершенные",
    "📊 Статистика",
    "⬅ Назад",
}

WORKFLOW_STUB_MESSAGES = {
    "📋 Шаблоны процессов": "Шаблоны процессов",
    "▶️ Активные процессы": "Активные процессы",
    "⏸ Приостановленные": "Приостановленные процессы",
    "✅ Завершенные": "Завершенные процессы",
    "📊 Статистика": "Статистика процессов",
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

AGRO_CRM_BUTTONS = {
    "👥 Контрагенты",
    "📑 Контракты",
    "🚢 Логистика",
    "📄 Документы",
    "💵 Финансы",
    "📊 Отчеты Agro",
    "🤖 AI Agro",
}

AGRO_COUNTERPARTY_BUTTONS = set(AGRO_COUNTERPARTY_BUTTON_TO_TYPE.keys())

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
    active_module[message.from_user.id] = "agro"
    active_agro_sub.pop(message.from_user.id, None)
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
# AGRO TRADING CRM (extension — stubs)
# ==========================================================

@router.message(
    lambda m: (
        m.text in AGRO_COUNTERPARTY_BUTTONS
        and active_module.get(m.from_user.id) == "agro"
        and active_agro_sub.get(m.from_user.id) == "counterparties"
    )
)
async def agro_counterparty_type_screen(message: Message):
    # TODO: future implementation — counterparty CRUD UI
    user_id = message.from_user.id
    cp_type = AGRO_COUNTERPARTY_BUTTON_TO_TYPE[message.text]
    type_label = AGRO_COUNTERPARTY_TYPES.get(cp_type, cp_type)
    text = format_agro_counterparties_text(user_id, counterparty_type=cp_type)
    await message.answer(
        f"{type_label}\n\n{text}",
        reply_markup=agro_counterparties_menu(),
    )
    await message.answer(
        "Действия:",
        reply_markup=agro_module_actions_inline("counterparties"),
    )
    log_audit(user_id, "open_stub", "agro_trading", f"counterparty:{cp_type}")


@router.message(
    lambda m: (
        m.text in AGRO_CRM_BUTTONS
        and active_module.get(m.from_user.id) == "agro"
    )
)
async def agro_crm_screen(message: Message):
    # TODO: future implementation — agro CRM section screens
    screen = message.text
    user_id = message.from_user.id

    if screen == "👥 Контрагенты":
        active_agro_sub[user_id] = "counterparties"
        types = ", ".join(AGRO_COUNTERPARTY_TYPES.values())
        await message.answer(
            f"👥 Контрагенты\n\n"
            f"Типы: {types}\n\n"
            "Выберите категорию контрагентов.",
            reply_markup=agro_counterparties_menu(),
        )
        await message.answer(
            "Действия:",
            reply_markup=agro_module_actions_inline("counterparties"),
        )
        log_audit(user_id, "open_stub", "agro_trading", "counterparties")
        return

    section_map = {
        "📑 Контракты": ("contracts", format_agro_contracts_text),
        "🚢 Логистика": ("logistics", format_agro_logistics_text),
        "📄 Документы": ("documents", format_agro_documents_text),
        "💵 Финансы": ("finance", format_agro_finance_text),
        "📊 Отчеты Agro": ("reports", format_agro_reports_text),
    }

    if screen in section_map:
        section_key, formatter = section_map[screen]
        if not can_access_agro_section(user_id, section_key):
            await message.answer(
                f"{screen}\n\nНет доступа к разделу.",
                reply_markup=agro_menu(),
            )
            return
        active_agro_sub.pop(user_id, None)
        await message.answer(formatter(user_id), reply_markup=agro_menu())
        await message.answer(
            "Действия:",
            reply_markup=agro_module_actions_inline(section_key),
        )
        log_audit(user_id, "open_stub", "agro_trading", section_key)
        return

    if screen == "🤖 AI Agro":
        active_agro_sub.pop(user_id, None)
        await message.answer(
            format_agro_ai_assistant_stub(user_id),
            reply_markup=agro_menu(),
        )
        await message.answer(
            "Контекст AI Agro:",
            reply_markup=agro_module_actions_inline("ai_assistant"),
        )
        log_audit(user_id, "open_stub", "agro_trading", "ai_assistant")
        return


@router.message(
    lambda m: (
        m.text == "⬅️ Назад"
        and active_module.get(m.from_user.id) == "agro"
        and active_agro_sub.get(m.from_user.id)
    )
)
async def agro_sub_back(message: Message):
    active_agro_sub.pop(message.from_user.id, None)
    await message.answer(
        "Agro Trading",
        reply_markup=agro_menu(),
    )


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


@router.message(F.text == "✅ Задачи")
async def open_tasks_module(message: Message):
    # TODO: future implementation — tasks dashboard and counters
    _init_ai_user(message)
    _clear_ai_state(message.from_user.id)
    active_module[message.from_user.id] = "tasks"
    log_audit(message.from_user.id, "open", "tasks")

    modules = ", ".join(TASK_MODULES.values())
    await message.answer(
        f"✅ Задачи\n\n"
        f"Центральный модуль задач системы.\n"
        f"Модули: {modules}\n"
        f"Статусы: {', '.join(TASK_STATUSES)}\n"
        f"Приоритеты: {', '.join(TASK_PRIORITIES)}\n\n"
        "Интеграция: календарь, уведомления, отчеты.\n"
        "Раздел находится в разработке.",
        reply_markup=tasks_module_menu(),
    )
    await message.answer(
        "Дополнительно:",
        reply_markup=tasks_module_actions_inline(),
    )


@router.message(
    lambda m: (
        m.text in TASKS_MENU_BUTTONS
        and active_module.get(m.from_user.id) == "tasks"
    )
)
async def tasks_screen(message: Message):
    screen = message.text
    user_id = message.from_user.id

    if screen == "⬅ Назад":
        active_module.pop(user_id, None)
        await message.answer("Главное меню", reply_markup=owner_main_menu())
        return

    title = TASKS_STUB_MESSAGES.get(screen, screen)

    if screen == "📥 Мои задачи":
        text = format_system_tasks_text(user_id, scope="my")
        await message.answer(f"{title}\n\n{text}", reply_markup=tasks_module_menu())
        log_audit(user_id, "open_stub", "tasks", "my")
        return

    if screen == "👥 Назначенные":
        text = format_system_tasks_text(user_id, scope="assigned")
        await message.answer(f"{title}\n\n{text}", reply_markup=tasks_module_menu())
        log_audit(user_id, "open_stub", "tasks", "assigned")
        return

    if screen == "📅 Просроченные":
        text = format_system_tasks_text(user_id, scope="all", overdue_only=True)
        await message.answer(f"{title}\n\n{text}", reply_markup=tasks_module_menu())
        log_audit(user_id, "open_stub", "tasks", "overdue")
        return

    if screen == "🏁 Завершенные":
        text = format_system_tasks_text(user_id, scope="all", status="DONE")
        await message.answer(f"{title}\n\n{text}", reply_markup=tasks_module_menu())
        log_audit(user_id, "open_stub", "tasks", "done")
        return

    if screen == "⚙ Фильтры":
        await message.answer(
            format_task_filters_text(user_id),
            reply_markup=tasks_module_menu(),
        )
        log_audit(user_id, "open_stub", "tasks", "filters")
        return

    if screen == "🆕 Новая задача":
        await message.answer(
            f"{title}\n\n"
            "Создание задач через Telegram находится в разработке.\n"
            "Будут доступны: создание, назначение, смена статуса, "
            "завершение и перенос срока.",
            reply_markup=tasks_module_menu(),
        )
        await message.answer(
            "Действия с задачей:",
            reply_markup=tasks_module_actions_inline(),
        )
        log_audit(user_id, "open_stub", "tasks", "new")
        return

    await message.answer(
        f"{title}\n\nРаздел находится в разработке.",
        reply_markup=tasks_module_menu(),
    )
    log_audit(user_id, "open_stub", "tasks", screen)


@router.message(F.text == "📁 Файлы и документы")
async def open_files_module(message: Message):
    # TODO: future implementation — files dashboard and storage stats
    _init_ai_user(message)
    _clear_ai_state(message.from_user.id)
    active_module[message.from_user.id] = "files"
    log_audit(message.from_user.id, "open", "files")

    modules = ", ".join(FILE_MODULES.values())
    await message.answer(
        f"📁 Файлы и документы\n\n"
        f"Центральное файловое хранилище системы.\n"
        f"Модули: {modules}\n\n"
        "Интеграция: Crypto OTC, Agro Trading, Юриспруденция, "
        "Drone Engineering, Cafe & Beauty, Календарь, Задачи.\n"
        "Раздел находится в разработке.",
        reply_markup=files_module_menu(),
    )
    await message.answer(
        "Дополнительно:",
        reply_markup=files_module_actions_inline(),
    )


@router.message(
    lambda m: (
        m.text in FILES_MENU_BUTTONS
        and active_module.get(m.from_user.id) == "files"
    )
)
async def files_screen(message: Message):
    screen = message.text
    user_id = message.from_user.id

    if screen == "⬅ Назад":
        active_module.pop(user_id, None)
        await message.answer("Главное меню", reply_markup=owner_main_menu())
        return

    title = FILES_STUB_MESSAGES.get(screen, screen)

    if screen == "📥 Входящие":
        text = format_system_files_text(user_id, scope="incoming")
        await message.answer(f"{title}\n\n{text}", reply_markup=files_module_menu())
        log_audit(user_id, "open_stub", "files", "incoming")
        return

    if screen == "📤 Исходящие":
        text = format_system_files_text(user_id, scope="outgoing")
        await message.answer(f"{title}\n\n{text}", reply_markup=files_module_menu())
        log_audit(user_id, "open_stub", "files", "outgoing")
        return

    if screen == "⭐ Избранное":
        text = format_system_files_text(user_id, scope="favorite")
        await message.answer(f"{title}\n\n{text}", reply_markup=files_module_menu())
        log_audit(user_id, "open_stub", "files", "favorite")
        return

    if screen == "🗂 По модулям":
        await message.answer(
            format_file_modules_text(user_id),
            reply_markup=files_module_menu(),
        )
        log_audit(user_id, "open_stub", "files", "modules")
        return

    if screen == "📎 Вложения к задачам":
        text = format_system_files_text(user_id, scope="task")
        await message.answer(f"{title}\n\n{text}", reply_markup=files_module_menu())
        log_audit(user_id, "open_stub", "files", "task_attachments")
        return

    if screen == "🔍 Поиск":
        await message.answer(
            format_file_search_text(user_id),
            reply_markup=files_module_menu(),
        )
        await message.answer(
            "Действия с файлом:",
            reply_markup=files_module_actions_inline(),
        )
        log_audit(user_id, "open_stub", "files", "search")
        return

    if screen == "🏷 Теги":
        await message.answer(
            format_file_tags_text(user_id),
            reply_markup=files_module_menu(),
        )
        log_audit(user_id, "open_stub", "files", "tags")
        return

    if screen == "🕒 Последние файлы":
        text = format_system_files_text(user_id, scope="recent")
        await message.answer(f"{title}\n\n{text}", reply_markup=files_module_menu())
        log_audit(user_id, "open_stub", "files", "recent")
        return

    await message.answer(
        f"{title}\n\nРаздел находится в разработке.",
        reply_markup=files_module_menu(),
    )
    log_audit(user_id, "open_stub", "files", screen)


@router.message(F.text == "🔎 Глобальный поиск")
async def open_search_module(message: Message):
    # TODO: future implementation — search dashboard and recent queries
    _init_ai_user(message)
    _clear_ai_state(message.from_user.id)
    active_module[message.from_user.id] = "search"
    log_audit(message.from_user.id, "open", "search")

    domains = ", ".join(SEARCH_DOMAINS.values())
    await message.answer(
        f"{format_search_hub_text(message.from_user.id)}\n\n"
        f"Модули: {', '.join(SEARCH_SCOPES.values())}\n"
        f"Области: {domains}",
        reply_markup=search_module_menu(),
    )
    await message.answer(
        "Дополнительно:",
        reply_markup=search_module_actions_inline("all"),
    )


@router.message(
    lambda m: (
        m.text in SEARCH_MENU_BUTTONS
        and active_module.get(m.from_user.id) == "search"
    )
)
async def search_screen(message: Message):
    screen = message.text
    user_id = message.from_user.id

    if screen == "⬅ Назад":
        active_module.pop(user_id, None)
        await message.answer("Главное меню", reply_markup=owner_main_menu())
        return

    scope = get_search_scope_for_button(screen)
    title = SEARCH_STUB_MESSAGES.get(screen, screen)
    text = format_global_search_text(user_id, scope=scope)

    await message.answer(
        f"{title}\n\n{text}",
        reply_markup=search_module_menu(),
    )
    await message.answer(
        "Действия поиска:",
        reply_markup=search_module_actions_inline(scope),
    )
    log_audit(user_id, "open_stub", "search", scope)


@router.message(F.text == "⚙️ Бизнес-процессы")
async def open_workflow_module(message: Message):
    # TODO: future implementation — workflow dashboard and triggers
    _init_ai_user(message)
    _clear_ai_state(message.from_user.id)
    active_module[message.from_user.id] = "workflow"
    log_audit(message.from_user.id, "open", "workflow")

    modules = ", ".join(WORKFLOW_MODULES.values())
    actions = ", ".join(WORKFLOW_ACTION_TYPES.values())
    await message.answer(
        f"⚙️ Бизнес-процессы\n\n"
        f"Workflow Engine — центральный движок процессов.\n"
        f"Модули: {modules}\n"
        f"Статусы: {', '.join(WORKFLOW_STATUSES)}\n"
        f"Действия: {actions}\n\n"
        "Интеграция: задачи, календарь, уведомления, файлы.\n"
        "Раздел находится в разработке.",
        reply_markup=workflow_module_menu(),
    )
    await message.answer(
        "Дополнительно:",
        reply_markup=workflow_module_actions_inline(),
    )


@router.message(
    lambda m: (
        m.text in WORKFLOW_MENU_BUTTONS
        and active_module.get(m.from_user.id) == "workflow"
    )
)
async def workflow_screen(message: Message):
    screen = message.text
    user_id = message.from_user.id

    if screen == "⬅ Назад":
        active_module.pop(user_id, None)
        await message.answer("Главное меню", reply_markup=owner_main_menu())
        return

    title = WORKFLOW_STUB_MESSAGES.get(screen, screen)

    if screen == "📋 Шаблоны процессов":
        text = format_workflow_templates_text(user_id)
        await message.answer(f"{title}\n\n{text}", reply_markup=workflow_module_menu())
        log_audit(user_id, "open_stub", "workflow", "templates")
        return

    if screen == "▶️ Активные процессы":
        text = format_workflow_processes_text(user_id, status="ACTIVE")
        await message.answer(f"{title}\n\n{text}", reply_markup=workflow_module_menu())
        log_audit(user_id, "open_stub", "workflow", "active")
        return

    if screen == "⏸ Приостановленные":
        text = format_workflow_processes_text(user_id, status="PAUSED")
        await message.answer(f"{title}\n\n{text}", reply_markup=workflow_module_menu())
        log_audit(user_id, "open_stub", "workflow", "paused")
        return

    if screen == "✅ Завершенные":
        text = format_workflow_processes_text(user_id, status="COMPLETED")
        await message.answer(f"{title}\n\n{text}", reply_markup=workflow_module_menu())
        log_audit(user_id, "open_stub", "workflow", "completed")
        return

    if screen == "📊 Статистика":
        await message.answer(
            format_workflow_stats_text(user_id),
            reply_markup=workflow_module_menu(),
        )
        log_audit(user_id, "open_stub", "workflow", "stats")
        return

    await message.answer(
        f"{title}\n\nРаздел находится в разработке.",
        reply_markup=workflow_module_menu(),
    )
    log_audit(user_id, "open_stub", "workflow", screen)


@router.message(F.text == "📅 Календарь")
async def open_calendar_module(message: Message):
    # TODO: future implementation — calendar dashboard and widgets
    if active_module.get(message.from_user.id) == "agro":
        user_id = message.from_user.id
        await message.answer(
            format_agro_calendar_text(user_id),
            reply_markup=agro_menu(),
        )
        await message.answer(
            "Действия:",
            reply_markup=agro_module_actions_inline("calendar"),
        )
        log_audit(user_id, "open_stub", "agro_trading", "calendar")
        return

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


@router.callback_query(F.data.startswith("tsk:assign:"))
async def tasks_assign_callback(callback: CallbackQuery):
    # TODO: future implementation — assign task to user
    task_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"👤 Назначить задачу #{task_id}\n\n"
        "Назначение задач находится в разработке.",
        reply_markup=tasks_module_menu(),
    )
    log_audit(callback.from_user.id, "tasks_stub", "tasks", f"assign:{task_id}")


@router.callback_query(F.data.startswith("tsk:complete:"))
async def tasks_complete_callback(callback: CallbackQuery):
    # TODO: future implementation — complete task workflow
    task_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"🏁 Завершить задачу #{task_id}\n\n"
        "Завершение задач находится в разработке.",
        reply_markup=tasks_module_menu(),
    )
    log_audit(callback.from_user.id, "tasks_stub", "tasks", f"complete:{task_id}")


@router.callback_query(F.data.startswith("tsk:reschedule:"))
async def tasks_reschedule_callback(callback: CallbackQuery):
    # TODO: future implementation — reschedule task due date
    task_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"📅 Перенести срок задачи #{task_id}\n\n"
        "Перенос срока находится в разработке.",
        reply_markup=tasks_module_menu(),
    )
    log_audit(callback.from_user.id, "tasks_stub", "tasks", f"reschedule:{task_id}")


@router.callback_query(F.data.startswith("tsk:status:"))
async def tasks_status_callback(callback: CallbackQuery):
    # TODO: future implementation — change task status
    task_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"⚙ Статус задачи #{task_id}\n\n"
        f"Доступные статусы: {', '.join(TASK_STATUSES)}\n\n"
        "Изменение статуса находится в разработке.",
        reply_markup=tasks_module_menu(),
    )
    log_audit(callback.from_user.id, "tasks_stub", "tasks", f"status:{task_id}")


@router.callback_query(F.data.startswith("fil:open:"))
async def files_open_callback(callback: CallbackQuery):
    # TODO: future implementation — open file preview
    file_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"📂 Открыть файл #{file_id}\n\n"
        "Просмотр файлов находится в разработке.",
        reply_markup=files_module_menu(),
    )
    log_audit(callback.from_user.id, "files_stub", "files", f"open:{file_id}")


@router.callback_query(F.data.startswith("fil:download:"))
async def files_download_callback(callback: CallbackQuery):
    # TODO: future implementation — download file from storage
    file_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"⬇ Скачать файл #{file_id}\n\n"
        "Скачивание файлов находится в разработке.",
        reply_markup=files_module_menu(),
    )
    log_audit(callback.from_user.id, "files_stub", "files", f"download:{file_id}")


@router.callback_query(F.data.startswith("fil:tag:"))
async def files_tag_callback(callback: CallbackQuery):
    # TODO: future implementation — add or edit file tags
    file_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"🏷 Теги файла #{file_id}\n\n"
        "Управление тегами находится в разработке.",
        reply_markup=files_module_menu(),
    )
    log_audit(callback.from_user.id, "files_stub", "files", f"tag:{file_id}")


@router.callback_query(F.data.startswith("fil:attach:"))
async def files_attach_callback(callback: CallbackQuery):
    # TODO: future implementation — attach file to task
    file_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"📎 Прикрепить файл #{file_id} к задаче\n\n"
        "Привязка к задачам находится в разработке.",
        reply_markup=files_module_menu(),
    )
    log_audit(callback.from_user.id, "files_stub", "files", f"attach:{file_id}")


@router.callback_query(F.data.startswith("agr:create:"))
async def agro_create_callback(callback: CallbackQuery):
    # TODO: future implementation — create agro CRM entity
    section = callback.data.split(":", 2)[2]
    await callback.answer()
    await callback.message.answer(
        f"➕ Создать · {section}\n\n"
        "Создание записей находится в разработке.",
        reply_markup=agro_menu(),
    )
    log_audit(callback.from_user.id, "agro_stub", "agro_trading", f"create:{section}")


@router.callback_query(F.data.startswith("agr:search:"))
async def agro_search_callback(callback: CallbackQuery):
    # TODO: future implementation — search within agro section
    section = callback.data.split(":", 2)[2]
    await callback.answer()
    await callback.message.answer(
        f"🔍 Поиск · {section}\n\n"
        "Поиск в разделе находится в разработке.",
        reply_markup=agro_menu(),
    )
    log_audit(callback.from_user.id, "agro_stub", "agro_trading", f"search:{section}")


@router.callback_query(F.data.startswith("agr:by_request:"))
async def agro_by_request_callback(callback: CallbackQuery):
    # TODO: future implementation — filter by CRM request number
    section = callback.data.split(":", 2)[2]
    await callback.answer()
    await callback.message.answer(
        f"📋 По заявке · {section}\n\n"
        "Привязка к заявкам CRM находится в разработке.",
        reply_markup=agro_menu(),
    )
    log_audit(callback.from_user.id, "agro_stub", "agro_trading", f"by_request:{section}")


@router.callback_query(F.data.startswith("agr:report:"))
async def agro_report_callback(callback: CallbackQuery):
    # TODO: future implementation — section report export
    section = callback.data.split(":", 2)[2]
    user_id = callback.from_user.id
    await callback.answer()
    if section == "reports":
        text = format_agro_reports_text(user_id)
    else:
        text = f"📊 Отчет · {section}\n\nРаздел находится в разработке."
    await callback.message.answer(text, reply_markup=agro_menu())
    log_audit(user_id, "agro_stub", "agro_trading", f"report:{section}")


@router.callback_query(F.data == "agr:ai:open")
async def agro_ai_open_callback(callback: CallbackQuery):
    # TODO: future implementation — open AI Agro Assistant chat
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.answer(
        format_agro_ai_assistant_stub(user_id),
        reply_markup=agro_menu(),
    )
    log_audit(user_id, "agro_stub", "agro_trading", "ai_open")


@router.callback_query(F.data.startswith("agr:ai:context:"))
async def agro_ai_context_callback(callback: CallbackQuery):
    # TODO: future implementation — preview AI Agro context area
    area = callback.data.split(":", 3)[3]
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.answer(
        format_agro_ai_context_stub(area, user_id),
        reply_markup=agro_menu(),
    )
    log_audit(user_id, "agro_stub", "agro_trading", f"ai_context:{area}")


@router.callback_query(F.data.startswith("agr:deal:bind:contract:"))
async def agro_deal_bind_contract_callback(callback: CallbackQuery):
    request_number = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    request = get_request_by_number(request_number)
    if not RequestAuthService.can_update_status(user_id, request):
        await callback.answer(RequestAuthService.deny_message("bind"), show_alert=True)
        return
    contract_id = AgroDealLifecycle.bind_contract(user_id, request_number)
    await callback.answer()
    await callback.message.answer(
        f"📑 Контракт #{contract_id} привязан к сделке #{request_number}\n\n"
        f"{format_agro_deal_text(request_number)}",
        reply_markup=agro_deal_actions_inline(request_number),
    )


@router.callback_query(F.data.startswith("agr:deal:bind:logistics:"))
async def agro_deal_bind_logistics_callback(callback: CallbackQuery):
    request_number = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    request = get_request_by_number(request_number)
    if not RequestAuthService.can_update_status(user_id, request):
        await callback.answer(RequestAuthService.deny_message("bind"), show_alert=True)
        return
    logistics_id = AgroDealLifecycle.bind_logistics(user_id, request_number)
    await callback.answer()
    await callback.message.answer(
        f"🚢 Логистика #{logistics_id} привязана к сделке #{request_number}\n\n"
        f"{format_agro_deal_text(request_number)}",
        reply_markup=agro_deal_actions_inline(request_number),
    )


@router.callback_query(F.data.startswith("agr:deal:bind:finance:"))
async def agro_deal_bind_finance_callback(callback: CallbackQuery):
    request_number = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    request = get_request_by_number(request_number)
    if not RequestAuthService.can_update_status(user_id, request):
        await callback.answer(RequestAuthService.deny_message("bind"), show_alert=True)
        return
    finance_id = AgroDealLifecycle.bind_finance(user_id, request_number)
    await callback.answer()
    await callback.message.answer(
        f"💵 Финансы #{finance_id} привязаны к сделке #{request_number}\n\n"
        f"{format_agro_deal_text(request_number)}",
        reply_markup=agro_deal_actions_inline(request_number),
    )


@router.callback_query(F.data.startswith("agr:deal:close:"))
async def agro_deal_close_callback(callback: CallbackQuery):
    request_number = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    request = get_request_by_number(request_number)
    if not RequestAuthService.can_update_status(user_id, request):
        await callback.answer(RequestAuthService.deny_message("close"), show_alert=True)
        return
    update_request_status(request_number, "DONE", user_id)
    await callback.answer("Сделка закрыта")
    await callback.message.answer(
        f"🏁 Сделка #{request_number} закрыта.\n\n"
        f"{format_agro_deal_text(request_number)}",
        reply_markup=agro_deal_actions_inline(request_number),
    )


@router.callback_query(F.data.startswith("agr:deal:report:"))
async def agro_deal_report_callback(callback: CallbackQuery):
    request_number = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    request = get_request_by_number(request_number)
    if not RequestAuthService.can_view_request(user_id, request):
        await callback.answer(RequestAuthService.deny_message("report"), show_alert=True)
        return
    file_id = AgroDealLifecycle.generate_report(user_id, request_number)
    await callback.answer()
    await callback.message.answer(
        f"📊 Отчёт по сделке #{request_number} сформирован (файл #{file_id}).\n\n"
        f"{format_agro_deal_text(request_number)}",
        reply_markup=agro_deal_actions_inline(request_number),
    )


@router.callback_query(F.data.startswith("srch:run:"))
async def search_run_callback(callback: CallbackQuery):
    # TODO: future implementation — execute search query
    scope = callback.data.split(":", 2)[2]
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.answer(
        format_global_search_text(user_id, scope=scope),
        reply_markup=search_module_menu(),
    )
    log_audit(user_id, "search_stub", "search", f"run:{scope}")


@router.callback_query(F.data == "srch:filter:open")
async def search_filter_callback(callback: CallbackQuery):
    # TODO: future implementation — search filters UI
    user_id = callback.from_user.id
    await callback.answer()
    domains = ", ".join(SEARCH_DOMAINS.values())
    await callback.message.answer(
        f"⚙ Фильтры поиска\n\n"
        f"Области: {domains}\n\n"
        "Фильтрация находится в разработке.",
        reply_markup=search_module_menu(),
    )
    log_audit(user_id, "search_stub", "search", "filter")


@router.callback_query(F.data == "srch:history:open")
async def search_history_callback(callback: CallbackQuery):
    # TODO: future implementation — search history
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.answer(
        "🕒 История поиска\n\n"
        "История запросов находится в разработке.",
        reply_markup=search_module_menu(),
    )
    log_audit(user_id, "search_stub", "search", "history")


@router.callback_query(F.data.startswith("wfl:start:"))
async def workflow_start_callback(callback: CallbackQuery):
    # TODO: future implementation — start workflow process
    process_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"▶️ Запустить процесс #{process_id}\n\n"
        "Запуск процессов находится в разработке.",
        reply_markup=workflow_module_menu(),
    )
    log_audit(callback.from_user.id, "workflow_stub", "workflow", f"start:{process_id}")


@router.callback_query(F.data.startswith("wfl:pause:"))
async def workflow_pause_callback(callback: CallbackQuery):
    # TODO: future implementation — pause workflow process
    process_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"⏸ Приостановить процесс #{process_id}\n\n"
        "Приостановка процессов находится в разработке.",
        reply_markup=workflow_module_menu(),
    )
    log_audit(callback.from_user.id, "workflow_stub", "workflow", f"pause:{process_id}")


@router.callback_query(F.data.startswith("wfl:complete:"))
async def workflow_complete_callback(callback: CallbackQuery):
    # TODO: future implementation — complete workflow process
    process_id = callback.data.split(":")[-1]
    await callback.answer()
    await callback.message.answer(
        f"✅ Завершить процесс #{process_id}\n\n"
        "Завершение процессов находится в разработке.",
        reply_markup=workflow_module_menu(),
    )
    log_audit(callback.from_user.id, "workflow_stub", "workflow", f"complete:{process_id}")


@router.callback_query(F.data.startswith("wfl:action:"))
async def workflow_action_callback(callback: CallbackQuery):
    # TODO: future implementation — execute workflow action
    parts = callback.data.split(":")
    action_key = parts[2] if len(parts) > 2 else "menu"
    process_id = parts[3] if len(parts) > 3 else "0"
    actions = ", ".join(WORKFLOW_ACTION_TYPES.values())
    await callback.answer()
    await callback.message.answer(
        f"⚙ Действие · {action_key} · процесс #{process_id}\n\n"
        f"Доступные действия: {actions}\n\n"
        "Выполнение действий находится в разработке.",
        reply_markup=workflow_module_menu(),
    )
    log_audit(callback.from_user.id, "workflow_stub", "workflow", f"action:{action_key}:{process_id}")


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
        and m.text not in TASKS_MENU_BUTTONS
        and m.text not in FILES_MENU_BUTTONS
        and m.text not in SEARCH_MENU_BUTTONS
        and m.text not in WORKFLOW_MENU_BUTTONS
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
    active_agro_sub.pop(message.from_user.id, None)
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
        request = get_request_by_number(number)
        if not RequestAuthService.can_take_request(user_id, request):
            await message.answer(RequestAuthService.deny_message("take"))
            return
        if request and request[7]:
            await message.answer("Заявка уже закреплена за менеджером.")
            return
        assign_manager(number, user_id)
        update_request_status(number, "IN_PROGRESS", user_id)
        await message.answer(f"✅ Заявка #{number} взята в работу")
        return

    if text_lower.startswith("завершить "):
        number = int(text_lower.replace("завершить ", ""))
        request = get_request_by_number(number)
        if not RequestAuthService.can_update_status(user_id, request):
            await message.answer(RequestAuthService.deny_message("update"))
            return
        update_request_status(number, "DONE", user_id)
        await message.answer(f"✅ Заявка #{number} завершена")
        return

    if text_lower.startswith("отменить "):
        number = int(text_lower.replace("отменить ", ""))
        request = get_request_by_number(number)
        if not RequestAuthService.can_cancel_request(user_id, request):
            await message.answer(RequestAuthService.deny_message("cancel"))
            return
        update_request_status(number, "CANCELLED", user_id)
        await message.answer(f"❌ Заявка #{number} отменена")
        return

    print(f"Получено сообщение: [{message.text}]")

    # ===== Открытие заявки по номеру =====
    if message.text.isdigit():

        request = get_request_by_number(int(message.text))

        if not request:
            await message.answer("Заявка не найдена.")
            return

        if not RequestAuthService.can_view_request(user_id, request):
            await message.answer(RequestAuthService.deny_message("view"))
            return

        text = (
            f"📋 Заявка #{request[1]}\n\n"
            f"👤 Клиент: {request[3]}\n"
            f"🆔 ID клиента: {request[2]}\n"
            f"📦 Товар: {request[4]}\n\n"
            f"📝 Текст заявки:\n{request[5]}\n\n"
            f"📊 Статус: {normalize_status(request[6])}\n"
            f"👨‍💼 Менеджер ID: {request[7]}\n"
            f"🕒 Создана: {request[8]}"
        )

        await message.answer(text)
        deal_text = format_agro_deal_text(int(message.text))
        await message.answer(deal_text)
        if PermissionService.is_crm_operator(user_id):
            await message.answer(
                "Действия со сделкой:",
                reply_markup=agro_deal_actions_inline(int(message.text)),
            )
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

    if not RequestAuthService.can_take_request(callback.from_user.id, request):
        await callback.answer(
            RequestAuthService.deny_message("take"),
            show_alert=True,
        )
        return

    if request[7]:
        await callback.answer(
        "Заявка уже закреплена за менеджером.",
        show_alert=True
        )
        return

    assign_manager(request_number, callback.from_user.id)

    update_request_status(request_number, "IN_PROGRESS", callback.from_user.id)

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
    request = get_request_by_number(request_number)

    if not RequestAuthService.can_update_status(callback.from_user.id, request):
        await callback.answer(
            RequestAuthService.deny_message("update"),
            show_alert=True,
        )
        return

    update_request_status(request_number, "DONE", callback.from_user.id)

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
    request = get_request_by_number(request_number)

    if not RequestAuthService.can_cancel_request(callback.from_user.id, request):
        await callback.answer(
            RequestAuthService.deny_message("cancel"),
            show_alert=True,
        )
        return

    update_request_status(request_number, "CANCELLED", callback.from_user.id)

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