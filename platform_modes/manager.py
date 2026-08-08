"""Mode manager — façade for Dual Experience + AI Command Center gate."""

from __future__ import annotations

from typing import Any

from platform_modes.mode_state import ACTIVE_MODES, WorkMode, indicator_ru
from platform_modes.mode_switch import match_mode_command, try_switch_from_text
from platform_modes.permissions import (
    can_auto_run_agents,
    can_proactive_suggest,
    requires_confirmation,
    voice_continuous,
)
from platform_modes.session_mode import SessionMode, session_mode_store

VERSION = "45.1.0"


class ModeManager:
    VERSION = VERSION

    def get(self, owner_id: str) -> SessionMode:
        return session_mode_store.get(owner_id)

    def status(self, owner_id: str) -> dict[str, Any]:
        session = self.get(owner_id)
        mode = session.mode
        return {
            "mode": mode.value,
            "indicator": indicator_ru(mode),
            "version": self.VERSION,
            "capabilities": {
                "auto_agents": can_auto_run_agents(mode),
                "proactive": can_proactive_suggest(mode),
                "voice_continuous": voice_continuous(mode),
                "manual_ui": mode == WorkMode.HUMAN_MODE,
            },
            "settings": session.settings.to_dict(),
            "active_modes": [m.value for m in ACTIVE_MODES],
        }

    def change(self, owner_id: str, mode: str | WorkMode, *, channel: str = "web") -> dict[str, Any]:
        from platform_modes.mode_state import parse_mode

        parsed = parse_mode(mode)
        if parsed is None:
            return {**self.status(owner_id), "error": "unknown_mode"}
        if parsed == WorkMode.AUTO_MODE:
            return {**self.status(owner_id), "error": "AUTO_MODE ещё не доступен"}
        session_mode_store.set_mode(owner_id, parsed, channel=channel)
        return self.status(owner_id)

    def set_voice(self, owner_id: str, enabled: bool, *, channel: str = "web") -> dict[str, Any]:
        target = WorkMode.VOICE_MODE if enabled else WorkMode.HUMAN_MODE
        session_mode_store.set_mode(owner_id, target, channel=channel)
        return self.status(owner_id)

    def remember_default(self, owner_id: str, mode: str | WorkMode | None = None) -> dict[str, Any]:
        from platform_modes.mode_state import parse_mode

        session = self.get(owner_id)
        target = parse_mode(mode) if mode else session.mode
        if target is None or target == WorkMode.AUTO_MODE:
            target = WorkMode.HUMAN_MODE
        session_mode_store.set_default(owner_id, target)
        return self.status(owner_id)

    def update_settings(self, owner_id: str, data: dict[str, Any]) -> dict[str, Any]:
        session_mode_store.update_settings(owner_id, data)
        return self.status(owner_id)

    def restore(self, owner_id: str) -> dict[str, Any]:
        session_mode_store.restore(owner_id)
        return self.status(owner_id)

    def handle_text_command(self, owner_id: str, text: str, *, channel: str = "web") -> dict[str, Any] | None:
        session = try_switch_from_text(owner_id, text, channel=channel)
        if session is None:
            return None
        return self.status(owner_id)

    def gate_ai_action(self, owner_id: str, *, action: str = "run") -> dict[str, Any]:
        """Policy gate before AI Command Center / Hercules execution."""
        session = self.get(owner_id)
        mode = session.mode
        if mode == WorkMode.HUMAN_MODE:
            return {
                "allowed": action in ("answer", "reply", "chat"),
                "auto_agents": False,
                "proactive": False,
                "confirm": requires_confirmation(action, settings=session.settings),
                "mode": mode.value,
                "message_ru": "Human Mode: AI отвечает только на прямой вопрос, без автозапуска агентов.",
            }
        return {
            "allowed": True,
            "auto_agents": can_auto_run_agents(mode),
            "proactive": can_proactive_suggest(mode),
            "confirm": requires_confirmation(action, settings=session.settings),
            "mode": mode.value,
            "voice": voice_continuous(mode),
            "message_ru": "AI Mode" if mode == WorkMode.AI_MODE else "Voice Mode",
        }

    async def run_command_if_allowed(
        self,
        owner_id: str,
        text: str,
        *,
        channel: str = "web",
        max_steps: int | None = 3,
    ) -> dict[str, Any]:
        """
        Integration path:
        ModeManager → AI Command Center → Planner → Hercules
        Never call agents directly.
        """
        # Mode switch commands take priority
        switched = self.handle_text_command(owner_id, text, channel=channel)
        if switched:
            return {"type": "mode_switch", **switched}

        gate = self.gate_ai_action(owner_id, action="run")
        mode = self.get(owner_id).mode

        if mode == WorkMode.HUMAN_MODE:
            # Explicit ask only — still via Command Center, no multi-agent auto chain
            from platform_ai_command.core.command_center import ai_command_center

            result = await ai_command_center.handle(
                text,
                owner_id=owner_id,
                channel=channel,
                max_steps=1,  # no long autonomous chains
            )
            return {"type": "human_reply", "gate": gate, **result}

        from platform_ai_command.core.command_center import ai_command_center

        result = await ai_command_center.handle(
            text,
            owner_id=owner_id,
            channel=channel,
            voice=(mode == WorkMode.VOICE_MODE),
            max_steps=max_steps,
        )
        return {"type": "ai_execution", "gate": gate, **result}

    def telegram_menu(self, owner_id: str) -> dict[str, Any]:
        st = self.status(owner_id)
        return {
            "title": "⚙ Режим работы",
            "current": st["indicator"],
            "mode": st["mode"],
            "buttons": [
                "⚪ Human Mode",
                "🟢 AI Mode",
                "🎙 Voice Mode",
                "📌 Сделать режимом по умолчанию",
                "📌 Запомнить режим",
            ],
        }


mode_manager = ModeManager()
