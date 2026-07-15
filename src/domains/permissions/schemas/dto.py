"""DTO/schema placeholders for domain `permissions` — no pydantic dependency required."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PermissionsDTO:
    id: str | None = None
