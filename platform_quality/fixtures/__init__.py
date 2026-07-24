"""Test data management — Sprint 21.5."""

from __future__ import annotations

from typing import Any
import uuid


class TestDataPlatform:
    def generate(self, *, kind: str = "organization", count: int = 3) -> dict[str, Any]:
        factories = {
            "organization": lambda i: {"id": f"org_{i}", "name": f"Org {i}"},
            "user": lambda i: {"id": f"user_{i}", "email": f"user{i}@example.com"},
            "deal": lambda i: {"id": f"deal_{i}", "amount": 1000 * (i + 1)},
            "workflow": lambda i: {"id": f"wf_{i}", "status": "ready"},
        }
        factory = factories.get(kind, factories["organization"])
        items = [factory(i) for i in range(max(1, int(count)))]
        return {
            "fixture_id": f"fix_{uuid.uuid4().hex[:12]}",
            "kind": kind,
            "items": items,
            "environment": "isolated",
            "count": len(items),
        }
