# Dashboard job widgets — data for operations dashboard.

from __future__ import annotations

from platform_jobs.job_engine import job_engine


async def build_running_jobs(_ctx=None) -> dict:
    widgets = await job_engine.dashboard_widgets()
    return widgets["running_jobs"]


async def build_failed_jobs(_ctx=None) -> dict:
    widgets = await job_engine.dashboard_widgets()
    return widgets["failed_jobs"]


async def build_job_queue_size(_ctx=None) -> dict:
    widgets = await job_engine.dashboard_widgets()
    return widgets["queue_size"]


async def build_worker_health(_ctx=None) -> dict:
    widgets = await job_engine.dashboard_widgets()
    return widgets["worker_health"]


async def build_job_execution_rate(_ctx=None) -> dict:
    widgets = await job_engine.dashboard_widgets()
    return widgets["execution_rate"]


async def build_job_retry_rate(_ctx=None) -> dict:
    widgets = await job_engine.dashboard_widgets()
    return widgets["retry_rate"]
