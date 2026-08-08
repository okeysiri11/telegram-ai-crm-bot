"""Conversation memory for Telegram Super App — remembers prior turns."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock
from time import time
from typing import Any


@dataclass
class Turn:
    role: str  # user | ai | system
    text: str
    ts: float = field(default_factory=time)
    meta: dict[str, Any] = field(default_factory=dict)


class ConversationMemory:
    """In-process memory keyed by telegram user id (tenant-ready key shape)."""

    def __init__(self, *, max_turns: int = 40) -> None:
        self._max = max_turns
        self._lock = Lock()
        self._by_user: dict[str, deque[Turn]] = defaultdict(lambda: deque(maxlen=self._max))
        self._context: dict[str, dict[str, Any]] = defaultdict(dict)

    @staticmethod
    def key(telegram_id: int, tenant_id: str | None = None) -> str:
        return f"{tenant_id or 'default'}:{telegram_id}"

    def add(self, key: str, role: str, text: str, **meta: Any) -> Turn:
        turn = Turn(role=role, text=text, meta=meta)
        with self._lock:
            self._by_user[key].append(turn)
        return turn

    def history(self, key: str, *, limit: int = 20) -> list[Turn]:
        with self._lock:
            items = list(self._by_user.get(key, ()))
        return items[-limit:]

    def last_ai(self, key: str) -> Turn | None:
        for turn in reversed(self.history(key, limit=40)):
            if turn.role == "ai":
                return turn
        return None

    def set_context(self, key: str, **kwargs: Any) -> None:
        with self._lock:
            self._context[key].update(kwargs)

    def get_context(self, key: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._context.get(key, {}))

    def clear(self, key: str) -> None:
        with self._lock:
            self._by_user.pop(key, None)
            self._context.pop(key, None)


conversation_memory = ConversationMemory()
