"""Sprint 43.2 — Multimodal generation chain."""

from __future__ import annotations

from typing import Any

from platform_ai.pipeline_models import AiTaskRequest
from platform_ai.providers.manager import ProviderManager, provider_manager


MULTIMODAL_STEPS = (
    "prompt",
    "llm",
    "image",
    "video",
    "voice",
    "music",
    "subtitle",
    "publishing",
)


class MultimodalPipeline:
    """Prompt → LLM → Image → Video → Voice → Music → Subtitle → Publishing."""

    VERSION = "43.2"

    def __init__(self, providers: ProviderManager | None = None) -> None:
        self.providers = providers or provider_manager

    async def run(
        self,
        idea: str,
        *,
        owner_id: str = "system",
        steps: list[str] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        chain = steps or list(MULTIMODAL_STEPS)
        meta = dict(meta or {})
        artifacts: dict[str, Any] = {}
        costs: dict[str, float] = {}
        current_prompt = idea

        for step in chain:
            if step == "prompt":
                artifacts["prompt"] = current_prompt
                continue
            if step == "llm":
                res = await self.providers.generate("text", current_prompt, meta=meta)
                artifacts["llm"] = res.to_dict()
                current_prompt = res.content
                costs["llm"] = res.cost.total
            elif step == "image":
                res = await self.providers.generate("image", current_prompt, meta=meta)
                artifacts["image"] = res.to_dict()
                costs["image"] = res.cost.total
            elif step == "video":
                res = await self.providers.generate("video", current_prompt, meta=meta)
                artifacts["video"] = res.to_dict()
                costs["video"] = res.cost.total
            elif step == "voice":
                res = await self.providers.generate("voice", current_prompt, meta=meta)
                artifacts["voice"] = res.to_dict()
                costs["voice"] = res.cost.total
            elif step == "music":
                res = await self.providers.generate("music", f"музыка для: {idea}", meta=meta)
                artifacts["music"] = res.to_dict()
                costs["music"] = res.cost.total
            elif step == "subtitle":
                res = await self.providers.generate(
                    "text",
                    f"Сделай субтитры на русском для ролика по теме: {idea}",
                    meta=meta,
                )
                artifacts["subtitle"] = res.to_dict()
                costs["subtitle"] = res.cost.total
            elif step == "publishing":
                artifacts["publishing"] = {
                    "status": "prepared",
                    "message": "Публикация подготовлена через Provider Layer",
                    "channels": ["instagram", "tiktok", "telegram", "youtube"],
                }

        return {
            "owner_id": owner_id,
            "idea": idea,
            "steps": chain,
            "artifacts": artifacts,
            "costs": costs,
            "total_cost": round(sum(costs.values()), 4),
            "version": self.VERSION,
        }


multimodal_pipeline = MultimodalPipeline()
