"""Natural-language and button mode switching."""

from __future__ import annotations

import re

from platform_modes.mode_state import WorkMode, parse_mode
from platform_modes.session_mode import SessionMode, session_mode_store

# Text / voice commands → mode
_COMMAND_MAP: list[tuple[re.Pattern[str], WorkMode | str]] = [
    (re.compile(r"^\s*ai\s*on\s*$", re.I), WorkMode.AI_MODE),
    (re.compile(r"^\s*ai\s*off\s*$", re.I), WorkMode.HUMAN_MODE),
    (re.compile(r"^\s*voice\s*on\s*$", re.I), WorkMode.VOICE_MODE),
    (re.compile(r"^\s*voice\s*off\s*$", re.I), WorkMode.HUMAN_MODE),
    (re.compile(r"^\s*human\s*mode\s*$", re.I), WorkMode.HUMAN_MODE),
    (re.compile(r"работаем\s*вручную|выключи\s*ai|выключить\s*ai|отключись|остановись|^стоп$", re.I), WorkMode.HUMAN_MODE),
    (re.compile(r"включи\s*ai|включить\s*ai", re.I), WorkMode.AI_MODE),
    (re.compile(r"включи\s*голос|включить\s*голос|голосовой\s*режим", re.I), WorkMode.VOICE_MODE),
]


VOICE_OFF_PHRASES = (
    "стоп",
    "отключись",
    "работаем вручную",
    "выключить ai",
    "выключи ai",
    "voice off",
    "ai off",
)


def match_mode_command(text: str) -> WorkMode | None:
    raw = (text or "").strip()
    if not raw:
        return None
    for pattern, mode in _COMMAND_MAP:
        if pattern.search(raw):
            return mode if isinstance(mode, WorkMode) else parse_mode(mode)
    # Button labels
    low = raw.lower()
    if "human mode" in low or raw.startswith("⚪"):
        return WorkMode.HUMAN_MODE
    if "ai mode" in low or (raw.startswith("🟢") and "ai" in low):
        return WorkMode.AI_MODE
    if "voice mode" in low or raw.startswith("🎙"):
        return WorkMode.VOICE_MODE
    return None


def is_voice_stop(text: str) -> bool:
    q = (text or "").strip().lower()
    return any(p in q for p in VOICE_OFF_PHRASES)


def apply_switch(owner_id: str, mode: WorkMode, *, channel: str = "web") -> SessionMode:
    return session_mode_store.set_mode(owner_id, mode, channel=channel)


def try_switch_from_text(owner_id: str, text: str, *, channel: str = "web") -> SessionMode | None:
    mode = match_mode_command(text)
    if mode is None:
        return None
    return apply_switch(owner_id, mode, channel=channel)
