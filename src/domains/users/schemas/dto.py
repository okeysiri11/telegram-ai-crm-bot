"""DTO/schema placeholders for domain `users` — no pydantic dependency required."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UsersDTO:
    id: str | None = None
