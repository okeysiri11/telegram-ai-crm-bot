# Dashboard widget registry — ids, TTLs, and refresh intervals.

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WidgetId = Literal[
    "system_status",
    "active_requests",
    "requests_by_vertical",
    "manager_load",
    "sla_status",
    "workflow_status",
    "recent_events",
    "recent_audit",
    "configuration_changes",
    "top_kpis",
    "notifications_queue",
    "platform_version",
    "running_jobs",
    "failed_jobs",
    "job_queue_size",
    "worker_health",
    "job_execution_rate",
    "job_retry_rate",
]


@dataclass(frozen=True)
class WidgetSpec:
    widget_id: str
    title: str
    refresh_interval: int
    ttl_seconds: int


WIDGET_SPECS: dict[str, WidgetSpec] = {
    spec.widget_id: spec
    for spec in (
        WidgetSpec("system_status", "System Status", 30, 30),
        WidgetSpec("active_requests", "Active Requests", 15, 15),
        WidgetSpec("requests_by_vertical", "Requests By Vertical", 60, 60),
        WidgetSpec("manager_load", "Manager Load", 20, 20),
        WidgetSpec("sla_status", "SLA Status", 30, 30),
        WidgetSpec("workflow_status", "Workflow Status", 30, 30),
        WidgetSpec("recent_events", "Recent Events", 10, 10),
        WidgetSpec("recent_audit", "Recent Audit", 20, 20),
        WidgetSpec("configuration_changes", "Configuration Changes", 30, 30),
        WidgetSpec("top_kpis", "Top KPIs", 60, 60),
        WidgetSpec("notifications_queue", "Notifications Queue", 15, 15),
        WidgetSpec("platform_version", "Platform Version", 300, 300),
        WidgetSpec("running_jobs", "Running Jobs", 10, 10),
        WidgetSpec("failed_jobs", "Failed Jobs", 15, 15),
        WidgetSpec("job_queue_size", "Job Queue Size", 10, 10),
        WidgetSpec("worker_health", "Worker Health", 15, 15),
        WidgetSpec("job_execution_rate", "Job Execution Rate", 30, 30),
        WidgetSpec("job_retry_rate", "Job Retry Rate", 30, 30),
    )
}


ALL_WIDGET_IDS: tuple[str, ...] = tuple(WIDGET_SPECS.keys())


def get_widget_spec(widget_id: str) -> WidgetSpec:
    spec = WIDGET_SPECS.get(widget_id)
    if spec is None:
        from platform_operations.exceptions import WidgetNotFoundError

        raise WidgetNotFoundError(widget_id)
    return spec
