# AI request router — task type, cost, latency, availability, fallback.

from __future__ import annotations

import logging
from dataclasses import dataclass

from platform_ai.exceptions import AIRoutingError, AIProviderUnavailableError
from platform_ai.model_registry import model_registry
from platform_ai.models import AIRequest, ProviderStatus, TaskType
from platform_ai.provider_manager import provider_manager

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    provider_id: str
    model_id: str
    reason: str
    fallback: bool = False


class ProviderRouter:
    """Select optimal provider/model for each AI request."""

    TASK_PREFERENCES: dict[str, list[str]] = {
        TaskType.CHAT.value: ["openrouter", "openai", "anthropic"],
        TaskType.CODE.value: ["openai", "deepseek", "anthropic"],
        TaskType.SUMMARIZATION.value: ["google", "anthropic", "openai"],
        TaskType.CLASSIFICATION.value: ["openai", "anthropic", "deepseek"],
        TaskType.EMBEDDING.value: ["openai", "local_llama"],
    }

    def route(self, request: AIRequest) -> RoutingDecision:
        if request.provider and request.model:
            if not provider_manager.is_enabled(request.provider):
                raise AIProviderUnavailableError(request.provider)
            return RoutingDecision(request.provider, request.model, "explicit")

        if request.provider:
            model = request.model or self._default_model(request.provider)
            return RoutingDecision(request.provider, model, "provider_specified")

        if request.model:
            for model_rec in model_registry.list_all():
                if model_rec.model_id == request.model and provider_manager.is_enabled(model_rec.provider_id):
                    return RoutingDecision(model_rec.provider_id, model_rec.model_id, "model_specified")

        return self._auto_route(request)

    def _auto_route(self, request: AIRequest) -> RoutingDecision:
        task = request.task_type.value if isinstance(request.task_type, TaskType) else str(request.task_type)
        preferred = self.TASK_PREFERENCES.get(task, provider_manager.fallback_chain)

        candidates = model_registry.list_by_task(task)
        if not candidates:
            candidates = model_registry.list_all()

        scored: list[tuple[float, str, str]] = []
        for model in candidates:
            if not provider_manager.is_enabled(model.provider_id):
                continue
            provider = provider_manager.get_provider(model.provider_id)
            if provider.average_latency_ms == 0:
                latency_score = 1.0
            else:
                latency_score = 1.0 / (1.0 + provider.average_latency_ms / 1000)
            cost_score = 1.0 / (1.0 + model.pricing.input_per_1k + model.pricing.output_per_1k)
            pref_bonus = 2.0 if model.provider_id in preferred else 0.0
            pref_index = preferred.index(model.provider_id) if model.provider_id in preferred else 99
            score = latency_score + cost_score + pref_bonus - pref_index * 0.1
            scored.append((score, model.provider_id, model.model_id))

        if not scored:
            raise AIRoutingError(f"No available provider for task {task}")

        scored.sort(reverse=True)
        _, provider_id, model_id = scored[0]
        return RoutingDecision(provider_id, model_id, f"auto_route:{task}")

    def fallback_candidates(self, exclude: str) -> list[RoutingDecision]:
        decisions: list[RoutingDecision] = []
        for provider_id in provider_manager.fallback_chain:
            if provider_id == exclude or not provider_manager.is_enabled(provider_id):
                continue
            model_id = self._default_model(provider_id)
            if model_registry.get_optional(provider_id, model_id):
                decisions.append(RoutingDecision(provider_id, model_id, "fallback", fallback=True))
        return decisions

    def _default_model(self, provider_id: str) -> str:
        models = model_registry.list_by_provider(provider_id)
        if not models:
            raise AIRoutingError(f"No models for provider {provider_id}")
        config = provider_manager.get_provider(provider_id).config
        default = config.get("default_model")
        if default:
            for m in models:
                if m.model_id == default:
                    return default
        return models[0].model_id


provider_router = ProviderRouter()
