"""Command history — prompts, agents, cost, retry."""

from __future__ import annotations

import threading
from typing import Any

from platform_ai_command.core.models import CommandPlan, CommandResult


class CommandHistory:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._by_owner: dict[str, list[dict[str, Any]]] = {}
        self._favorites: dict[str, set[str]] = {}

    def add(self, owner_id: str, plan: CommandPlan, result: CommandResult) -> dict[str, Any]:
        entry = {
            "id": result.plan_id,
            "prompt": plan.message.text,
            "agents": list(plan.route.agents),
            "providers": list(plan.route.providers_hint),
            "vertical": plan.route.vertical,
            "tools": list(plan.route.tools),
            "cost": result.cost,
            "duration_sec": result.duration_sec,
            "status": result.status,
            "reply": result.reply_ru,
            "files": list(result.files),
            "hercules_job_ids": list(result.hercules_job_ids),
            "created_at": result.created_at,
            "favorite": False,
        }
        with self._lock:
            self._by_owner.setdefault(owner_id, []).insert(0, entry)
            self._by_owner[owner_id] = self._by_owner[owner_id][:200]
        return entry

    def list(self, owner_id: str, *, limit: int = 30) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._by_owner.get(owner_id, [])[:limit])

    def toggle_favorite(self, owner_id: str, plan_id: str) -> bool:
        with self._lock:
            favs = self._favorites.setdefault(owner_id, set())
            if plan_id in favs:
                favs.discard(plan_id)
                fav = False
            else:
                favs.add(plan_id)
                fav = True
            for e in self._by_owner.get(owner_id, []):
                if e["id"] == plan_id:
                    e["favorite"] = fav
            return fav

    def favorites(self, owner_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [e for e in self._by_owner.get(owner_id, []) if e.get("favorite")]

    def get(self, owner_id: str, plan_id: str) -> dict[str, Any] | None:
        with self._lock:
            for e in self._by_owner.get(owner_id, []):
                if e["id"] == plan_id:
                    return dict(e)
        return None


command_history = CommandHistory()
