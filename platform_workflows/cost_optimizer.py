"""Epic 45.3 — Cost Optimizer (pick best AI for step)."""
from __future__ import annotations
from typing import Any

# model catalog: cost units, speed (higher faster), quality
MODELS = [
    {"id": "fast-lite", "cost": 0.01, "speed": 10, "quality": 5, "kinds": {"text", "copy", "offer"}},
    {"id": "balanced", "cost": 0.05, "speed": 7, "quality": 8, "kinds": {"text", "image", "plan", "document"}},
    {"id": "premium", "cost": 0.2, "speed": 4, "quality": 10, "kinds": {"video", "image", "voice", "presentation"}},
    {"id": "voice-std", "cost": 0.03, "speed": 8, "quality": 7, "kinds": {"voice", "tts"}},
    {"id": "vision-std", "cost": 0.08, "speed": 6, "quality": 8, "kinds": {"image", "banner", "reels"}},
]

class CostOptimizer:
    def choose(self, *, kind: str, priority: str = "balanced", budget: float | None = None) -> dict[str, Any]:
        kind = (kind or "text").lower()
        candidates = [m for m in MODELS if kind in m["kinds"] or "text" in m["kinds"]]
        if not candidates:
            candidates = MODELS
        if priority == "cheap" or priority == "cost":
            candidates = sorted(candidates, key=lambda m: m["cost"])
        elif priority == "fast" or priority == "speed":
            candidates = sorted(candidates, key=lambda m: -m["speed"])
        elif priority == "quality":
            candidates = sorted(candidates, key=lambda m: -m["quality"])
        else:
            candidates = sorted(candidates, key=lambda m: (m["cost"] / max(m["quality"], 1)) )
        if budget is not None:
            affordable = [m for m in candidates if m["cost"] <= budget]
            if affordable:
                candidates = affordable
        pick = candidates[0]
        return {"model": pick["id"], "cost": pick["cost"], "reason": f"priority={priority}", "kind": kind}

cost_optimizer = CostOptimizer()
