"""Sprint 43.1 — Unified AI Runtime Pipeline.

Single entry for Telegram / Web / Desktop / Mobile / REST / Automation / Workflow.
Never call vendor SDKs from channels — only Provider Layer (Creative Factory media).
"""

from __future__ import annotations

import logging
import time
from threading import Lock
from typing import Any, Callable, Awaitable

from platform_ai.creative_engine import CreativeFactoryEngine, creative_factory_engine
from platform_ai.pipeline_analytics import AiPipelineAnalytics, ai_pipeline_analytics
from platform_ai.pipeline_cache import AiResultCache, ai_result_cache
from platform_ai.pipeline_models import (
    AiTaskRecord,
    AiTaskRequest,
    AiTaskStatus,
    POST_GEN_WORKFLOW_RU,
)
from platform_ai.prompt_engine import PromptEngine, prompt_engine
from platform_ai.providers.manager import ProviderManager, provider_manager
from platform_jobs import QueueLane, unified_queue

logger = logging.getLogger(__name__)

NotifyFn = Callable[[AiTaskRecord], Awaitable[None] | None]

# Kept for compatibility — ProviderManager is source of truth (Sprint 43.2).
PROVIDER_CATALOG: dict[str, tuple[str, ...]] = {
    "image": (
        "openai_image",
        "flux_image",
        "recraft_image",
        "ideogram_image",
        "bfl_image",
        "stability_image",
        "fal_image",
        "replicate_image",
        "local_image",
    ),
    "video": (
        "runway_video",
        "google_veo",
        "pika_video",
        "kling_video",
        "luma_video",
        "hailuo_video",
        "local_video",
    ),
    "voice": (
        "elevenlabs_voice",
        "cartesia_voice",
        "google_tts",
        "azure_speech",
        "openai_voice",
        "local_voice",
    ),
    "text": (
        "openai_text",
        "anthropic_text",
        "gemini_text",
        "deepseek_text",
        "mistral_text",
        "local_text",
    ),
    "music": ("local_music",),
    "document": ("openai_text", "anthropic_text", "local_text"),
    "presentation": ("openai_text", "anthropic_text", "local_text"),
    "ads": ("openai_text", "anthropic_text", "local_text"),
    "prompt": ("openai_text", "anthropic_text", "local_text"),
}

COST_TABLE: dict[str, float] = {
    "image": 0.08,
    "video": 0.35,
    "voice": 0.05,
    "music": 0.05,
    "text": 0.02,
    "document": 0.03,
    "presentation": 0.04,
    "ads": 0.03,
    "prompt": 0.01,
}


def _ensure_providers(media: Any) -> None:
    """Register Sprint 43.1 provider ids on MediaProviderManager."""
    extras = [
        ("google_imagen", "image"),
        ("flux_image", "image"),
        ("recraft_image", "image"),
        ("ideogram_image", "image"),
        ("bfl_image", "image"),
        ("google_veo", "video"),
        ("pika_video", "video"),
        ("luma_video", "video"),
        ("kling_video", "video"),
        ("hailuo_video", "video"),
        ("cartesia_voice", "voice"),
        ("azure_speech", "voice"),
        ("google_tts", "voice"),
        ("gemini_text", "text"),
        ("openrouter_text", "text"),
        ("anthropic_text", "text"),
    ]
    for pid, modality in extras:
        if pid not in media.providers:
            media.providers[pid] = {
                "provider_id": pid,
                "modality": modality,
                "available": True,
                "label": pid.replace("_", " ").title(),
            }
    for modality, order in PROVIDER_CATALOG.items():
        media_key = modality if modality in ("image", "video", "voice", "text") else "text"
        media.fallback[media_key] = list(PROVIDER_CATALOG.get(media_key, order))


class UnifiedAiPipeline:
    """
    Create → Validate → Choose Provider → Reserve Credits → Queue →
    Execute → Progress → Store → History → Notify → Cache → Analytics
    """

    VERSION = "43.2"
    PIPELINE_STEPS = (
        "create",
        "validate",
        "choose_provider",
        "reserve_credits",
        "queue",
        "execute",
        "progress",
        "store_result",
        "history",
        "notify",
        "cache",
        "analytics",
    )

    def __init__(
        self,
        *,
        factory: CreativeFactoryEngine | None = None,
        prompts: PromptEngine | None = None,
        cache: AiResultCache | None = None,
        analytics: AiPipelineAnalytics | None = None,
        providers: ProviderManager | None = None,
    ) -> None:
        self.factory = factory or creative_factory_engine
        self.prompts = prompts or prompt_engine
        self.cache = cache or ai_result_cache
        self.analytics = analytics or ai_pipeline_analytics
        self.providers = providers or provider_manager
        self._lock = Lock()
        self._tasks: dict[str, AiTaskRecord] = {}
        self._by_owner: dict[str, list[str]] = {}
        self._credits: dict[str, float] = {}
        self._notifiers: list[NotifyFn] = []
        _ensure_providers(self.factory.media)

    def reset(self) -> None:
        with self._lock:
            self._tasks.clear()
            self._by_owner.clear()
            self._credits.clear()
        self.cache.reset()
        self.analytics.reset()

    def register_notifier(self, fn: NotifyFn) -> None:
        self._notifiers.append(fn)

    def get(self, task_id: str) -> AiTaskRecord | None:
        with self._lock:
            return self._tasks.get(task_id)

    def list_for_owner(self, owner_id: str, *, limit: int = 30) -> list[AiTaskRecord]:
        with self._lock:
            ids = self._by_owner.get(owner_id, [])[:limit]
            return [self._tasks[i] for i in ids if i in self._tasks]

    def favorites(self, owner_id: str) -> list[AiTaskRecord]:
        return [t for t in self.list_for_owner(owner_id, limit=100) if t.favorite]

    def search(self, owner_id: str, query: str) -> list[AiTaskRecord]:
        q = (query or "").lower().strip()
        if not q:
            return self.list_for_owner(owner_id)
        return [
            t
            for t in self.list_for_owner(owner_id, limit=100)
            if q in t.prompt.lower() or q in t.modality or q in (t.provider_id or "")
        ]

    def filter_by(
        self,
        owner_id: str,
        *,
        modality: str | None = None,
        status: str | None = None,
    ) -> list[AiTaskRecord]:
        rows = self.list_for_owner(owner_id, limit=100)
        if modality:
            rows = [t for t in rows if t.modality == modality]
        if status:
            rows = [t for t in rows if t.status == status]
        return rows

    def toggle_favorite(self, task_id: str) -> AiTaskRecord | None:
        with self._lock:
            t = self._tasks.get(task_id)
            if not t:
                return None
            t.favorite = not t.favorite
            t.append_history("favorite", value=t.favorite)
            return t

    def delete(self, task_id: str, owner_id: str) -> bool:
        with self._lock:
            t = self._tasks.get(task_id)
            if not t or t.owner_id != owner_id:
                return False
            self._tasks.pop(task_id, None)
            ids = self._by_owner.get(owner_id, [])
            self._by_owner[owner_id] = [i for i in ids if i != task_id]
            return True

    def provider_catalog(self, modality: str | None = None) -> dict[str, list[str]]:
        if modality:
            return {modality: list(PROVIDER_CATALOG.get(modality, ()))}
        return {k: list(v) for k, v in PROVIDER_CATALOG.items()}

    def post_gen_workflow(self) -> list[dict[str, str]]:
        return [{"id": a, "label": l} for a, l in POST_GEN_WORKFLOW_RU]

    def owner_dashboard(self, owner_id: str) -> dict[str, Any]:
        tasks = self.list_for_owner(owner_id, limit=50)
        active = [
            t
            for t in tasks
            if t.status
            in (
                AiTaskStatus.QUEUED.value,
                AiTaskStatus.PREPARING.value,
                AiTaskStatus.GENERATING.value,
                AiTaskStatus.PROCESSING.value,
                AiTaskStatus.RETRY.value,
            )
        ]
        errors = [t for t in tasks if t.status == AiTaskStatus.ERROR.value]
        snap = self.analytics.snapshot()
        return {
            "active_tasks": [t.to_dict() for t in active[:10]],
            "queue_depth": len(active),
            "ai_usage": snap,
            "cost_total": round(sum(t.cost_estimate for t in tasks), 4),
            "top_models": snap.get("popular_models", {}),
            "recent": [t.to_dict() for t in tasks[:8]],
            "errors": [t.to_dict() for t in errors[:5]],
            "credits_reserved": self._credits.get(owner_id, 0.0),
            "pipeline_version": self.VERSION,
        }

    def _validate(self, req: AiTaskRequest) -> None:
        if not req.owner_id:
            raise ValueError("Не указан владелец задачи")
        if not (req.prompt or "").strip():
            raise ValueError("Пустой запрос генерации")
        if req.modality not in PROVIDER_CATALOG and req.modality not in (
            "image",
            "video",
            "voice",
            "text",
        ):
            # allow known modalities only
            if req.modality not in COST_TABLE:
                raise ValueError(f"Неподдерживаемая модальность: {req.modality}")

    def _choose_provider(self, req: AiTaskRequest) -> str:
        order = self.providers.order_for(req.modality if req.modality in (
            "image", "video", "voice", "text", "music"
        ) else "text", req.preferred_provider)
        if order:
            return order[0]
        catalog = PROVIDER_CATALOG.get(req.modality) or PROVIDER_CATALOG["text"]
        return catalog[0]

    def _reserve_credits(self, owner_id: str, amount: float) -> float:
        with self._lock:
            self._credits[owner_id] = self._credits.get(owner_id, 0.0) + amount
            return self._credits[owner_id]

    def _store(self, task: AiTaskRecord) -> None:
        with self._lock:
            self._tasks[task.id] = task
            self._by_owner.setdefault(task.owner_id, []).insert(0, task.id)
            self._by_owner[task.owner_id] = self._by_owner[task.owner_id][:200]

    async def _notify(self, task: AiTaskRecord) -> None:
        for fn in self._notifiers:
            try:
                res = fn(task)
                if hasattr(res, "__await__"):
                    await res  # type: ignore[misc]
            except Exception as exc:  # noqa: BLE001
                logger.warning("pipeline_notify_failed: %s", exc)

    async def run(self, req: AiTaskRequest) -> AiTaskRecord:
        """Full synchronous-style pipeline execution (still async I/O)."""
        # 1 create + optimize prompt
        if req.optimize_prompt:
            opt = self.prompts.optimize(
                req.prompt,
                domain=req.vertical or req.studio_id,
                modality=req.modality,
                meta=req.meta,
            )
            optimized = opt["optimized_prompt"]
        else:
            optimized = req.prompt

        task = AiTaskRecord.new(req, optimized_prompt=optimized)
        task.append_history("create")
        self._store(task)

        try:
            # 2 validate
            self._validate(req)
            task.status = AiTaskStatus.PREPARING.value
            task.progress = 5
            task.append_history("validate")

            # 3 choose provider
            provider = self._choose_provider(req)
            task.provider_id = provider
            task.append_history("choose_provider", provider=provider)
            task.progress = 10

            # 4 reserve credits
            cost = COST_TABLE.get(req.modality, 0.05)
            task.cost_estimate = cost
            task.credits_reserved = cost
            self._reserve_credits(req.owner_id, cost)
            task.append_history("reserve_credits", amount=cost)
            task.progress = 15

            # cache check before queue
            cache_key = self.cache.key(req.owner_id, req.modality, optimized, provider)
            cached = self.cache.get(cache_key)
            if cached:
                task.cache_hit = True
                task.status = AiTaskStatus.DONE.value
                task.progress = 100
                task.result = cached
                task.started_at = time.time()
                task.finished_at = time.time()
                task.append_history("cache_hit")
                self.analytics.record(task)
                await self._notify(task)
                return task

            # 5 queue (platform_jobs UnifiedQueueArchitecture)
            task.status = AiTaskStatus.QUEUED.value
            task.append_history("queue")
            lane = QueueLane.RENDER if req.modality in ("image", "video", "voice") else QueueLane.AI
            platform_job = await unified_queue.enqueue(
                lane=lane,
                handler_name="unified_ai_pipeline.execute",
                payload={"task_id": task.id, "modality": req.modality},
            )
            task.platform_job_id = platform_job.job_id
            task.progress = 25

            # 6–7 execute + progress via Provider Manager (Sprint 43.2)
            task.status = AiTaskStatus.GENERATING.value
            task.started_at = time.time()
            task.progress = 40
            task.append_history("execute_start")

            media_mod = req.modality if req.modality in ("image", "video", "voice", "text", "music") else "text"
            provider_result = await self.providers.generate(
                media_mod,
                optimized,
                preferred=provider,
                meta=req.meta,
            )
            result = provider_result.to_dict()
            task.progress = 75
            task.status = AiTaskStatus.PROCESSING.value
            task.append_history("progress", progress=75, mode=provider_result.mode)

            # 8 store result + cost breakdown
            task.result = {
                **result,
                "pipeline_version": self.VERSION,
                "optimized_prompt": optimized,
                "cost_breakdown": provider_result.cost.to_dict(),
            }
            task.provider_id = result.get("provider_id") or provider
            task.cost_estimate = float(provider_result.cost.total or task.cost_estimate)
            task.status = AiTaskStatus.DONE.value
            task.progress = 100
            task.finished_at = time.time()
            task.append_history("store_result", mode=provider_result.mode)

            await unified_queue.complete(platform_job, result=task.result)

            # 9 history already on task
            # 10 notify
            await self._notify(task)
            task.append_history("notify")

            # 11 cache
            self.cache.set(cache_key, task.result)
            task.append_history("cache")

            # 12 analytics
            self.analytics.record(task)
            task.append_history("analytics")
            self._store(task)
            return task

        except Exception as exc:  # noqa: BLE001
            task.status = AiTaskStatus.ERROR.value
            task.error = str(exc)
            task.finished_at = time.time()
            task.append_history("error", message=str(exc))
            self.analytics.record(task)
            self._store(task)
            await self._notify(task)
            logger.exception("unified_ai_pipeline_failed task=%s", task.id)
            return task

    async def retry(self, task_id: str) -> AiTaskRecord:
        prev = self.get(task_id)
        if not prev:
            raise ValueError("Задача не найдена")
        req = AiTaskRequest(
            owner_id=prev.owner_id,
            modality=prev.modality,
            prompt=prev.prompt,
            channel=prev.channel,
            tenant_id=prev.tenant_id,
            preferred_provider=prev.provider_id,
            meta=prev.meta,
            studio_id=prev.studio_id,
            vertical=prev.vertical,
            optimize_prompt=True,
        )
        # bypass cache for explicit retry? keep cache for identical — user asked retry
        # Force fresh by slightly tagging meta
        req.meta = {**req.meta, "_retry_of": task_id, "_nonce": time.time()}
        req.optimize_prompt = True
        # Clear cache key by changing optimized path — use optimize_prompt False with nonce in prompt
        fresh = AiTaskRequest(
            owner_id=req.owner_id,
            modality=req.modality,
            prompt=f"{req.prompt}\n[повтор:{task_id[:8]}]",
            channel=req.channel,
            tenant_id=req.tenant_id,
            preferred_provider=req.preferred_provider,
            meta=req.meta,
            studio_id=req.studio_id,
            vertical=req.vertical,
        )
        task = await self.run(fresh)
        task.status = AiTaskStatus.RETRY.value if task.status == AiTaskStatus.DONE.value else task.status
        if task.status == AiTaskStatus.RETRY.value:
            task.status = AiTaskStatus.DONE.value
            task.append_history("retry", of=task_id)
        return task

    def duplicate(self, task_id: str) -> AiTaskRecord:
        prev = self.get(task_id)
        if not prev:
            raise ValueError("Задача не найдена")
        clone = AiTaskRecord.new(
            AiTaskRequest(
                owner_id=prev.owner_id,
                modality=prev.modality,
                prompt=prev.prompt,
                channel=prev.channel,
                tenant_id=prev.tenant_id,
                meta=prev.meta,
                studio_id=prev.studio_id,
                vertical=prev.vertical,
            ),
            optimized_prompt=prev.optimized_prompt,
        )
        clone.status = AiTaskStatus.CREATED.value
        clone.append_history("duplicate", of=task_id)
        self._store(clone)
        return clone


unified_ai_pipeline = UnifiedAiPipeline()
