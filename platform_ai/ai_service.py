# AI Service — single entry point for all AI requests.

from __future__ import annotations

import logging
import time
from typing import Any

from platform_ai.ai_events import (
    AIFallbackUsedEvent,
    AIProviderFailedEvent,
    AIRequestCompletedEvent,
    AIRequestStartedEvent,
    CostThresholdExceededEvent,
    publish_ai_event,
)
from platform_ai.cache import ai_cache
from platform_ai.context_builder import context_builder
from platform_ai.conversation_manager import conversation_manager
from platform_ai.cost_tracker import cost_tracker
from platform_ai.model_registry import model_registry
from platform_ai.models import AIRequest, AIResponse, TaskType
from platform_ai.prompt_service import prompt_service
from platform_ai.provider_manager import provider_manager
from platform_ai.provider_router import provider_router
from platform_ai.token_manager import token_manager

logger = logging.getLogger(__name__)


class AIService:
    """All platform AI traffic must go through this service."""

    def __init__(self) -> None:
        self._request_count = 0
        self._initialized = False

    def reset(self) -> None:
        provider_manager.reset()
        prompt_service.reset()
        conversation_manager.reset()
        ai_cache.reset()
        cost_tracker.reset()
        self._request_count = 0
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        provider_manager.initialize()
        prompt_service.load_defaults()
        self._initialized = True
        logger.info("ai_service_initialized")

    async def complete(self, request: AIRequest) -> AIResponse:
        self.initialize()
        self._request_count += 1

        if request.template_id:
            rendered = prompt_service.render(request.template_id, request.template_vars)
            request.prompt = rendered

        context = await context_builder.build(request)
        messages = context_builder.build_messages(request, context)
        request.messages = messages

        prompt_key = request.prompt or (messages[-1].content if messages else "")
        decision = provider_router.route(request)

        await publish_ai_event(
            AIRequestStartedEvent(
                request_id=request.request_id,
                provider_id=decision.provider_id,
                model_id=decision.model_id,
                task_type=request.task_type.value,
                plugin_id=request.plugin_id,
            )
        )

        if request.use_cache:
            cached = ai_cache.get(decision.provider_id, decision.model_id, prompt_key, context)
            if cached:
                cached.request_id = request.request_id
                cost_tracker.record(cached, plugin_id=request.plugin_id)
                await publish_ai_event(
                    AIRequestCompletedEvent(
                        request_id=request.request_id,
                        provider_id=cached.provider_id,
                        model_id=cached.model_id,
                        tokens_in=cached.tokens_in,
                        tokens_out=cached.tokens_out,
                        cost_usd=cached.cost_usd,
                        cached=True,
                    )
                )
                return cached

        response = await self._execute_with_fallback(request, decision, prompt_key, context)

        if request.use_cache and not response.cached:
            ai_cache.set(decision.provider_id, decision.model_id, prompt_key, response, context)

        cost_tracker.record(response, plugin_id=request.plugin_id)

        if "conversation_id" in context:
            conversation_manager.add_message(context["conversation_id"], "user", prompt_key)
            conversation_manager.add_message(context["conversation_id"], "assistant", response.content)

        await publish_ai_event(
            AIRequestCompletedEvent(
                request_id=request.request_id,
                provider_id=response.provider_id,
                model_id=response.model_id,
                tokens_in=response.tokens_in,
                tokens_out=response.tokens_out,
                cost_usd=response.cost_usd,
                cached=response.cached,
                latency_ms=response.latency_ms,
            )
        )

        if cost_tracker.exceeds_threshold():
            await publish_ai_event(
                CostThresholdExceededEvent(
                    total_usd=cost_tracker._total_usd,
                    threshold_usd=cost_tracker.threshold_usd,
                    details=cost_tracker.summary(),
                )
            )

        return response

    async def _execute_with_fallback(
        self,
        request: AIRequest,
        decision: Any,
        prompt_key: str,
        context: dict[str, Any],
    ) -> AIResponse:
        candidates = [decision, *provider_router.fallback_candidates(decision.provider_id)]
        last_error = ""

        for candidate in candidates:
            try:
                return await self._call_provider(request, candidate, prompt_key)
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "ai_provider_failed provider=%s model=%s error=%s",
                    candidate.provider_id,
                    candidate.model_id,
                    exc,
                )
                await publish_ai_event(
                    AIProviderFailedEvent(
                        request_id=request.request_id,
                        provider_id=candidate.provider_id,
                        model_id=candidate.model_id,
                        error=last_error,
                    )
                )
                if candidate.fallback and candidate.provider_id != decision.provider_id:
                    await publish_ai_event(
                        AIFallbackUsedEvent(
                            request_id=request.request_id,
                            original_provider=decision.provider_id,
                            fallback_provider=candidate.provider_id,
                            reason=last_error,
                        )
                    )

        from platform_ai.exceptions import AIProviderUnavailableError

        raise AIProviderUnavailableError(f"All providers failed: {last_error}")

    async def _call_provider(self, request: AIRequest, decision: Any, prompt_key: str) -> AIResponse:
        provider = provider_manager.get_provider(decision.provider_id)
        start = time.monotonic()
        result = await provider._timed_complete(request, model_id=decision.model_id)
        latency_ms = (time.monotonic() - start) * 1000

        tokens_in = result.tokens_in or token_manager.estimate(prompt_key)
        tokens_out = result.tokens_out or token_manager.estimate(result.content)
        cost = cost_tracker.estimate_cost(decision.provider_id, decision.model_id, tokens_in, tokens_out)

        return AIResponse(
            request_id=request.request_id,
            provider_id=decision.provider_id,
            model_id=decision.model_id,
            content=result.content,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost,
            latency_ms=latency_ms,
            fallback_used=decision.fallback,
            metadata=result.metadata,
        )

    async def status(self) -> dict[str, Any]:
        self.initialize()
        providers = await provider_manager.health_all()
        return {
            "initialized": self._initialized,
            "request_count": self._request_count,
            "providers": [p.to_dict() for p in providers],
            "models": [m.to_dict() for m in model_registry.list_all()],
            "cache": ai_cache.stats(),
            "costs": cost_tracker.summary(),
        }


ai_service = AIService()
