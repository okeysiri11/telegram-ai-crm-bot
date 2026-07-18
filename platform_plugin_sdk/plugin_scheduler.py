# Plugin scheduler — jobs only through Job Engine with namespaced handlers.

from __future__ import annotations

from typing import Any, Callable

from platform_plugin_sdk.plugin_api import JobsApi


class PluginScheduler:
    """Schedules plugin jobs with automatic handler namespacing."""

    def __init__(self, plugin_id: str, jobs: JobsApi) -> None:
        self.plugin_id = plugin_id
        self._jobs = jobs
        self._registered: set[str] = set()

    def _namespaced(self, handler_name: str) -> str:
        prefix = f"plugin.{self.plugin_id}."
        if handler_name.startswith(prefix):
            return handler_name
        return f"{prefix}{handler_name}"

    def register(self, handler_name: str, handler: Callable[..., Any]) -> str:
        full_name = self._namespaced(handler_name)
        self._jobs.register_handler(full_name, handler)
        self._registered.add(full_name)
        return full_name

    async def enqueue(self, handler_name: str, payload: dict[str, Any], **options: Any) -> dict[str, Any]:
        full_name = self._namespaced(handler_name)
        enriched = {"plugin_id": self.plugin_id, **payload}
        return await self._jobs.enqueue(full_name, enriched, **options)

    async def schedule_cron(
        self,
        handler_name: str,
        payload: dict[str, Any],
        cron_expression: str,
        **options: Any,
    ) -> dict[str, Any]:
        from platform_jobs.models import JobType

        return await self.enqueue(
            handler_name,
            payload,
            job_type=JobType.CRON,
            cron_expression=cron_expression,
            **options,
        )

    @property
    def handlers(self) -> set[str]:
        return set(self._registered)
