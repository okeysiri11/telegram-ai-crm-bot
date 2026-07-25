"""Test Registry — Sprint 25.1."""

from __future__ import annotations

from typing import Any

from platform_testing.models import TEST_CATEGORIES


class TestRegistry:
    def register(
        self,
        *,
        test_id: str,
        name: str,
        module: str,
        category: str = "unit",
        priority: str = "medium",
        owner: str = "qa",
        dependencies: list[str] | None = None,
        tags: list[str] | None = None,
        estimated_duration_ms: int = 100,
        version: str = "1.0",
    ) -> dict[str, Any]:
        if not test_id or not name or not module:
            raise ValueError("test_id, name and module are required")
        category = (category or "unit").lower()
        if category not in TEST_CATEGORIES:
            raise ValueError(f"unsupported category: {category}")
        return {
            "test_id": test_id,
            "name": name.strip(),
            "module": module,
            "category": category,
            "priority": priority,
            "owner": owner,
            "dependencies": list(dependencies or []),
            "tags": list(tags or []),
            "estimated_duration_ms": int(estimated_duration_ms),
            "last_result": None,
            "last_execution": None,
            "version": version,
        }

    def update_result(self, test: dict[str, Any], *, result: str, executed_at: str) -> dict[str, Any]:
        updated = dict(test)
        updated["last_result"] = result
        updated["last_execution"] = executed_at
        return updated
