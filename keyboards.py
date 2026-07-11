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
                KeyboardButton(text="🤖 AI помощник")
            ],
            [
                KeyboardButton(text="⚙ Администрирование")
            ]
        ],
        resize_keyboard=True
    )

    return keyboard

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
                KeyboardButton(text="⬅️ Назад")
            ]
        ],
        resize_keyboard=True
    )

    return keyboard

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