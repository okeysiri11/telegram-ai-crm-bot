# Structured logging service — centralized JSON logs with correlation.

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from contextvars import ContextVar
from typing import Any

from platform_observability.models import StructuredLogEntry

logger = logging.getLogger(__name__)

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
_request_id: ContextVar[str] = ContextVar("request_id", default="")
_user_id: ContextVar[int | None] = ContextVar("user_id", default=None)
_job_id: ContextVar[str | None] = ContextVar("job_id", default=None)
_workflow_id: ContextVar[str | None] = ContextVar("workflow_id", default=None)
_agent_id: ContextVar[str | None] = ContextVar("agent_id", default=None)
_task_id: ContextVar[str | None] = ContextVar("task_id", default=None)

_log_buffer: asyncio.Queue | None = None


class LoggingService:
    def __init__(self, *, max_entries: int = 50_000) -> None:
        self._entries: list[StructuredLogEntry] = []
        self._max_entries = max_entries

    def reset(self) -> None:
        self._entries.clear()

    @staticmethod
    def new_correlation_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def set_context(
        *,
        correlation_id: str | None = None,
        request_id: str | None = None,
        user_id: int | None = None,
        job_id: str | None = None,
        workflow_id: str | None = None,
        agent_id: str | None = None,
        task_id: str | None = None,
    ) -> None:
        if correlation_id:
            _correlation_id.set(correlation_id)
        if request_id:
            _request_id.set(request_id)
        if user_id is not None:
            _user_id.set(user_id)
        if job_id:
            _job_id.set(job_id)
        if workflow_id:
            _workflow_id.set(workflow_id)
        if agent_id:
            _agent_id.set(agent_id)
        if task_id:
            _task_id.set(task_id)

    @staticmethod
    def get_context() -> dict[str, Any]:
        return {
            "correlation_id": _correlation_id.get() or LoggingService.new_correlation_id(),
            "request_id": _request_id.get() or None,
            "user_id": _user_id.get(),
            "job_id": _job_id.get(),
            "workflow_id": _workflow_id.get(),
            "agent_id": _agent_id.get(),
            "task_id": _task_id.get(),
        }

    def log(
        self,
        level: str,
        message: str,
        *,
        component: str = "platform",
        extra: dict[str, Any] | None = None,
    ) -> StructuredLogEntry:
        ctx = self.get_context()
        entry = StructuredLogEntry(
            level=level.upper(),
            message=message,
            correlation_id=ctx["correlation_id"],
            request_id=ctx.get("request_id"),
            user_id=ctx.get("user_id"),
            job_id=ctx.get("job_id"),
            workflow_id=ctx.get("workflow_id"),
            agent_id=ctx.get("agent_id"),
            task_id=ctx.get("task_id"),
            component=component,
            extra=extra or {},
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries :]

        # Non-blocking: emit JSON to stdlib logger without blocking caller
        try:
            logger.log(
                getattr(logging, entry.level, logging.INFO),
                json.dumps(entry.to_dict(), default=str),
            )
        except Exception:
            pass
        return entry

    def info(self, message: str, **kwargs: Any) -> StructuredLogEntry:
        return self.log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> StructuredLogEntry:
        return self.log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> StructuredLogEntry:
        return self.log("ERROR", message, **kwargs)

    def query(
        self,
        *,
        level: str | None = None,
        correlation_id: str | None = None,
        component: str | None = None,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        entries = self._entries
        if level:
            entries = [e for e in entries if e.level == level.upper()]
        if correlation_id:
            entries = [e for e in entries if e.correlation_id == correlation_id]
        if component:
            entries = [e for e in entries if e.component == component]
        if agent_id:
            entries = [e for e in entries if e.agent_id == agent_id]
        if workflow_id:
            entries = [e for e in entries if e.workflow_id == workflow_id]
        return [e.to_dict() for e in entries[-limit:]]


logging_service = LoggingService()
