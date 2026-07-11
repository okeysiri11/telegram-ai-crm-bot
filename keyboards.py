from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def owner_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💰 Crypto OTC"),
                KeyboardButton(text="🚁 Drone Engineering")
            ],
            [
                KeyboardButton(text="⚖ Юриспруденция"),
                KeyboardButton(text="☕ Cafe & Beauty")
            ],
            [
                KeyboardButton(text="🌾 Agro Trading"),
                KeyboardButton(text="👥 Пользователи")
            ],
            [
                KeyboardButton(text="📅 Календарь"),
                KeyboardButton(text="📊 Отчеты")
            ],
            [
                KeyboardButton(text="🤖 AI помощник"),
                KeyboardButton(text="🔔 Уведомления")
            ],
            [
                KeyboardButton(text="✅ Задачи"),
                KeyboardButton(text="📁 Файлы и документы")
            ],
            [
                KeyboardButton(text="🔎 Глобальный поиск")
            ],
            [
                KeyboardButton(text="⚙️ Бизнес-процессы")
            ],
            [
                KeyboardButton(text="⚙ Администрирование")
            ]
        ],
        resize_keyboard=True
    )

    return keyboard


def notifications_module_menu():
    # TODO: future implementation — central notifications hub
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📥 Новые"),
                KeyboardButton(text="📌 Важные")
            ],
            [
                KeyboardButton(text="📅 Напоминания"),
                KeyboardButton(text="⚙ Настройки уведомлений")
            ],
            [
                KeyboardButton(text="🗑 Архив")
            ],
            [
                KeyboardButton(text="⬅ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def notifications_module_actions_inline() -> InlineKeyboardMarkup:
    # TODO: future implementation — notification quick actions
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Прочитать все",
                    callback_data="ntf:action:read_all"
                ),
                InlineKeyboardButton(
                    text="🗑 В архив",
                    callback_data="ntf:action:archive_all"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⚙ Настройки",
                    callback_data="ntf:settings:open"
                ),
            ],
        ]
    )


def tasks_module_menu():
    # TODO: future implementation — central tasks hub
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📥 Мои задачи"),
                KeyboardButton(text="🆕 Новая задача")
            ],
            [
                KeyboardButton(text="👥 Назначенные"),
                KeyboardButton(text="📅 Просроченные")
            ],
            [
                KeyboardButton(text="🏁 Завершенные"),
                KeyboardButton(text="⚙ Фильтры")
            ],
            [
                KeyboardButton(text="⬅ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def tasks_module_actions_inline(task_id: int = 0) -> InlineKeyboardMarkup:
    # TODO: future implementation — task quick actions
    tid = task_id or 0
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Назначить",
                    callback_data=f"tsk:assign:{tid}"
                ),
                InlineKeyboardButton(
                    text="🏁 Завершить",
                    callback_data=f"tsk:complete:{tid}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📅 Перенести срок",
                    callback_data=f"tsk:reschedule:{tid}"
                ),
                InlineKeyboardButton(
                    text="⚙ Статус",
                    callback_data=f"tsk:status:{tid}"
                ),
            ],
        ]
    )


def files_module_menu():
    # TODO: future implementation — central files hub
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📥 Входящие"),
                KeyboardButton(text="📤 Исходящие")
            ],
            [
                KeyboardButton(text="⭐ Избранное"),
                KeyboardButton(text="🗂 По модулям")
            ],
            [
                KeyboardButton(text="📎 Вложения к задачам"),
                KeyboardButton(text="🔍 Поиск")
            ],
            [
                KeyboardButton(text="🏷 Теги"),
                KeyboardButton(text="🕒 Последние файлы")
            ],
            [
                KeyboardButton(text="⬅ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def files_module_actions_inline(file_id: int = 0) -> InlineKeyboardMarkup:
    # TODO: future implementation — file quick actions
    fid = file_id or 0
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📂 Открыть",
                    callback_data=f"fil:open:{fid}"
                ),
                InlineKeyboardButton(
                    text="⬇ Скачать",
                    callback_data=f"fil:download:{fid}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏷 Тег",
                    callback_data=f"fil:tag:{fid}"
                ),
                InlineKeyboardButton(
                    text="📎 К задаче",
                    callback_data=f"fil:attach:{fid}"
                ),
            ],
        ]
    )


def workflow_module_menu():
    # TODO: future implementation — workflow engine hub
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Шаблоны процессов")
            ],
            [
                KeyboardButton(text="▶️ Активные процессы"),
                KeyboardButton(text="⏸ Приостановленные")
            ],
            [
                KeyboardButton(text="✅ Завершенные"),
                KeyboardButton(text="📊 Статистика")
            ],
            [
                KeyboardButton(text="⬅ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def workflow_module_actions_inline(process_id: int = 0) -> InlineKeyboardMarkup:
    # TODO: future implementation — workflow quick actions
    pid = process_id or 0
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶️ Запустить",
                    callback_data=f"wfl:start:{pid}"
                ),
                InlineKeyboardButton(
                    text="⏸ Пауза",
                    callback_data=f"wfl:pause:{pid}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Завершить",
                    callback_data=f"wfl:complete:{pid}"
                ),
                InlineKeyboardButton(
                    text="⚙ Действие",
                    callback_data=f"wfl:action:menu:{pid}"
                ),
            ],
        ]
    )


def search_module_menu():
    # TODO: future implementation — global search hub
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔍 Поиск по всему")
            ],
            [
                KeyboardButton(text="👥 Пользователи"),
                KeyboardButton(text="📅 Календарь")
            ],
            [
                KeyboardButton(text="✅ Задачи"),
                KeyboardButton(text="📁 Файлы")
            ],
            [
                KeyboardButton(text="💰 Crypto OTC"),
                KeyboardButton(text="🌾 Agro Trading")
            ],
            [
                KeyboardButton(text="⚖️ Юриспруденция"),
                KeyboardButton(text="🚁 Drone Engineering")
            ],
            [
                KeyboardButton(text="☕ Cafe & Beauty")
            ],
            [
                KeyboardButton(text="⬅ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def search_module_actions_inline(scope: str = "all") -> InlineKeyboardMarkup:
    # TODO: future implementation — search quick actions
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔍 Запустить поиск",
                    callback_data=f"srch:run:{scope}"
                ),
                InlineKeyboardButton(
                    text="⚙ Фильтры",
                    callback_data="srch:filter:open"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🕒 История",
                    callback_data="srch:history:open"
                ),
            ],
        ]
    )


def wife_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="☕ Cafe"),
                KeyboardButton(text="💄 Beauty")
            ],
            [
                KeyboardButton(text="📦 Склад"),
                KeyboardButton(text="📅 Календарь")
            ],
            [
                KeyboardButton(text="👤 Профиль")
            ]
        ],
        resize_keyboard=True
    )

    return keyboard


def drone_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Проекты"),
                KeyboardButton(text="📐 CAD / SolidWorks")
            ],
            [
                KeyboardButton(text="🔌 Электроника"),
                KeyboardButton(text="⚙ ArduPilot")
            ],
            [
                KeyboardButton(text="🎮 Betaflight"),
                KeyboardButton(text="📅 Календарь")
            ],
            [
                KeyboardButton(text="👤 Профиль")
            ]
        ],
        resize_keyboard=True
    )

    return keyboard


def lawyer_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📂 Дела"),
                KeyboardButton(text="📑 Документы")
            ],
            [
                KeyboardButton(text="📚 Законодательство"),
                KeyboardButton(text="⚖ Судебная практика")
            ],
            [
                KeyboardButton(text="📅 Календарь"),
                KeyboardButton(text="👤 Профиль")
            ]
        ],
        resize_keyboard=True
    )

    return keyboard
def crypto_otc_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💵 Курсы"),
                KeyboardButton(text="🏦 Банки")
            ],
            [
                KeyboardButton(text="💳 Платежи"),
                KeyboardButton(text="👤 Клиенты")
            ],
            [
                KeyboardButton(text="📈 Арбитраж"),
                KeyboardButton(text="📑 Договоры")
            ],
            [
                KeyboardButton(text="📊 PnL"),
                KeyboardButton(text="📅 Сделки")
            ],
            [
                KeyboardButton(text="⬅️ Назад")
            ]
        ],
        resize_keyboard=True
    )

    return keyboard 
def agro_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🌾 Товары"),
                KeyboardButton(text="🌍 Страны")
            ],
            [
                KeyboardButton(text="🚢 Логистика"),
                KeyboardButton(text="📈 Цены")
            ],
            [
                KeyboardButton(text="📑 Контракты"),
                KeyboardButton(text="📊 Аналитика")
            ],
            [
                KeyboardButton(text="🗄 База данных"),
                KeyboardButton(text="📅 Календарь")
            ],
            [
                KeyboardButton(text="🧮 Фрахт"),
                KeyboardButton(text="🚛 Автологистика")
            ],
            [
                KeyboardButton(text="🛳 Морская логистика"),
                KeyboardButton(text="📦 Склады")
            ],
            [
                KeyboardButton(text="👥 Контрагенты"),
                KeyboardButton(text="📄 Документы")
            ],
            [
                KeyboardButton(text="💵 Финансы"),
                KeyboardButton(text="📊 Отчеты Agro")
            ],
            [
                KeyboardButton(text="🤖 AI Agro")
            ],
            [
                KeyboardButton(text="⬅️ Назад")
            ]
        ],
        resize_keyboard=True
    )

    return keyboard


def agro_deal_actions_inline(request_number: int) -> InlineKeyboardMarkup:
    rn = request_number
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📑 Контракт",
                    callback_data=f"agr:deal:bind:contract:{rn}",
                ),
                InlineKeyboardButton(
                    text="🚢 Логистика",
                    callback_data=f"agr:deal:bind:logistics:{rn}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💵 Финансы",
                    callback_data=f"agr:deal:bind:finance:{rn}",
                ),
                InlineKeyboardButton(
                    text="📊 Отчёт",
                    callback_data=f"agr:deal:report:{rn}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏁 Закрыть сделку",
                    callback_data=f"agr:deal:close:{rn}",
                ),
            ],
        ]
    )


def agro_counterparties_menu():
    # TODO: future implementation — counterparty management
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Поставщики"),
                KeyboardButton(text="🛒 Покупатели")
            ],
            [
                KeyboardButton(text="🚛 Перевозчики"),
                KeyboardButton(text="🤝 Брокеры")
            ],
            [
                KeyboardButton(text="📦 Экспедиторы")
            ],
            [
                KeyboardButton(text="⬅️ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def agro_module_actions_inline(section_key: str = "overview") -> InlineKeyboardMarkup:
    # TODO: future implementation — agro CRM quick actions
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Создать",
                    callback_data=f"agr:create:{section_key}"
                ),
                InlineKeyboardButton(
                    text="🔍 Поиск",
                    callback_data=f"agr:search:{section_key}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📋 По заявке",
                    callback_data=f"agr:by_request:{section_key}"
                ),
                InlineKeyboardButton(
                    text="📊 Отчет",
                    callback_data=f"agr:report:{section_key}"
                ),
            ],
        ]
    )

def agro_products_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🌾 Пшеница"),
                KeyboardButton(text="🌽 Кукуруза")
            ],
            [
                KeyboardButton(text="🌻 Подсолнечное масло"),
                KeyboardButton(text="🫒 Оливковое масло")
            ],
            [
                KeyboardButton(text="🍎 Яблоки"),
                KeyboardButton(text="🧂 Сахар")
            ],
            [
                KeyboardButton(text="🫘 Нут"),
                KeyboardButton(text="🌱 Шрот")
            ],
            [
                KeyboardButton(text="🌾 Ячмень"),
                KeyboardButton(text="🌿 Рапс")
            ],
            [
                KeyboardButton(text="⬅ Назад")
            ]
        ],
        resize_keyboard=True
    )

    return keyboard

def product_actions_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🟢 Купить"),
                KeyboardButton(text="🔴 Продать")
            ],
            [
                KeyboardButton(text="📊 Цены"),
                KeyboardButton(text="🚛 Логистика")
            ],
            [
                KeyboardButton(text="📄 Контракты"),
                KeyboardButton(text="🌍 Страны")
            ],
            [
                KeyboardButton(text="🚢 Фрахт"),
                KeyboardButton(text="📈 Аналитика")
            ],
            [
                KeyboardButton(text="⬅ Назад к товарам")
            ]
        ],
        resize_keyboard=True
    )

    return keyboard
def manager_request_menu(request_number: int):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟡 В работу",
                    callback_data=f"work_{request_number}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🟢 Завершить",
                    callback_data=f"done_{request_number}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔴 Отменить",
                    callback_data=f"cancel_{request_number}"
                )
            ]
        ]
    )

    return keyboard
def crm_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📂 Активные заявки"),
                KeyboardButton(text="👤 Мои заявки")
            ],

            [
                KeyboardButton(text="🆕 Новые заявки"),
                KeyboardButton(text="✅ Завершенные")
            ],

            [
                KeyboardButton(text="❌ Отмененные")
            ],

            [
                KeyboardButton(text="📋 CRM"),
                KeyboardButton(text="⬅️ Назад")
            ]
        ],
        resize_keyboard=True
    )

    return keyboard


# ==========================================================
# MODULE MENUS (infrastructure stubs)
# ==========================================================

def law_module_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📂 Дела"),
                KeyboardButton(text="📑 Документы")
            ],
            [
                KeyboardButton(text="📚 Законодательство"),
                KeyboardButton(text="⚖ Судебная практика")
            ],
            [
                KeyboardButton(text="📅 Календарь")
            ],
            [
                KeyboardButton(text="⬅️ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def drone_module_menu():
    # TODO: future implementation — full drone engineering hub
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📁 Проекты"),
                KeyboardButton(text="📋 Спецификации BOM")
            ],
            [
                KeyboardButton(text="🔋 Аккумуляторы"),
                KeyboardButton(text="⚡ Электроника")
            ],
            [
                KeyboardButton(text="📡 Связь и VTX"),
                KeyboardButton(text="🛰 Навигация и GPS")
            ],
            [
                KeyboardButton(text="🧠 Автопилоты"),
                KeyboardButton(text="📐 CAD и чертежи")
            ],
            [
                KeyboardButton(text="💰 Себестоимость"),
                KeyboardButton(text="📦 Закупки")
            ],
            [
                KeyboardButton(text="🤖 AI инженер")
            ],
            [
                KeyboardButton(text="⬅ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def drone_module_actions_inline(section_key: str = "overview") -> InlineKeyboardMarkup:
    # TODO: future implementation — section-specific quick actions
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤖 AI инженер",
                    callback_data="drn:ai:open"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📁 Проекты",
                    callback_data="drn:ai:context:projects"
                ),
                InlineKeyboardButton(
                    text="📋 BOM",
                    callback_data="drn:ai:context:bom"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔋 Аккумуляторы",
                    callback_data="drn:ai:context:batteries"
                ),
                InlineKeyboardButton(
                    text="📐 Чертежи",
                    callback_data="drn:ai:context:drawings"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="◀ К разделу",
                    callback_data=f"drn:section:back:{section_key}"
                ),
            ],
        ]
    )


def cafe_beauty_module_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="☕ Cafe"),
                KeyboardButton(text="💄 Beauty")
            ],
            [
                KeyboardButton(text="📦 Склад"),
                KeyboardButton(text="📅 Календарь")
            ],
            [
                KeyboardButton(text="⬅️ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def users_module_menu():
    # TODO: future implementation — central users & access management hub
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Список пользователей"),
                KeyboardButton(text="➕ Добавить пользователя")
            ],
            [
                KeyboardButton(text="🛡 Роли"),
                KeyboardButton(text="🔐 Права доступа")
            ],
            [
                KeyboardButton(text="📊 Активность"),
                KeyboardButton(text="📝 Журнал действий")
            ],
            [
                KeyboardButton(text="⬅ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def users_module_actions_inline() -> InlineKeyboardMarkup:
    # TODO: future implementation — inline user management actions
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить",
                    callback_data="usr:user:add"
                ),
                InlineKeyboardButton(
                    text="🛡 Роли",
                    callback_data="usr:roles:view"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔐 Права",
                    callback_data="usr:permissions:view"
                ),
                InlineKeyboardButton(
                    text="📝 Журнал",
                    callback_data="usr:audit:view"
                ),
            ],
        ]
    )


def reports_module_menu():
    # TODO: future implementation — central reports hub for all modules
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💰 Финансы"),
                KeyboardButton(text="📈 Прибыль")
            ],
            [
                KeyboardButton(text="👥 Пользователи"),
                KeyboardButton(text="📅 Календарь")
            ],
            [
                KeyboardButton(text="🌾 Agro Trading"),
                KeyboardButton(text="💵 Crypto OTC")
            ],
            [
                KeyboardButton(text="🚁 Drone Engineering"),
                KeyboardButton(text="⚖️ Юриспруденция")
            ],
            [
                KeyboardButton(text="☕ Cafe & Beauty"),
                KeyboardButton(text="🤖 AI аналитика")
            ],
            [
                KeyboardButton(text="⬅ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def reports_module_actions_inline(report_type: str = "summary") -> InlineKeyboardMarkup:
    # TODO: future implementation — dynamic report actions
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Фильтр: даты",
                    callback_data=f"rpt:filter:date:{report_type}"
                ),
                InlineKeyboardButton(
                    text="👤 Фильтр: пользователь",
                    callback_data=f"rpt:filter:user:{report_type}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏢 Фильтр: отдел",
                    callback_data=f"rpt:filter:department:{report_type}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📊 Excel",
                    callback_data=f"rpt:export:excel:{report_type}"
                ),
                InlineKeyboardButton(
                    text="📄 PDF",
                    callback_data=f"rpt:export:pdf:{report_type}"
                ),
            ],
        ]
    )


def calendar_module_menu():
    # TODO: future implementation — central calendar hub for all modules
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 Мои события"),
                KeyboardButton(text="➕ Новое событие")
            ],
            [
                KeyboardButton(text="🔔 Напоминания"),
                KeyboardButton(text="📆 Сегодня")
            ],
            [
                KeyboardButton(text="📈 Неделя"),
                KeyboardButton(text="📂 Все события")
            ],
            [
                KeyboardButton(text="⬅ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def calendar_event_actions_inline(event_id: int) -> InlineKeyboardMarkup:
    # TODO: future implementation — dynamic event action menu
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать",
                    callback_data=f"cal:event:edit:{event_id}"
                ),
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"cal:event:delete:{event_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Завершить",
                    callback_data=f"cal:event:complete:{event_id}"
                ),
                InlineKeyboardButton(
                    text="📅 Перенести",
                    callback_data=f"cal:event:reschedule:{event_id}"
                ),
            ],
        ]
    )


def module_inline_actions(module_key: str) -> InlineKeyboardMarkup:
    # TODO: future implementation — connect module-specific AI agent
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤖 AI агент",
                    callback_data=f"mod:{module_key}:ai"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀ К разделу",
                    callback_data=f"mod:{module_key}:back"
                )
            ]
        ]
    )


def ai_assistant_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📁 Мои проекты"),
                KeyboardButton(text="✅ Мои задачи")
            ],
            [
                KeyboardButton(text="💬 История диалогов")
            ],
            [
                KeyboardButton(text="⚙ Настройки AI")
            ],
            [
                KeyboardButton(text="◀ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def ai_settings_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🎭 Тон общения"),
                KeyboardButton(text="🌐 Язык ответов")
            ],
            [
                KeyboardButton(text="📏 Глубина контекста"),
                KeyboardButton(text="🗑 Очистить историю")
            ],
            [
                KeyboardButton(text="⬅️ К AI помощнику")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def ai_tone_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Нейтральный"),
                KeyboardButton(text="Формальный")
            ],
            [
                KeyboardButton(text="Дружелюбный")
            ],
            [
                KeyboardButton(text="⬅️ К настройкам AI")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def ai_context_depth_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="10 сообщений"),
                KeyboardButton(text="20 сообщений")
            ],
            [
                KeyboardButton(text="40 сообщений")
            ],
            [
                KeyboardButton(text="⬅️ К настройкам AI")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard