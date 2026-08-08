"""Sprint 46.1 — Dialog State Manager (deterministic Yes/No / VIN / short answers)."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from services.auto_human_conversation_policy import (
    VIN_SKIP_TOKENS,
    VIN_YES_TOKENS,
    is_short_contextual,
)

# Phases
IDLE = "idle"
SEARCHING = "searching"
REFINING = "refining"
VIN_CHOICE = "vin_choice"  # ASK_VIN
VIN_INPUT = "vin_input"  # WAITING_FOR_VIN
LEASING = "leasing"
FINISHING = "finishing"

VIN_SKIPPED = "VIN_SKIPPED"
WAITING_FOR_VIN = "WAITING_FOR_VIN"
VIN_PROVIDED = "VIN_PROVIDED"


@dataclass
class DialogState:
    phase: str = IDLE
    intent: str | None = None
    last_question: str | None = None
    vin_status: str | None = None  # VIN_SKIPPED | WAITING_FOR_VIN | VIN_PROVIDED
    known: dict[str, Any] = field(default_factory=dict)
    workflow: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "intent": self.intent,
            "last_question": self.last_question,
            "vin_status": self.vin_status,
            "known": dict(self.known),
            "workflow": self.workflow,
        }


class AutoDialogStateManager:
    """
    Resolution order for short answers:
    1. active deterministic state
    2. reply_to / last_question context
    3. conversation memory (known)
    4. current workflow
    5. only then general intent (caller)
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._by_user: dict[int, DialogState] = {}

    def get(self, user_id: int) -> DialogState:
        with self._lock:
            st = self._by_user.get(user_id)
            if not st:
                st = DialogState()
                self._by_user[user_id] = st
            return st

    def set_phase(self, user_id: int, phase: str, **kwargs: Any) -> DialogState:
        with self._lock:
            st = self.get(user_id)
            st.phase = phase
            for k, v in kwargs.items():
                if k == "known" and isinstance(v, dict):
                    st.known.update(v)
                elif hasattr(st, k):
                    setattr(st, k, v)
            self._by_user[user_id] = st
            return st

    def update_known(self, user_id: int, **fields: Any) -> DialogState:
        with self._lock:
            st = self.get(user_id)
            for k, v in fields.items():
                if v is not None:
                    st.known[k] = v
            self._by_user[user_id] = st
            return st

    def clear(self, user_id: int | None = None) -> None:
        with self._lock:
            if user_id is None:
                self._by_user.clear()
            else:
                self._by_user.pop(user_id, None)

    def resolve_short_answer(self, user_id: int, text: str) -> dict[str, Any] | None:
        """
        If active dialog state can consume a short answer, return a transition dict.
        Otherwise None → caller may run general intent.
        """
        raw = (text or "").strip()
        low = raw.lower()
        st = self.get(user_id)

        # 1. active deterministic state — VIN choice
        if st.phase == VIN_CHOICE:
            if low in VIN_SKIP_TOKENS or low == "2":
                return self._vin_skip(user_id)
            if low in VIN_YES_TOKENS or low == "1":
                return self._vin_yes(user_id)
            # unknown while in VIN_CHOICE — still treat as need re-ask only if not contextual skip
            if is_short_contextual(low):
                return self._vin_skip(user_id)

        if st.phase == VIN_INPUT:
            if low in VIN_SKIP_TOKENS:
                return self._vin_skip(user_id)
            # otherwise treat as VIN value
            return {
                "handled": True,
                "event": VIN_PROVIDED,
                "phase": FINISHING,
                "vin": raw.upper(),
                "reply_ru": None,
                "continue_workflow": True,
            }

        # Short answers are NOT standalone intents when dialog active
        if is_short_contextual(low) and st.phase not in {IDLE, None}:
            if low in {"ищи", "давай", "да", "ок", "сюда"}:
                return {
                    "handled": True,
                    "event": "FORCE_SEARCH",
                    "phase": st.phase,
                    "continue_workflow": True,
                    "force_search": True,
                }
            if low in {"не важно", "неважно", "любой", "любая"}:
                return {
                    "handled": True,
                    "event": "SKIP_OPTIONAL",
                    "phase": st.phase,
                    "continue_workflow": True,
                    "force_search": True,
                }
            # "нет"/"2" without VIN phase — do not invent new intent
            return {
                "handled": True,
                "event": "CONTEXTUAL_NOOP",
                "phase": st.phase,
                "continue_workflow": True,
                "force_search": True,
            }

        return None

    def begin_vin_choice(self, user_id: int) -> DialogState:
        return self.set_phase(user_id, VIN_CHOICE, last_question="vin_optional", vin_status=None)

    def _vin_skip(self, user_id: int) -> dict[str, Any]:
        self.set_phase(user_id, FINISHING, vin_status=VIN_SKIPPED)
        return {
            "handled": True,
            "event": VIN_SKIPPED,
            "phase": FINISHING,
            "vin": None,
            "reply_ru": "Хорошо, без VIN.",
            "continue_workflow": True,
        }

    def _vin_yes(self, user_id: int) -> dict[str, Any]:
        self.set_phase(user_id, VIN_INPUT, vin_status=WAITING_FOR_VIN, last_question="vin")
        return {
            "handled": True,
            "event": WAITING_FOR_VIN,
            "phase": VIN_INPUT,
            "reply_ru": "Введите VIN автомобиля:",
            "continue_workflow": False,
            "ask_vin_only": True,
        }


auto_dialog_state = AutoDialogStateManager()
