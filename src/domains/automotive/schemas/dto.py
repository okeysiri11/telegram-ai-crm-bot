"""DTO/schema placeholders for domain `automotive` — no pydantic dependency required."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AutomotiveDTO:
    id: str | None = None
