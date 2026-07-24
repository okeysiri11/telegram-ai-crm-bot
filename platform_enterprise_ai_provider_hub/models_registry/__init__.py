"""Model Registry — Sprint 24.9."""

from __future__ import annotations

from typing import Any

from platform_enterprise_ai_provider_hub.models import MODEL_TYPES


class ModelRegistry:
    def register(
        self,
        *,
        model_id: str,
        provider_id: str,
        model_type: str = "chat",
        context_window: int = 8192,
        max_output: int = 2048,
        cost_per_1k: float = 0.0,
        speed_score: float = 0.5,
        quality_score: float = 0.5,
        capabilities: list[str] | None = None,
    ) -> dict[str, Any]:
        if not model_id or not provider_id:
            raise ValueError("model_id and provider_id are required")
        model_type = (model_type or "chat").lower()
        if model_type not in MODEL_TYPES:
            raise ValueError(f"unsupported model_type: {model_type}")
        return {
            "model_id": model_id,
            "provider_id": provider_id,
            "type": model_type,
            "context": int(context_window),
            "max_response_size": int(max_output),
            "cost": float(cost_per_1k),
            "speed": float(speed_score),
            "quality_rating": float(quality_score),
            "capabilities": list(capabilities or []),
        }
