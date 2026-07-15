"""DTO/schema placeholders for domain `insurance` — no pydantic dependency required."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InsuranceDTO:
    id: str | None = None
