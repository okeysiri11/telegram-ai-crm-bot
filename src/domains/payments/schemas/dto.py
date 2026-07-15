"""DTO/schema placeholders for domain `payments` — no pydantic dependency required."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PaymentsDTO:
    id: str | None = None
