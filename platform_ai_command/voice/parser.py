"""Voice-first command parsing (Russian)."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceIntent:
    id: str
    patterns: tuple[str, ...]
    text_command: str


VOICE_INTENTS: tuple[VoiceIntent, ...] = (
    VoiceIntent("open_crm", ("открой crm", "открыть crm"), "Открой CRM"),
    VoiceIntent("create_client", ("создай клиента", "новый клиент"), "Создай клиента"),
    VoiceIntent("show_profit", ("покажи прибыль", "покажи доход"), "Покажи прибыль"),
    VoiceIntent("create_ads", ("создай рекламу", "сделай рекламу"), "Создай рекламу"),
    VoiceIntent("create_reels", ("сделай reels", "создай reels", "сделай рилс"), "Сделай Reels"),
    VoiceIntent("create_video", ("создай видео", "сделай видео"), "Создай видео"),
    VoiceIntent("voiceover", ("озвучь ролик", "озвучь видео", "озвучь"), "Озвучь ролик"),
    VoiceIntent("publish", ("опубликуй", "опубликовать"), "Опубликуй"),
    VoiceIntent("create_image", ("создай изображение", "создай картинку"), "Создай изображение"),
    VoiceIntent("create_deal", ("создай сделку",), "Создай сделку"),
    VoiceIntent("create_doc", ("создай документ",), "Создай документ"),
    VoiceIntent("create_pres", ("создай презентацию",), "Создай презентацию"),
    VoiceIntent("create_workflow", ("создай workflow", "создай воркфлоу"), "Создай Workflow"),
    VoiceIntent("run_agent", ("запусти ai agent", "запусти агента"), "Запустить AI Agent"),
)


def parse_voice_transcript(transcript: str) -> str:
    """Map spoken RU phrase → canonical text command."""
    q = (transcript or "").strip().lower()
    for intent in VOICE_INTENTS:
        for p in intent.patterns:
            if p in q:
                return intent.text_command
    # soft normalize
    q2 = re.sub(r"\s+", " ", q)
    return q2[:500] if q2 else transcript


def is_voice_command(text: str) -> bool:
    q = (text or "").lower()
    return any(p in q for intent in VOICE_INTENTS for p in intent.patterns)
