from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def owner_main_menu(*, show_automotive: bool = True):
    keyboard_rows = [
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
            KeyboardButton(text="🏢 Company Core"),
        ],
    ]
    if show_automotive:
        keyboard_rows.append([KeyboardButton(text=AUTO_VERTICAL_MAIN_BUTTON)])
    keyboard_rows.extend([
            [
                KeyboardButton(text="👥 Пользователи"),
            ],
            [
                KeyboardButton(text="📅 Календарь"),
                KeyboardButton(text="📊 Аналитика")
            ],
            [
                KeyboardButton(text="🤖 AI Агенты"),
                KeyboardButton(text="🤖 AI помощник")
            ],
            [
                KeyboardButton(text="🔔 Уведомления"),
                KeyboardButton(text="✅ Задачи")
            ],
            [
                KeyboardButton(text="📂 Файлы"),
                KeyboardButton(text="🔎 Поиск")
            ],
            [
                KeyboardButton(text="📊 Отчеты"),
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
            ],
            [
                KeyboardButton(text="👑 Owner Panel"),
            ],
            [
                KeyboardButton(text="🤝 Partner Cabinet"),
            ],
            [
                KeyboardButton(text="📊 Owner Dashboard"),
            ],
            [
                KeyboardButton(text="⚙ Настройки"),
            ],
            [
                KeyboardButton(text="🧪 Тестовый центр"),
                KeyboardButton(text="❤️ System Health"),
            ],
    ])
    keyboard = ReplyKeyboardMarkup(
        keyboard=keyboard_rows,
        resize_keyboard=True
    )

    return keyboard


def owner_panel_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Owner Dashboard")],
            [
                KeyboardButton(text="🤝 Partner Cabinet"),
                KeyboardButton(text="🔗 Entry Links"),
            ],
            [
                KeyboardButton(text="📝 Notes"),
            ],
            [
                KeyboardButton(text="💳 Payment Profile"),
            ],
            [KeyboardButton(text="⬅ Назад")],
        ],
        resize_keyboard=True,
    )


def partner_cabinet_menu(*, owner: bool = False) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text="🔄 Обновить")]]
    if owner:
        rows.append([KeyboardButton(text="🤝 Partner Cabinet")])
    rows.append([KeyboardButton(text="⬅ Назад")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def owner_dashboard_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📈 Marketing Analytics"),
                KeyboardButton(text="💰 Revenue Analytics"),
            ],
            [
                KeyboardButton(text="👥 Manager Analytics"),
                KeyboardButton(text="🤝 Partner Analytics"),
            ],
            [
                KeyboardButton(text="📋 Pipeline Analytics"),
            ],
            [
                KeyboardButton(text="⏱ SLA Analytics"),
            ],
            [
                KeyboardButton(text="🛡 Anti Loss Analytics"),
            ],
            [
                KeyboardButton(text="💳 Payment Analytics"),
            ],
            [
                KeyboardButton(text="🏦 Settlement Analytics"),
            ],
            [
                KeyboardButton(text="📋 Pipeline Board"),
            ],
            [KeyboardButton(text="⬅ Назад")],
        ],
        resize_keyboard=True,
    )


def tenant_scoped_menu(ctx: dict | None = None, lang: str | None = None) -> ReplyKeyboardMarkup | None:
    from services.automotive_localization import normalize_language, t

    if not ctx or not ctx.get("tenant_scoped"):
        return None
    language = normalize_language(lang or ctx.get("language"))
    tenant_code = ctx.get("tenant_code") or ""
    vertical = ctx.get("vertical") or "auto"
    rows: list[list[KeyboardButton]] = []

    if vertical == "auto" or tenant_code.startswith("auto_") or tenant_code.endswith("_partner"):
        rows.append([KeyboardButton(text=AUTO_VERTICAL_MAIN_BUTTON)])
    elif vertical == "agro":
        rows.append([KeyboardButton(text="🌾 Agro Trading")])
    elif vertical == "drones":
        rows.append([KeyboardButton(text="🚁 Drone Engineering")])
    elif vertical == "legal":
        rows.append([KeyboardButton(text="⚖ Юриспруденция")])
    elif vertical in {"finance", "crypto"}:
        rows.append([KeyboardButton(text="💰 Crypto OTC")])

    rows.append([KeyboardButton(text="🏠 Мой раздел")])
    cart_label = "🛒 Кошик" if language == "uk" else "🛒 Корзина"
    rows.append([KeyboardButton(text=cart_label)])
    rows.append([KeyboardButton(text=t("settings_title", language))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


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
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Мои задачи"),
                KeyboardButton(text="📌 Активные"),
            ],
            [
                KeyboardButton(text="✅ Завершенные"),
                KeyboardButton(text="⚠ Просроченные"),
            ],
            [
                KeyboardButton(text="👥 Все задачи"),
                KeyboardButton(text="➕ Новая задача"),
            ],
            [
                KeyboardButton(text="⬅ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def tasks_list_inline(tasks_rows) -> InlineKeyboardMarkup:
    rows = []
    for row in tasks_rows[:15]:
        tid, title = row[0], row[1]
        short = title if len(title) <= 32 else title[:29] + "..."
        rows.append([
            InlineKeyboardButton(
                text=f"#{tid} {short}",
                callback_data=f"tsk:open:{tid}",
            ),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows or [[
        InlineKeyboardButton(text="—", callback_data="tsk:noop:0"),
    ]])


def task_card_inline(task_id: int) -> InlineKeyboardMarkup:
    tid = task_id
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="▶ В работу", callback_data=f"tsk:start:{tid}"),
                InlineKeyboardButton(text="⏸ Пауза", callback_data=f"tsk:pause:{tid}"),
            ],
            [
                InlineKeyboardButton(text="✅ Завершить", callback_data=f"tsk:complete:{tid}"),
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"tsk:cancel:{tid}"),
            ],
            [
                InlineKeyboardButton(text="✏ Изменить", callback_data=f"tsk:edit:{tid}"),
                InlineKeyboardButton(text="👤 Назначить", callback_data=f"tsk:assign:{tid}"),
            ],
            [
                InlineKeyboardButton(text="📅 Изменить срок", callback_data=f"tsk:deadline:{tid}"),
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"tsk:del:{tid}"),
            ],
        ]
    )


def task_delete_confirm_inline(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить",
                    callback_data=f"tsk:del:yes:{task_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=f"tsk:open:{task_id}",
                ),
            ],
        ]
    )


def tasks_module_actions_inline(task_id: int = 0) -> InlineKeyboardMarkup:
    if task_id:
        return task_card_inline(task_id)
    return InlineKeyboardMarkup(inline_keyboard=[])


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
                KeyboardButton(text="🟢 Buy USDT"),
                KeyboardButton(text="🔴 Sell USDT"),
            ],
            [
                KeyboardButton(text="💵 Buy Cash"),
                KeyboardButton(text="💴 Sell Cash"),
            ],
            [
                KeyboardButton(text="📑 Сделки OTC"),
                KeyboardButton(text="🤖 Crypto Agent"),
            ],
            [
                KeyboardButton(text="💵 Курсы"),
                KeyboardButton(text="📊 PnL"),
            ],
            [
                KeyboardButton(text="⬅️ Назад"),
            ],
        ],
        resize_keyboard=True,
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
                KeyboardButton(text="📑 Сделки"),
            ],
            [
                KeyboardButton(text="📄 Документы"),
                KeyboardButton(text="💵 Финансы"),
            ],
            [
                KeyboardButton(text="📊 Отчеты Agro"),
                KeyboardButton(text="🤖 AI Agro"),
            ],
            [
                KeyboardButton(text="⬅️ Назад")
            ]
        ],
        resize_keyboard=True
    )

    return keyboard


def agro_deal_hub_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="▶️ Активные сделки"),
                KeyboardButton(text="🤝 Переговоры"),
            ],
            [
                KeyboardButton(text="📑 Контракты ERP"),
                KeyboardButton(text="🚢 Логистика ERP"),
            ],
            [
                KeyboardButton(text="💳 Платежи"),
                KeyboardButton(text="🏁 Закрытые сделки"),
            ],
            [
                KeyboardButton(text="📊 Аналитика сделок"),
            ],
            [
                KeyboardButton(text="⬅️ Назад в Agro"),
            ],
        ],
        resize_keyboard=True,
    )


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

AGRO_PRODUCT_CATALOG = [
    "🌾 Пшеница",
    "🌽 Кукуруза",
    "🌻 Подсолнечное масло",
    "🫒 Оливковое масло",
    "🍎 Яблоки",
    "🧂 Сахар",
    "🫘 Нут",
    "🌱 Шрот",
    "🌾 Ячмень",
    "🌱 Рапс",
]


def agro_products_inline() -> InlineKeyboardMarkup:
    rows = []
    row = []
    for idx, product in enumerate(AGRO_PRODUCT_CATALOG):
        row.append(
            InlineKeyboardButton(
                text=product,
                callback_data=f"agr:prod:{idx}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_actions_inline(product_idx: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟢 Купить",
                    callback_data=f"agr:buy:{product_idx}",
                ),
                InlineKeyboardButton(
                    text="🔴 Продать",
                    callback_data=f"agr:sell:{product_idx}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅ Назад к товарам",
                    callback_data="agr:nav:products",
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
                KeyboardButton(text="📥 New Leads"),
                KeyboardButton(text="📋 My Leads"),
            ],
            [
                KeyboardButton(text="🆕 Новые заявки"),
                KeyboardButton(text="👤 Мои заявки"),
            ],
            [
                KeyboardButton(text="👥 Clients"),
                KeyboardButton(text="📊 Statistics"),
            ],
            [
                KeyboardButton(text="✅ Завершенные"),
                KeyboardButton(text="❌ Отмененные"),
            ],
            [
                KeyboardButton(text="📋 CRM"),
                KeyboardButton(text="⬅️ Назад"),
            ],
        ],
        resize_keyboard=True,
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


def calendar_module_menu(user_id: int = None):
    from services.calendar_access import CalendarAccessService

    rows = [
        [
            KeyboardButton(text="📅 Мой календарь"),
            KeyboardButton(text="🏢 Календарь отдела"),
        ],
    ]
    if user_id is not None and CalendarAccessService.can_see_all_company(user_id):
        rows.append([KeyboardButton(text="🌍 Все события компании")])
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            *rows,
            [
                KeyboardButton(text="📅 Сегодня"),
                KeyboardButton(text="📆 Неделя"),
            ],
            [
                KeyboardButton(text="🗓 Месяц"),
                KeyboardButton(text="➕ Создать событие"),
            ],
            [
                KeyboardButton(text="🔔 Напоминания"),
            ],
            [
                KeyboardButton(text="⬅ Назад")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def calendar_events_list_inline(events) -> InlineKeyboardMarkup:
    rows = []
    for event in events[:15]:
        eid, title = event[0], event[1]
        short = title if len(title) <= 32 else title[:29] + "..."
        rows.append([
            InlineKeyboardButton(
                text=f"#{eid} {short}",
                callback_data=f"cal:open:{eid}",
            ),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows or [[
        InlineKeyboardButton(text="—", callback_data="cal:noop:0"),
    ]])


def calendar_event_actions_inline(event_id: int) -> InlineKeyboardMarkup:
    eid = event_id
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="▶ Активировать", callback_data=f"cal:active:{eid}"),
                InlineKeyboardButton(text="✅ Завершить", callback_data=f"cal:complete:{eid}"),
            ],
            [
                InlineKeyboardButton(text="✏ Изменить", callback_data=f"cal:edit:{eid}"),
                InlineKeyboardButton(text="📅 Перенести", callback_data=f"cal:reschedule:{eid}"),
            ],
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"cal:cancel:{eid}"),
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"cal:delete:{eid}"),
            ],
        ]
    )


def calendar_event_delete_confirm_inline(event_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить",
                    callback_data=f"cal:del:yes:{event_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=f"cal:open:{event_id}",
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
                KeyboardButton(text="🤖 Общий AI"),
                KeyboardButton(text="🌾 Agro AI"),
            ],
            [
                KeyboardButton(text="💵 Crypto AI"),
                KeyboardButton(text="⚖ Legal AI"),
            ],
            [
                KeyboardButton(text="🚁 Drone AI"),
                KeyboardButton(text="💄 Beauty AI"),
            ],
            [
                KeyboardButton(text="📊 Finance AI"),
                KeyboardButton(text="🔄 Авто-роутинг"),
            ],
            [
                KeyboardButton(text="📁 Мои проекты"),
                KeyboardButton(text="✅ Мои задачи"),
            ],
            [
                KeyboardButton(text="💬 История диалогов"),
            ],
            [
                KeyboardButton(text="⚙ Настройки AI"),
            ],
            [
                KeyboardButton(text="◀ Назад"),
            ],
        ],
        resize_keyboard=True,
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


def ai_projects_list_inline(projects, active_project_id: int = None) -> InlineKeyboardMarkup:
    rows = []
    for project_id, title, *_rest in projects:
        short_title = title if len(title) <= 28 else title[:25] + "..."
        active = " 🔵" if active_project_id == project_id else ""
        rows.append([
            InlineKeyboardButton(
                text=f"📂 {short_title}{active}",
                callback_data=f"ai:proj:open:{project_id}",
            ),
        ])
        rows.append([
            InlineKeyboardButton(
                text="▶️ Активировать",
                callback_data=f"ai:proj:active:{project_id}",
            ),
            InlineKeyboardButton(
                text="🗑 Удалить",
                callback_data=f"ai:proj:del:{project_id}",
            ),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ai_project_detail_inline(project_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶️ Активировать",
                    callback_data=f"ai:proj:active:{project_id}",
                ),
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"ai:proj:del:{project_id}",
                ),
            ],
        ]
    )


def ai_project_delete_confirm_inline(project_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить",
                    callback_data=f"ai:proj:del:yes:{project_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=f"ai:proj:open:{project_id}",
                ),
            ],
        ]
    )


def ai_agents_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🧠 Общий AI"),
                KeyboardButton(text="🚁 Drone AI"),
            ],
            [
                KeyboardButton(text="⚖ Legal AI"),
                KeyboardButton(text="🌾 Agro AI"),
            ],
            [
                KeyboardButton(text="💰 Crypto AI"),
                KeyboardButton(text="💄 Beauty AI"),
            ],
            [
                KeyboardButton(text="📜 История агента"),
                KeyboardButton(text="⬅ Назад"),
            ],
        ],
        resize_keyboard=True,
    )


def ai_agents_list_inline(agents: list) -> InlineKeyboardMarkup:
    code_map = {
        "AI_GENERAL": "agent:select:AI_GENERAL",
        "AI_DRONE": "agent:select:AI_DRONE",
        "AI_LEGAL": "agent:select:AI_LEGAL",
        "AI_AGRO": "agent:select:AI_AGRO",
        "AI_CRYPTO": "agent:select:AI_CRYPTO",
        "AI_BEAUTY": "agent:select:AI_BEAUTY",
        "AI_FINANCE": "agent:select:AI_FINANCE",
    }
    rows = []
    for row in agents:
        code, name = row[1], row[2]
        cb = code_map.get(code)
        if cb:
            rows.append([InlineKeyboardButton(text=name, callback_data=cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def dashboard_module_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📊 KPI"),
                KeyboardButton(text="📈 Продажи"),
            ],
            [
                KeyboardButton(text="📅 Загрузка"),
                KeyboardButton(text="📦 Проекты"),
            ],
            [
                KeyboardButton(text="🔔 Уведомления KPI"),
                KeyboardButton(text="📋 Задачи KPI"),
            ],
            [
                KeyboardButton(text="⬅ Назад"),
            ],
        ],
        resize_keyboard=True,
    )


def company_core_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👥 Сотрудники"),
                KeyboardButton(text="🏢 Отделы"),
            ],
            [
                KeyboardButton(text="📊 KPI"),
                KeyboardButton(text="⏱ Учёт времени"),
            ],
            [
                KeyboardButton(text="🟢 Check-in"),
                KeyboardButton(text="🔴 Check-out"),
            ],
            [
                KeyboardButton(text="🤖 HR Agent"),
                KeyboardButton(text="🔔 HR напоминания"),
            ],
            [
                KeyboardButton(text="⬅️ Назад"),
            ],
        ],
        resize_keyboard=True,
    )


def admin_module_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔐 Права пользователя"),
                KeyboardButton(text="🛡 Роли системы"),
            ],
            [
                KeyboardButton(text="📋 Список пользователей"),
                KeyboardButton(text="📝 Журнал действий"),
            ],
            [
                KeyboardButton(text="💰 Revenue Dashboard"),
            ],
            [
                KeyboardButton(text="📈 Lead Dashboard"),
                KeyboardButton(text="📋 Lead List"),
            ],
            [
                KeyboardButton(text="🤝 Deal Dashboard"),
                KeyboardButton(text="📋 Deal List"),
            ],
            [
                KeyboardButton(text="💵 Revenue Engine"),
            ],
            [
                KeyboardButton(text="🛒 Cart Dashboard"),
            ],
            [
                KeyboardButton(text="📋 Pipeline Board"),
            ],
            [
                KeyboardButton(text="⬅ Назад"),
            ],
        ],
        resize_keyboard=True,
    )


def test_center_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🌾 Agro Test"),
                KeyboardButton(text="💰 Crypto Test"),
            ],
            [
                KeyboardButton(text="🚁 Drone Test"),
                KeyboardButton(text="☕ Cafe Test"),
            ],
            [
                KeyboardButton(text="💄 Beauty Test"),
                KeyboardButton(text="⚖ Legal Test"),
            ],
            [
                KeyboardButton(text="📅 Calendar Test"),
                KeyboardButton(text="📁 Files Test"),
            ],
            [
                KeyboardButton(text="🔎 Search Test"),
                KeyboardButton(text="📊 Reports Test"),
            ],
            [
                KeyboardButton(text="🤖 AI Test"),
                KeyboardButton(text="⚙ Workflow Test"),
            ],
            [
                KeyboardButton(text="🔔 Notification Test"),
            ],
            [
                KeyboardButton(text="🚗 Auto Test"),
                KeyboardButton(text="📋 Readiness Test"),
            ],
            [
                KeyboardButton(text="🏢 Tenant Test"),
                KeyboardButton(text="🔐 RBAC Test"),
            ],
            [
                KeyboardButton(text="🚘 Onboarding Test"),
                KeyboardButton(text="🏭 Production Test"),
            ],
            [
                KeyboardButton(text="💱 Treasury Test"),
            ],
            [
                KeyboardButton(text="⬅ Назад"),
            ],
        ],
        resize_keyboard=True,
    )


# ==========================================================
# AUTO VERTICAL (Automotive Telegram UI v2)
# ==========================================================

from services.automotive_localization import btn, normalize_language, t

AUTO_VERTICAL_MAIN_BUTTON = "🚗 Авто"

_HUB_BUTTON_KEYS = (
    "hub_cars",
    "hub_insurance",
    "hub_credit",
    "hub_leasing",
    "hub_logistics",
    "hub_legal",
    "back",
)
_MENU_BUTTON_KEYS = (
    "add_car",
    "list_cars",
    "search_car",
    "profit_calc",
    "marketing",
    "analytics",
    "ai_manager",
    "leads",
    "billing",
    "dealer_rates",
    "treasury",
    "auto_settings",
    "back_to_hub",
)


def _localized_button_set(keys: tuple[str, ...], lang: str | None = None) -> frozenset[str]:
    language = normalize_language(lang)
    return frozenset(btn(key, language) for key in keys)


AUTO_VERTICAL_HUB_BUTTONS = _localized_button_set(_HUB_BUTTON_KEYS, "ru")
AUTO_VERTICAL_MENU_BUTTONS = _localized_button_set(_MENU_BUTTON_KEYS, "ru")


def auto_vertical_hub_menu(lang: str | None = None) -> ReplyKeyboardMarkup:
    language = normalize_language(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=btn("hub_cars", language))],
            [
                KeyboardButton(text=btn("hub_insurance", language)),
                KeyboardButton(text=btn("hub_credit", language)),
            ],
            [
                KeyboardButton(text=btn("hub_leasing", language)),
                KeyboardButton(text=btn("hub_logistics", language)),
            ],
            [KeyboardButton(text=btn("hub_legal", language))],
            [KeyboardButton(text=btn("back", language))],
        ],
        resize_keyboard=True,
    )


def auto_client_services_menu(lang: str | None = None) -> ReplyKeyboardMarkup:
    language = normalize_language(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=btn("hub_insurance", language)),
                KeyboardButton(text=btn("hub_credit", language)),
            ],
            [
                KeyboardButton(text=btn("hub_leasing", language)),
                KeyboardButton(text=btn("hub_logistics", language)),
            ],
            [KeyboardButton(text=btn("hub_legal", language))],
            [KeyboardButton(text=btn("back", language))],
        ],
        resize_keyboard=True,
    )


def auto_client_menu(lang: str | None = None) -> ReplyKeyboardMarkup:
    from services.automotive_localization import btn, normalize_language

    language = normalize_language(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=btn("client_buy_car", language))],
            [KeyboardButton(text=btn("client_sell_car", language))],
            [KeyboardButton(text=btn("client_listing", language))],
            [KeyboardButton(text=btn("client_services", language))],
            [KeyboardButton(text=btn("client_manager", language))],
            [KeyboardButton(text=btn("client_my_requests", language))],
        ],
        resize_keyboard=True,
    )


def auto_client_phone_keyboard(lang: str | None = None) -> ReplyKeyboardMarkup:
    from services.automotive_localization import btn, normalize_language

    language = normalize_language(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Share phone number", request_contact=True)],
            [KeyboardButton(text=btn("client_buy_car", language))],
        ],
        resize_keyboard=True,
    )


def manager_dashboard_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📥 New Leads"),
                KeyboardButton(text="📋 My Leads"),
            ],
            [
                KeyboardButton(text="👥 Clients"),
                KeyboardButton(text="📊 Statistics"),
            ],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )


def auto_client_photos_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Готово", callback_data="ac:photos:done"),
                InlineKeyboardButton(text="⏭ Пропустить", callback_data="ac:photos:skip"),
            ],
        ]
    )


def auto_client_vin_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить VIN", callback_data="ac:vin:add"),
                InlineKeyboardButton(text="⏭ Пропустить", callback_data="ac:vin:skip"),
            ],
        ]
    )


def entry_flow_language_inline(*, prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇦 Русский", callback_data=f"{prefix}:lang:ru")],
            [InlineKeyboardButton(text="🇺🇦 Українська", callback_data=f"{prefix}:lang:uk")],
        ]
    )


def auto_vertical_menu(lang: str | None = None) -> ReplyKeyboardMarkup:
    language = normalize_language(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=btn("add_car", language)),
                KeyboardButton(text=btn("list_cars", language)),
            ],
            [
                KeyboardButton(text=btn("search_car", language)),
                KeyboardButton(text=btn("profit_calc", language)),
            ],
            [
                KeyboardButton(text=btn("marketing", language)),
                KeyboardButton(text=btn("analytics", language)),
            ],
            [
                KeyboardButton(text=btn("ai_manager", language)),
                KeyboardButton(text=btn("leads", language)),
            ],
            [
                KeyboardButton(text=btn("billing", language)),
                KeyboardButton(text=btn("dealer_rates", language)),
            ],
            [KeyboardButton(text=btn("treasury", language))],
            [KeyboardButton(text=btn("auto_settings", language))],
            [KeyboardButton(text=btn("back_to_hub", language))],
        ],
        resize_keyboard=True,
    )


def auto_partner_cards_inline(cards: list[dict], *, category: str, lang: str | None = None) -> InlineKeyboardMarkup:
    language = normalize_language(lang)
    rows = []
    for card in cards:
        code = card.get("code", "partner")
        emoji = (card.get("branding") or {}).get("logo_emoji") or "🤝"
        name = card.get("name", code)
        rows.append([
            InlineKeyboardButton(
                text=f"{emoji} {name}",
                callback_data=f"partner:card:{category}:{code}",
            )
        ])
    rows.append([InlineKeyboardButton(text=t("back_inline", language), callback_data=f"partner:back:{category}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def auto_partner_cta_inline(partner_code: str, ctas: list[dict], lang: str | None = None) -> InlineKeyboardMarkup:
    language = normalize_language(lang)
    rows = []
    for cta in ctas:
        rows.append([
            InlineKeyboardButton(
                text=cta.get("label", "Action"),
                callback_data=f"partner:cta:{partner_code}:{cta.get('cta_code')}",
            )
        ])
    rows.append([
        InlineKeyboardButton(text=t("back_partners", language), callback_data="partner:hub")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def auto_insurance_products_inline(products: list[dict], lang: str | None = None) -> InlineKeyboardMarkup:
    language = normalize_language(lang)
    rows = []
    for product in products:
        rows.append([
            InlineKeyboardButton(
                text=product.get("name", product.get("product_code", "Product")),
                callback_data=f"insurance:product:{product.get('product_code')}",
            )
        ])
    rows.append([InlineKeyboardButton(text=t("back_inline", language), callback_data="insurance:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def dealer_onboarding_automotive_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚗 Automotive",
                    callback_data="onboard:automotive",
                ),
            ],
        ]
    )


def dealer_onboarding_resume_inline(current_step: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="▶ Продолжить onboarding",
                callback_data="onboard:resume",
            ),
        ],
    ]
    if current_step in {"started", "automotive_selected"}:
        rows[0].insert(
            0,
            InlineKeyboardButton(
                text="🚗 Automotive",
                callback_data="onboard:automotive",
            ),
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def auto_billing_plans_inline() -> InlineKeyboardMarkup:
    from database.models.tenant_billing_engine import BillingPlanCode

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="STARTER",
                    callback_data=f"billing:plan:{BillingPlanCode.STARTER.value}",
                ),
                InlineKeyboardButton(
                    text="PRO",
                    callback_data=f"billing:plan:{BillingPlanCode.PRO.value}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="BUSINESS",
                    callback_data=f"billing:plan:{BillingPlanCode.BUSINESS.value}",
                ),
                InlineKeyboardButton(
                    text="ENTERPRISE",
                    callback_data=f"billing:plan:{BillingPlanCode.ENTERPRISE.value}",
                ),
            ],
            [
                InlineKeyboardButton(text="◀ Назад", callback_data="billing:back:menu"),
            ],
        ]
    )


def auto_billing_pricing_inline(plan_code: str) -> InlineKeyboardMarkup:
    from database.models.commercial_billing_engine import PricingModel

    models = (
        PricingModel.SUBSCRIPTION,
        PricingModel.PER_LEAD,
        PricingModel.REVENUE_SHARE,
        PricingModel.HYBRID,
        PricingModel.CUSTOM,
    )
    rows = []
    row: list[InlineKeyboardButton] = []
    for model in models:
        row.append(
            InlineKeyboardButton(
                text=model.value.replace("_", " ").title()[:20],
                callback_data=f"billing:pricing:{plan_code}:{model.value}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="◀ Назад", callback_data="billing:back:plans")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def auto_billing_payment_inline(plan_code: str, pricing_model: str) -> InlineKeyboardMarkup:
    from database.models.commercial_billing_engine import PaymentMethod

    methods = (
        (PaymentMethod.BANK_CARD.value, "Bank Card"),
        (PaymentMethod.BANK_TRANSFER.value, "Bank Transfer"),
        (PaymentMethod.USDT_TRC20.value, "USDT TRC20"),
        (PaymentMethod.USDT_ERC20.value, "USDT ERC20"),
    )
    rows = [
        [
            InlineKeyboardButton(
                text=label,
                callback_data=f"billing:pay:{plan_code}:{pricing_model}:{code}",
            )
        ]
        for code, label in methods
    ]
    rows.append([InlineKeyboardButton(text="◀ Назад", callback_data=f"billing:back:pricing:{plan_code}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def auto_billing_owner_actions_inline(payment_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Approve",
                    callback_data=f"billing:approve:{payment_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Reject",
                    callback_data=f"billing:reject:{payment_id}",
                ),
            ],
        ]
    )


def auto_vertical_car_list_inline(vehicles: list) -> InlineKeyboardMarkup:
    rows = []
    for vehicle in vehicles[:15]:
        vid = vehicle.get("id", "")
        make = vehicle.get("make", "")
        model = vehicle.get("model", "")
        year = vehicle.get("year", "")
        stock = vehicle.get("stock_number", "") or vehicle.get("vin", "")[-6:]
        label = f"{year} {make} {model}".strip()
        if stock:
            label = f"{label} ({stock})"
        if len(label) > 40:
            label = label[:37] + "..."
        rows.append([
            InlineKeyboardButton(
                text=label or vid[:8],
                callback_data=f"car:open:{vid}",
            ),
        ])
    if not rows:
        rows.append([
            InlineKeyboardButton(text="—", callback_data="car:noop:0"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def auto_vertical_actions_inline(section: str = "overview") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить",
                    callback_data="car:action:add",
                ),
                InlineKeyboardButton(
                    text="📋 Список",
                    callback_data="car:action:list",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔍 Поиск",
                    callback_data="car:action:search",
                ),
                InlineKeyboardButton(
                    text="💰 Прибыль",
                    callback_data="car:action:profit",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="◀ К разделу",
                    callback_data=f"car:section:back:{section}",
                ),
            ],
        ]
    )