"""HerculesRuntime — Universal + Session runtime façade."""

from __future__ import annotations

from typing import Any

from platform_hercules.cache.cache import hercules_cache
from platform_hercules.core.models import ExecutionContext, ExecutionPlan, HerculesJob
from platform_hercules.core.resources import resource_manager
from platform_hercules.cpu.pool import cpu_pool
from platform_hercules.gpu.pool import gpu_pool
from platform_hercules.metrics.metrics import hercules_metrics
from platform_hercules.orchestrator.orchestrator import hercules_orchestrator
from platform_hercules.queue.queue import hercules_queue
from platform_hercules.security.security import hercules_security
from platform_hercules.telemetry.telemetry import hercules_telemetry
from platform_hercules.workers.registry import worker_registry

VERSION = "1.0.0"

class SessionRuntime:
    """Per-owner session wrapper over Hercules."""

    def __init__(self, runtime: HerculesRuntime, session_id: str, owner_id: str) -> None:
        self.runtime = runtime
        self.session_id = session_id
        self.owner_id = owner_id

    def context(self, **kwargs: Any) -> ExecutionContext:
        return ExecutionContext(
            owner_id=self.owner_id,
            session_id=self.session_id,
            **kwargs,
        )

    async def run_ai(self, prompt: str, *, modality: str = "text", vertical: str | None = None) -> HerculesJob:
        return await self.runtime.submit_ai(
            self.context(channel="session"),
            prompt=prompt,
            modality=modality,
            vertical=vertical,
        )


class UniversalRuntime:
    """Alias surface — all domains call Hercules through this."""

    DOMAINS = (
        "crm",
        "erp",
        "ai_studio",
        "beauty",
        "auto",
        "crypto",
        "agro",
        "drone",
        "construction",
        "production",
        "knowledge",
        "marketplace",
        "telegram",
        "agents",
        "desktop",
    )


class HerculesRuntime:
    """Central execution engine of ADOS Enterprise."""

    VERSION = VERSION

    def __init__(self) -> None:
        self.orchestrator = hercules_orchestrator
        self.universal = UniversalRuntime()

    def session(self, session_id: str, owner_id: str) -> SessionRuntime:
        return SessionRuntime(self, session_id, owner_id)

    async def submit(self, plan: ExecutionPlan) -> HerculesJob:
        return await self.orchestrator.submit(plan)

    async def submit_ai(
        self,
        context: ExecutionContext,
        *,
        prompt: str,
        modality: str = "text",
        vertical: str | None = None,
    ) -> HerculesJob:
        return await self.orchestrator.submit_ai(
            context, prompt=prompt, modality=modality, vertical=vertical
        )

    def status(self, job_id: str) -> dict[str, Any] | None:
        job = self.orchestrator.get(job_id)
        if not job:
            return None
        return {
            "id": job.id,
            "lifecycle": job.state.lifecycle.value,
            "progress": job.state.progress,
            "error": job.state.error,
            "cost": job.state.cost,
            "worker_id": job.state.worker_id,
            "duration_sec": job.state.duration_sec(),
            "label": job.plan.label,
        }

    def cancel(self, job_id: str) -> dict[str, Any] | None:
        job = self.orchestrator.cancel(job_id)
        return self.status(job_id) if job else None

    async def retry(self, job_id: str) -> HerculesJob:
        return await self.orchestrator.retry(job_id)

    def dashboard(self) -> dict[str, Any]:
        return {
            "version": self.VERSION,
            "epic": "HERCULES_1.0",
            "health": hercules_telemetry.health(),
            "resources": resource_manager.dashboard(),
            "gpu": gpu_pool.snapshot(),
            "cpu": cpu_pool.snapshot(),
            "queues": hercules_queue.snapshot(),
            "workers": worker_registry.as_dicts(),
            "metrics": hercules_metrics.dashboard(),
            "cache": hercules_cache.stats(),
            "domains": list(UniversalRuntime.DOMAINS),
            "jobs": [
                {
                    "id": j.id,
                    "status": j.state.lifecycle.value,
                    "label": j.plan.label,
                    "line": j.status_line_ru(),
                }
                for j in self.orchestrator.list_jobs(limit=20)
            ],
            "audit_tail": hercules_security.audit_tail(10),
        }

    def telegram_overview_ru(self) -> str:
        d = self.dashboard()
        m = d["metrics"]
        g = d["gpu"]
        c = d["cpu"]
        return (
            "🟢 Hercules Runtime\n\n"
            f"Версия: {d['version']}\n"
            f"Выполняется: {m['running']}\n"
            f"Готово: {m['finished']} · Ошибки: {m['failed']}\n"
            f"Jobs/sec: {m['jobs_per_sec']}\n"
            f"CPU: {c['cores']} ядер · нагрузка ~{c['load_est']}%\n"
            f"GPU: {g['backend']} · слоты {g['used']}/{g['slots']}\n"
            f"VRAM ~{g['vram_mb_est']} МБ\n"
            f"Домены: {len(d['domains'])}"
        )


hercules_runtime = HerculesRuntime()
