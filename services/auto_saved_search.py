"""Sprint 46.1 — Saved auto searches / monitoring."""

from __future__ import annotations

import threading
import time
from typing import Any

from services.auto_request_memory import AutoSearchSlots


class AutoSavedSearchStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._items: dict[int, list[dict[str, Any]]] = {}

    def save(self, user_id: int, slots: AutoSearchSlots) -> dict[str, Any]:
        item = {
            "id": f"ss_{user_id}_{int(time.time())}",
            "slots": slots.to_dict(),
            "label_ru": slots.label_ru(),
            "created_at": time.time(),
            "active": True,
        }
        with self._lock:
            self._items.setdefault(user_id, []).append(item)
        return item

    def list_for(self, user_id: int) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._items.get(user_id) or [])

    def due_notifications(self) -> list[dict[str, Any]]:
        """Hook for Automation Engine / Hercules scheduler."""
        with self._lock:
            out = []
            for uid, items in self._items.items():
                for it in items:
                    if it.get("active"):
                        out.append({"user_id": uid, **it})
            return out


auto_saved_search = AutoSavedSearchStore()
