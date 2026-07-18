# Memory registry — type catalog and scope policies.

from __future__ import annotations

from typing import Any

from platform_ai.memory.models import MemoryType


class MemoryRegistry:
    def __init__(self) -> None:
        self._policies: dict[str, dict[str, Any]] = {
            MemoryType.CONVERSATION.value: {"ttl_hours": 24, "max_entries": 1000},
            MemoryType.WORKFLOW.value: {"ttl_hours": 168, "max_entries": 500},
            MemoryType.USER.value: {"ttl_hours": None, "max_entries": 5000},
            MemoryType.MANAGER.value: {"ttl_hours": None, "max_entries": 1000},
            MemoryType.PLUGIN.value: {"ttl_hours": None, "max_entries": 2000},
            MemoryType.ORGANIZATION.value: {"ttl_hours": None, "max_entries": 10000},
            MemoryType.SESSION.value: {"ttl_hours": 4, "max_entries": 200},
            MemoryType.TEMPORARY.value: {"ttl_hours": 1, "max_entries": 100},
            MemoryType.LONG_TERM.value: {"ttl_hours": None, "max_entries": 50000},
        }

    def reset(self) -> None:
        pass

    def list_types(self) -> list[str]:
        return [t.value for t in MemoryType]

    def get_policy(self, memory_type: str) -> dict[str, Any]:
        return dict(self._policies.get(memory_type, {"ttl_hours": None, "max_entries": 1000}))

    def summary(self) -> dict[str, Any]:
        return {"types": self.list_types(), "policies": self._policies}


memory_registry = MemoryRegistry()
