"""DTO/schema placeholders for domain `analytics` — no pydantic dependency required."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnalyticsDTO:
    id: str | None = None
