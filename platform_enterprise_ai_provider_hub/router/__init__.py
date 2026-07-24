"""Intelligent Model Router — Sprint 24.9."""

from __future__ import annotations

from typing import Any

from platform_enterprise_ai_provider_hub.models import ROUTE_CRITERIA, TASK_TYPES


class IntelligentModelRouter:
    def route(
        self,
        *,
        task_type: str,
        models: list[dict[str, Any]],
        prefer_cost: bool = False,
        prefer_speed: bool = False,
        prefer_quality: bool = True,
        require_local: bool = False,
        security_tier: str = "standard",
    ) -> dict[str, Any]:
        task_type = (task_type or "general_chat").lower()
        if task_type not in TASK_TYPES:
            raise ValueError(f"unsupported task_type: {task_type}")
        candidates = list(models or [])
        if require_local or security_tier == "strict_local":
            candidates = [m for m in candidates if str(m.get("provider_id", "")).startswith(("local", "ollama", "vllm", "lm_studio", "corp"))]
        if not candidates:
            raise ValueError("no eligible models for routing policy")

        def score(m: dict[str, Any]) -> float:
            quality = float(m.get("quality_rating", 0.5))
            speed = float(m.get("speed", 0.5))
            cost = float(m.get("cost", 0.0))
            # lower cost is better → invert relative to max 1.0 clamp
            cost_score = max(0.0, 1.0 - min(cost, 1.0))
            w_q, w_s, w_c = 0.45, 0.25, 0.3
            if prefer_quality:
                w_q = 0.55
            if prefer_speed:
                w_s = 0.45
                w_q = 0.3
            if prefer_cost:
                w_c = 0.5
                w_q = 0.25
            return quality * w_q + speed * w_s + cost_score * w_c

        ranked = sorted(candidates, key=score, reverse=True)
        chosen = ranked[0]
        return {
            "task_type": task_type,
            "selected_model": chosen.get("model_id"),
            "selected_provider": chosen.get("provider_id"),
            "criteria": list(ROUTE_CRITERIA),
            "ranked": [m.get("model_id") for m in ranked[:5]],
            "via_hub_only": True,
            "direct_provider_call": False,
        }
