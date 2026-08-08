"""Context memory — org, role, vertical, clients without re-asking."""

from __future__ import annotations

import threading
from typing import Any


class ContextMemory:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._data: dict[str, dict[str, Any]] = {}

    def update(self, owner_id: str, **kwargs: Any) -> None:
        with self._lock:
            ctx = self._data.setdefault(owner_id, {})
            ctx.update({k: v for k, v in kwargs.items() if v is not None})

    def get(self, owner_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._data.get(owner_id, {}))

    def enrich_prompt(self, owner_id: str, prompt: str) -> str:
        ctx = self.get(owner_id)
        if not ctx:
            return prompt
        bits = []
        for k in ("organization", "vertical", "role", "project", "client"):
            if ctx.get(k):
                bits.append(f"{k}={ctx[k]}")
        if not bits:
            return prompt
        return f"{prompt}\n\n[контекст: {'; '.join(bits)}]"


context_memory = ContextMemory()
