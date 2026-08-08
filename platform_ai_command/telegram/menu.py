"""Telegram Command Center menu helpers."""

from __future__ import annotations

from platform_ai_command.core.command_center import ai_command_center

# Exact button labels for Telegram router matching
TG_CMD_NEW_CHAT = "💬 Новый чат"
TG_CMD_VOICE = "🎙 Голосовой режим"
TG_CMD_IMAGE = "🎨 Создать изображение"
TG_CMD_VIDEO = "🎬 Создать видео"
TG_CMD_VOICEOVER = "🎤 Озвучить"
TG_CMD_DOC = "📄 Документ"
TG_CMD_CRM = "📊 CRM"
# Sprint 46.5 — kept for compatibility; navigation is handled by vertical_nav_router
TG_CMD_AUTO = "🚗 Auto"
TG_CMD_CRYPTO = "💰 Crypto"
TG_CMD_AGRO = "🌾 Agro"
TG_CMD_BEAUTY = "💄 Beauty"
TG_CMD_SETTINGS = "⚙ Настройки"
TG_CMD_CENTER = "🧠 AI Command"


def menu_labels() -> list[str]:
    return ai_command_center.telegram_menu_labels()


# Only generative / CRM prompts — NEVER map vertical entry to Hercules
BUTTON_TO_PROMPT: dict[str, str] = {
    TG_CMD_IMAGE: "Создай изображение",
    TG_CMD_VIDEO: "Создай видео",
    TG_CMD_VOICEOVER: "Озвучь текст",
    TG_CMD_DOC: "Создай документ",
    TG_CMD_CRM: "Открой CRM",
}
