"""Brand Center — Sprint 22.5."""

from __future__ import annotations

from typing import Any


class BrandCenter:
    def create(
        self,
        *,
        name: str,
        colors: list[str] | None = None,
        fonts: list[str] | None = None,
        tone_of_voice: str = "warm_professional",
        style: str = "friendly",
        positioning: str = "premium_beauty",
        audience: str = "local_women_25_45",
        advantages: list[str] | None = None,
        forbidden_words: list[str] | None = None,
        templates: list[str] | None = None,
        logo: str = "",
    ) -> dict[str, Any]:
        if not name:
            raise ValueError("brand name is required")
        return {
            "name": name.strip(),
            "logo": logo,
            "colors": list(colors or ["#1F2937", "#F472B6"]),
            "fonts": list(fonts or ["DisplaySans", "BodySans"]),
            "tone_of_voice": tone_of_voice,
            "style": style,
            "positioning": positioning,
            "audience": audience,
            "advantages": list(advantages or ["expert_masters", "convenient_booking"]),
            "forbidden_words": list(forbidden_words or ["cheap", "guaranteed_result"]),
            "templates": list(templates or ["promo_story", "reels_hook"]),
            "edition": "beauty",
        }
