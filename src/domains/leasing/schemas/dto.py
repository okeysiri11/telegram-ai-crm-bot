"""DTO/schema placeholders for domain `leasing` — no pydantic dependency required."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LeasingDTO:
    id: str | None = None
