"""DTO/schema placeholders for domain `notifications` — no pydantic dependency required."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NotificationsDTO:
    id: str | None = None
