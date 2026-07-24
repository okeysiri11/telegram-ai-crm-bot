"""Creative Studio — Sprint 22.5."""

from __future__ import annotations

from typing import Any

from platform_ai_marketing_os.models import CREATIVE_KINDS


class CreativeStudio:
    def generate(self, *, kind: str, prompt: str, brand: dict[str, Any] | None = None) -> dict[str, Any]:
        if kind not in CREATIVE_KINDS:
            raise ValueError(f"unknown creative kind: {kind}")
        if not prompt:
            raise ValueError("prompt is required")
        brand = brand or {}
        return {
            "kind": kind,
            "prompt": prompt,
            "artifact": f"{kind}://generated/{abs(hash(prompt)) % 10_000_000}",
            "provider_architecture": "enterprise_ai_provider",
            "brand_colors": brand.get("colors", []),
            "tone": brand.get("tone_of_voice"),
            "published": False,
            "requires_approval": True,
        }
