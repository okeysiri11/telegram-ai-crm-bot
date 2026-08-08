"""Epic 45.1 — Dual Experience: Human / AI / Voice modes."""

from __future__ import annotations

import enum


class WorkMode(str, enum.Enum):
    HUMAN_MODE = "human"
    AI_MODE = "ai"
    VOICE_MODE = "voice"
    AUTO_MODE = "auto"  # future


MODE_LABELS_RU: dict[WorkMode, str] = {
    WorkMode.HUMAN_MODE: "⚪ HUMAN MODE",
    WorkMode.AI_MODE: "🟢 AI ACTIVE",
    WorkMode.VOICE_MODE: "🎙 VOICE ACTIVE",
    WorkMode.AUTO_MODE: "🔵 AUTO MODE",
}

MODE_BUTTONS_RU: dict[WorkMode, str] = {
    WorkMode.HUMAN_MODE: "⚪ Human Mode",
    WorkMode.AI_MODE: "🟢 AI Mode",
    WorkMode.VOICE_MODE: "🎙 Voice Mode",
    WorkMode.AUTO_MODE: "🔵 Auto Mode",
}

# Only one active mode at a time — AUTO reserved.
ACTIVE_MODES: tuple[WorkMode, ...] = (
    WorkMode.HUMAN_MODE,
    WorkMode.AI_MODE,
    WorkMode.VOICE_MODE,
)


def parse_mode(value: str | WorkMode | None) -> WorkMode | None:
    if value is None:
        return None
    if isinstance(value, WorkMode):
        return value
    raw = (value or "").strip().lower()
    aliases = {
        "human": WorkMode.HUMAN_MODE,
        "human_mode": WorkMode.HUMAN_MODE,
        "human mode": WorkMode.HUMAN_MODE,
        "ai": WorkMode.AI_MODE,
        "ai_mode": WorkMode.AI_MODE,
        "ai mode": WorkMode.AI_MODE,
        "voice": WorkMode.VOICE_MODE,
        "voice_mode": WorkMode.VOICE_MODE,
        "voice mode": WorkMode.VOICE_MODE,
        "auto": WorkMode.AUTO_MODE,
        "auto_mode": WorkMode.AUTO_MODE,
    }
    return aliases.get(raw)


def indicator_ru(mode: WorkMode) -> str:
    return MODE_LABELS_RU.get(mode, MODE_LABELS_RU[WorkMode.HUMAN_MODE])
