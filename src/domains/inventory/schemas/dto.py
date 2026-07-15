"""DTO/schema placeholders for domain `inventory` — no pydantic dependency required."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InventoryDTO:
    id: str | None = None
