"""DTO/schema placeholders for domain `legal` — no pydantic dependency required."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LegalDTO:
    id: str | None = None
