# Model registry — provider models, pricing, capabilities.

from __future__ import annotations

from platform_ai.exceptions import AIModelNotFoundError
from platform_ai.models import AIModelRecord, ModelCapabilities, ModelPricing, ProviderStatus, TaskType


def _model(
    provider_id: str,
    model_id: str,
    display_name: str,
    *,
    context_window: int = 8192,
    input_price: float = 0.001,
    output_price: float = 0.002,
    task_types: list[str] | None = None,
    capabilities: ModelCapabilities | None = None,
) -> AIModelRecord:
    return AIModelRecord(
        provider_id=provider_id,
        model_id=model_id,
        display_name=display_name,
        context_window=context_window,
        pricing=ModelPricing(input_per_1k=input_price, output_per_1k=output_price),
        capabilities=capabilities or ModelCapabilities(),
        task_types=task_types or [TaskType.CHAT.value, TaskType.COMPLETION.value],
    )


BUILTIN_MODELS: list[AIModelRecord] = [
    _model("openai", "gpt-4o", "GPT-4o", context_window=128000, input_price=0.005, output_price=0.015),
    _model("openai", "gpt-4o-mini", "GPT-4o Mini", context_window=128000, input_price=0.00015, output_price=0.0006),
    _model("anthropic", "claude-3-5-sonnet", "Claude 3.5 Sonnet", context_window=200000, input_price=0.003, output_price=0.015),
    _model("anthropic", "claude-3-haiku", "Claude 3 Haiku", context_window=200000, input_price=0.00025, output_price=0.00125),
    _model("google", "gemini-1.5-pro", "Gemini 1.5 Pro", context_window=1000000, input_price=0.00125, output_price=0.005),
    _model("google", "gemini-1.5-flash", "Gemini 1.5 Flash", context_window=1000000, input_price=0.000075, output_price=0.0003),
    _model("openrouter", "openai/gpt-4o-mini", "OpenRouter GPT-4o Mini", context_window=128000, input_price=0.00015, output_price=0.0006),
    _model("local_llama", "llama-3.1-8b", "Local Llama 3.1 8B", context_window=8192, input_price=0.0, output_price=0.0),
    _model("deepseek", "deepseek-chat", "DeepSeek Chat", context_window=64000, input_price=0.00014, output_price=0.00028),
]


class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, AIModelRecord] = {}

    def register(self, model: AIModelRecord) -> None:
        key = f"{model.provider_id}:{model.model_id}"
        self._models[key] = model

    def get(self, provider_id: str, model_id: str) -> AIModelRecord:
        key = f"{provider_id}:{model_id}"
        if key not in self._models:
            raise AIModelNotFoundError(f"Model not found: {provider_id}/{model_id}")
        return self._models[key]

    def get_optional(self, provider_id: str, model_id: str) -> AIModelRecord | None:
        return self._models.get(f"{provider_id}:{model_id}")

    def list_all(self) -> list[AIModelRecord]:
        return list(self._models.values())

    def list_by_provider(self, provider_id: str) -> list[AIModelRecord]:
        return [m for m in self._models.values() if m.provider_id == provider_id]

    def list_by_task(self, task_type: str) -> list[AIModelRecord]:
        return [m for m in self._models.values() if task_type in m.task_types and m.status == ProviderStatus.AVAILABLE]

    def clear(self) -> None:
        self._models.clear()

    def load_defaults(self) -> int:
        for model in BUILTIN_MODELS:
            self.register(model)
        return len(BUILTIN_MODELS)


model_registry = ModelRegistry()
