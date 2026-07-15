"""DTO/schema placeholders for domain `ai_assistant` — no pydantic dependency required."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AiAssistantDTO:
    id: str | None = None
