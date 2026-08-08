"""Conversation + session context for Command Center."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Turn:
    role: str  # user|assistant
    text: str
    ts: float = field(default_factory=time.time)
    meta: dict[str, Any] = field(default_factory=dict)


class ConversationStore:
    def __init__(self, *, max_turns: int = 100) -> None:
        self._lock = threading.RLock()
        self._sessions: dict[str, list[Turn]] = {}
        self.max_turns = max_turns
        self._context: dict[str, dict[str, Any]] = {}

    def key(self, owner_id: str, session_id: str | None = None) -> str:
        return f"{owner_id}:{session_id or 'default'}"

    def add(self, key: str, role: str, text: str, **meta: Any) -> None:
        with self._lock:
            turns = self._sessions.setdefault(key, [])
            turns.append(Turn(role=role, text=text, meta=meta))
            if len(turns) > self.max_turns:
                self._sessions[key] = turns[-self.max_turns :]

    def history(self, key: str, *, limit: int = 20) -> list[Turn]:
        with self._lock:
            return list(self._sessions.get(key, [])[-limit:])

    def set_context(self, key: str, **kwargs: Any) -> None:
        with self._lock:
            ctx = self._context.setdefault(key, {})
            ctx.update(kwargs)

    def get_context(self, key: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._context.get(key, {}))

    def new_dialog(self, key: str) -> None:
        with self._lock:
            self._sessions[key] = []


conversation_store = ConversationStore()
