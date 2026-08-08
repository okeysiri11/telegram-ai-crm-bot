"""Mode preferences & permissions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_modes.mode_state import WorkMode


# Actions that always require confirmation regardless of mode
CONFIRM_REQUIRED_ACTIONS: frozenset[str] = frozenset(
    {
        "delete",
        "payment",
        "export",
        "send_message",
        "publish",
        "launch_ads",
        "change_settings",
        "удаление",
        "оплата",
        "экспорт",
        "отправка",
        "публикация",
        "реклама",
        "настройки",
    }
)


@dataclass
class ModeSettings:
    remember_last_mode: bool = True
    start_in_human: bool = True
    start_in_ai: bool = False
    start_voice_after_login: bool = False
    require_confirmation: bool = True
    show_execution_plan: bool = True
    speak_answers: bool = True
    show_agents: bool = True
    show_cost: bool = True
    show_duration: bool = True
    default_mode: WorkMode = WorkMode.HUMAN_MODE

    def to_dict(self) -> dict[str, Any]:
        return {
            "remember_last_mode": self.remember_last_mode,
            "start_in_human": self.start_in_human,
            "start_in_ai": self.start_in_ai,
            "start_voice_after_login": self.start_voice_after_login,
            "require_confirmation": self.require_confirmation,
            "show_execution_plan": self.show_execution_plan,
            "speak_answers": self.speak_answers,
            "show_agents": self.show_agents,
            "show_cost": self.show_cost,
            "show_duration": self.show_duration,
            "default_mode": self.default_mode.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ModeSettings:
        data = data or {}
        from platform_modes.mode_state import parse_mode

        dm = parse_mode(data.get("default_mode")) or WorkMode.HUMAN_MODE
        if dm == WorkMode.AUTO_MODE:
            dm = WorkMode.HUMAN_MODE
        return cls(
            remember_last_mode=bool(data.get("remember_last_mode", True)),
            start_in_human=bool(data.get("start_in_human", True)),
            start_in_ai=bool(data.get("start_in_ai", False)),
            start_voice_after_login=bool(data.get("start_voice_after_login", False)),
            require_confirmation=bool(data.get("require_confirmation", True)),
            show_execution_plan=bool(data.get("show_execution_plan", True)),
            speak_answers=bool(data.get("speak_answers", True)),
            show_agents=bool(data.get("show_agents", True)),
            show_cost=bool(data.get("show_cost", True)),
            show_duration=bool(data.get("show_duration", True)),
            default_mode=dm,
        )


def requires_confirmation(action: str, *, settings: ModeSettings | None = None) -> bool:
    """Sensitive actions always need confirm; optional general confirm via settings."""
    s = settings or ModeSettings()
    key = (action or "").lower().strip()
    sensitive = any(a in key for a in CONFIRM_REQUIRED_ACTIONS)
    if sensitive:
        return True
    if action in ("answer", "reply", "chat", "run"):
        return False if not s.require_confirmation else (action not in ("answer", "reply", "chat"))
    return bool(s.require_confirmation)


def can_auto_run_agents(mode: WorkMode) -> bool:
    return mode in (WorkMode.AI_MODE, WorkMode.VOICE_MODE)


def can_proactive_suggest(mode: WorkMode) -> bool:
    return mode in (WorkMode.AI_MODE, WorkMode.VOICE_MODE)


def can_execute_via_hercules(mode: WorkMode) -> bool:
    """Human mode still may answer via Command Center when explicitly asked — no auto chains."""
    return mode in (WorkMode.AI_MODE, WorkMode.VOICE_MODE, WorkMode.HUMAN_MODE)


def voice_continuous(mode: WorkMode) -> bool:
    return mode == WorkMode.VOICE_MODE
