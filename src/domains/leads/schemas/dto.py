"""DTO/schema placeholders for domain `leads` — no pydantic dependency required."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LeadsDTO:
    id: str | None = None
