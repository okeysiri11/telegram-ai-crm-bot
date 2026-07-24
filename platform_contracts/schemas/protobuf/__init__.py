"""protobuf schema helpers — Sprint 21.3."""

from __future__ import annotations

from typing import Any


def sample_schema(name: str = "BaseDTO") -> dict[str, Any]:
    return {
        "title": name,
        "type": "object",
        "format": "protobuf",
        "properties": {
            "id": {"type": "string"},
            "version": {"type": "integer"},
            "metadata": {"type": "object"},
        },
        "required": ["id", "version"],
    }
