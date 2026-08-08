"""
Sprint 46.5 — Vertical Role Registry + view-as session.

AUTHORIZATION (authenticated_role) ≠ VIEW MODE (active_persona).
Platform Owner can view as dealer/client without losing owner identity.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from threading import RLock
from typing import Any

# Canonical view personas per vertical (reuse existing domain roles where possible).
VERTICAL_PERSONAS: dict[str, tuple[str, ...]] = {
    "auto": ("owner", "dealer", "client"),
    "agro": ("owner", "trader", "client"),
    "beauty": ("owner", "manager", "specialist", "client"),
    "travel": ("owner", "manager", "agent", "client"),
    "crypto": ("owner", "trader", "client"),
    "legal": ("owner", "lawyer", "client"),
    "drone": ("owner", "operator", "client"),
    "construction": ("owner", "manager", "client"),
}

PERSONA_LABEL_RU: dict[str, str] = {
    "owner": "👑 Owner",
    "dealer": "🚘 Dealer",
    "client": "👤 Client",
    "trader": "📈 Trader",
    "manager": "💼 Manager",
    "specialist": "👩‍💼 Specialist",
    "agent": "🧳 Agent",
    "lawyer": "⚖ Lawyer",
    "operator": "🛰 Operator",
}

VERTICAL_TITLE_RU: dict[str, str] = {
    "auto": "🚗 AUTO",
    "agro": "🌾 AGRO",
    "beauty": "💄 BEAUTY",
    "travel": "✈ TRAVEL",
    "crypto": "💰 CRYPTO",
    "legal": "⚖ LEGAL",
    "drone": "🚁 DRONES",
    "construction": "🏗 CONSTRUCTION",
}

# Navigation labels → vertical_id (deterministic, never Hercules).
VERTICAL_ENTRY_LABELS: dict[str, str] = {
    "🚗 Auto": "auto",
    "🚗 Авто": "auto",
    "🚗 Cars": "auto",
    "🌾 Agro": "agro",
    "🌾 Агро": "agro",
    "🌾 Agro Trading": "agro",
    "💄 Beauty": "beauty",
    "💄 Красота": "beauty",
    "☕ Cafe & Beauty": "beauty",
    "💰 Crypto": "crypto",
    "💰 Crypto OTC": "crypto",
    "✈ Travel": "travel",
    "✈️ Travel": "travel",
    "⚖ Legal": "legal",
    "⚖ Юриспруденция": "legal",
    "🚁 Дроны": "drone",
    "🚁 Drone Engineering": "drone",
    "🏗 Construction": "construction",
}

BTN_SWITCH_ROLE = "🔄 Сменить роль"
BTN_MAIN_MENU = "🏠 Главное меню"
BTN_BACK = "⬅️ Назад"
BTN_ROLE_BACK = "⬅️ Назад"
BTN_CONCIERGE_OPTIONAL = "🤖 AI Консьерж"

# All role-picker button texts
PERSONA_BUTTONS: frozenset[str] = frozenset(PERSONA_LABEL_RU.values())

NAV_CONTROL_BUTTONS: frozenset[str] = frozenset(
    {BTN_SWITCH_ROLE, BTN_MAIN_MENU, BTN_BACK, BTN_ROLE_BACK, "🔄 Роль"}
)


@dataclass
class VerticalSession:
    user_id: int
    authenticated_role: str = "user"
    active_vertical: str | None = None
    active_persona: str | None = None
    active_module: str | None = None
    fsm_state: str = "platform_home"  # platform_home | vertical_entry | vertical_home
    conversation_context: dict[str, Any] = field(default_factory=dict)

    def breadcrumb(self) -> str:
        if not self.active_vertical:
            return "🏠 Платформа"
        title = VERTICAL_TITLE_RU.get(self.active_vertical, self.active_vertical.upper())
        if self.active_persona:
            persona = PERSONA_LABEL_RU.get(self.active_persona, self.active_persona)
            # Drop emoji for compact: "🚗 Auto · Dealer"
            short = persona.split(" ", 1)[-1] if " " in persona else persona
            vert_short = title.split(" ", 1)[-1] if " " in title else title
            emoji = title.split(" ", 1)[0] if " " in title else ""
            return f"{emoji} {vert_short.title()} · {short}".strip()
        return title

    def ai_context(self) -> dict[str, Any]:
        return {
            "authenticated_role": self.authenticated_role,
            "active_vertical": self.active_vertical,
            "active_persona": self.active_persona,
            "active_module": self.active_module,
        }


class VerticalRoleRegistry:
    """In-process session store (Telegram). Does not mutate platform identity."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._sessions: dict[int, VerticalSession] = {}

    def get(self, user_id: int) -> VerticalSession:
        with self._lock:
            sess = self._sessions.get(user_id)
            if sess is None:
                sess = VerticalSession(user_id=user_id)
                self._sessions[user_id] = sess
            return replace(sess, conversation_context=dict(sess.conversation_context))

    def _set(self, sess: VerticalSession) -> VerticalSession:
        with self._lock:
            self._sessions[sess.user_id] = sess
            return sess

    def ensure_authenticated_role(self, user_id: int, role: str) -> VerticalSession:
        sess = self.get(user_id)
        # Never downgrade platform_owner when viewing as persona
        if sess.authenticated_role == "platform_owner" and role != "platform_owner":
            return sess
        if role and role != sess.authenticated_role:
            sess = replace(sess, authenticated_role=role)
            return self._set(sess)
        return sess

    def begin_vertical(self, user_id: int, vertical_id: str) -> VerticalSession:
        """Enter vertical role selector; clear persona/module; keep authenticated_role."""
        sess = self.get(user_id)
        sess = replace(
            sess,
            active_vertical=vertical_id,
            active_persona=None,
            active_module=None,
            fsm_state="vertical_entry",
            conversation_context={},
        )
        return self._set(sess)

    def set_persona(self, user_id: int, persona: str) -> VerticalSession:
        sess = self.get(user_id)
        allowed = VERTICAL_PERSONAS.get(sess.active_vertical or "", ())
        if persona not in allowed:
            raise ValueError(f"persona {persona} not allowed for {sess.active_vertical}")
        sess = replace(sess, active_persona=persona, fsm_state="vertical_home")
        return self._set(sess)

    def clear_vertical(self, user_id: int) -> VerticalSession:
        sess = self.get(user_id)
        sess = replace(
            sess,
            active_vertical=None,
            active_persona=None,
            active_module=None,
            fsm_state="platform_home",
            conversation_context={},
        )
        return self._set(sess)

    def personas_for(self, vertical_id: str) -> tuple[str, ...]:
        return VERTICAL_PERSONAS.get(vertical_id, ("owner", "client"))

    def resolve_entry_label(self, text: str | None) -> str | None:
        if not text:
            return None
        return VERTICAL_ENTRY_LABELS.get(text.strip())

    def resolve_persona_label(self, text: str | None) -> str | None:
        if not text:
            return None
        stripped = text.strip()
        for code, label in PERSONA_LABEL_RU.items():
            if stripped == label:
                return code
        return None


vertical_role_registry = VerticalRoleRegistry()
