# Cost tracking — tokens and estimated cost per provider/model/plugin.

from __future__ import annotations

from collections import defaultdict
from typing import Any

from platform_ai.model_registry import model_registry
from platform_ai.models import AIResponse, CostRecord


class CostTracker:
    def __init__(self, *, threshold_usd: float = 100.0) -> None:
        self._records: list[CostRecord] = []
        self.threshold_usd = threshold_usd
        self._total_usd = 0.0

    def reset(self) -> None:
        self._records.clear()
        self._total_usd = 0.0

    def estimate_cost(self, provider_id: str, model_id: str, tokens_in: int, tokens_out: int) -> float:
        model = model_registry.get_optional(provider_id, model_id)
        if not model:
            return 0.0
        return (tokens_in / 1000 * model.pricing.input_per_1k) + (tokens_out / 1000 * model.pricing.output_per_1k)

    def record(self, response: AIResponse, plugin_id: str | None = None) -> CostRecord:
        cost = response.cost_usd or self.estimate_cost(
            response.provider_id, response.model_id, response.tokens_in, response.tokens_out
        )
        record = CostRecord(
            request_id=response.request_id,
            provider_id=response.provider_id,
            model_id=response.model_id,
            plugin_id=plugin_id,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cost_usd=cost,
        )
        self._records.append(record)
        self._total_usd += cost
        response.cost_usd = cost
        return record

    def exceeds_threshold(self) -> bool:
        return self._total_usd >= self.threshold_usd

    def summary(self) -> dict[str, Any]:
        by_provider: dict[str, float] = defaultdict(float)
        by_model: dict[str, float] = defaultdict(float)
        by_plugin: dict[str, float] = defaultdict(float)
        tokens_in = tokens_out = 0

        for rec in self._records:
            by_provider[rec.provider_id] += rec.cost_usd
            by_model[f"{rec.provider_id}:{rec.model_id}"] += rec.cost_usd
            key = rec.plugin_id or "platform"
            by_plugin[key] += rec.cost_usd
            tokens_in += rec.tokens_in
            tokens_out += rec.tokens_out

        return {
            "total_usd": round(self._total_usd, 6),
            "threshold_usd": self.threshold_usd,
            "threshold_exceeded": self.exceeds_threshold(),
            "request_count": len(self._records),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "by_provider": dict(by_provider),
            "by_model": dict(by_model),
            "by_plugin": dict(by_plugin),
        }

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return [
            {
                "request_id": r.request_id,
                "provider_id": r.provider_id,
                "model_id": r.model_id,
                "plugin_id": r.plugin_id,
                "tokens_in": r.tokens_in,
                "tokens_out": r.tokens_out,
                "cost_usd": r.cost_usd,
                "timestamp": r.timestamp,
            }
            for r in self._records[-limit:]
        ]


cost_tracker = CostTracker()
