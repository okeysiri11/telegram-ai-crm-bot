# Job handler registry — dynamic registration of job handlers.

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from platform_jobs.exceptions import JobHandlerError

logger = logging.getLogger(__name__)

JobHandler = Callable[[dict[str, Any]], Awaitable[Any] | Any]


class JobRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, JobHandler] = {}

    def register(self, name: str, handler: JobHandler) -> None:
        self._handlers[name] = handler
        logger.info("job_handler_registered name=%s", name)

    def get(self, name: str) -> JobHandler:
        handler = self._handlers.get(name)
        if handler is None:
            raise JobHandlerError(f"Job handler '{name}' not registered")
        return handler

    def list_handlers(self) -> list[str]:
        return sorted(self._handlers.keys())

    def reset(self) -> None:
        self._handlers.clear()


job_registry = JobRegistry()
