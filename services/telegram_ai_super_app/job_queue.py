"""Legacy UX job queue — Sprint 43.1 prefers platform_ai.UnifiedAiPipeline.

Kept as a thin compatibility shim for older imports/tests.
"""

from __future__ import annotations

from platform_ai.pipeline import unified_ai_pipeline
from platform_ai.pipeline_models import AiTaskRecord

# Back-compat alias
GenerationJob = AiTaskRecord


class JobQueue:
    """Deprecated shim — delegates list/favorites to UnifiedAiPipeline."""

    def create(self, user_key: str, modality: str, prompt: str) -> AiTaskRecord:
        from platform_ai.pipeline_models import AiTaskRequest

        # Synchronous placeholder record only — prefer pipeline.run()
        from platform_ai.pipeline_models import AiTaskRecord as Rec

        rec = Rec.new(
            AiTaskRequest(owner_id=user_key, modality=modality, prompt=prompt),
            optimized_prompt=prompt,
        )
        unified_ai_pipeline._store(rec)
        return rec

    def get(self, job_id: str) -> AiTaskRecord | None:
        return unified_ai_pipeline.get(job_id)

    def list_for_user(self, user_key: str, *, limit: int = 15) -> list[AiTaskRecord]:
        return unified_ai_pipeline.list_for_owner(user_key, limit=limit)

    def favorites(self, user_key: str) -> list[AiTaskRecord]:
        return unified_ai_pipeline.favorites(user_key)

    def toggle_favorite(self, job_id: str) -> AiTaskRecord | None:
        return unified_ai_pipeline.toggle_favorite(job_id)

    def mark_running(self, job_id: str, *, provider_id: str | None = None) -> AiTaskRecord | None:
        job = self.get(job_id)
        if not job:
            return None
        job.status = "генерируется"
        if provider_id:
            job.provider_id = provider_id
        return job

    def mark_progress(self, job_id: str, progress: int) -> None:
        job = self.get(job_id)
        if job:
            job.progress = progress

    def mark_done(self, job_id: str, result: dict) -> AiTaskRecord | None:
        job = self.get(job_id)
        if not job:
            return None
        job.status = "готово"
        job.progress = 100
        job.result = result
        return job

    def mark_error(self, job_id: str, error: str) -> AiTaskRecord | None:
        job = self.get(job_id)
        if not job:
            return None
        job.status = "ошибка"
        job.error = error
        return job


job_queue = JobQueue()
