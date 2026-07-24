"""AI Content Generator — Sprint 22.5."""

from __future__ import annotations

from typing import Any

from platform_ai_marketing_os.models import CONTENT_KINDS


class AIContentGenerator:
    def generate(self, *, kind: str, topic: str, brand: dict[str, Any] | None = None) -> dict[str, Any]:
        if kind not in CONTENT_KINDS:
            raise ValueError(f"unknown content kind: {kind}")
        if not topic:
            raise ValueError("topic is required")
        brand = brand or {}
        forbidden = set(brand.get("forbidden_words") or [])
        body = f"{brand.get('tone_of_voice', 'warm')}: {topic} — book today"
        for word in forbidden:
            body = body.replace(word, "***")
        return {
            "kind": kind,
            "topic": topic,
            "body": body,
            "provider_architecture": "enterprise_ai_provider",
            "published": False,
            "requires_approval": True,
        }
