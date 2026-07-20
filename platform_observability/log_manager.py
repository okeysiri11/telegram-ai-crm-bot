# LogManager — structured JSON logging with retention interface.

from __future__ import annotations

from platform_observability.logging_service import LoggingService, logging_service
from platform_observability.models import MonitoringContext
from platform_observability.retention_manager import RetentionManager, retention_manager


class LogManager:
    def __init__(
        self,
        *,
        logging: LoggingService | None = None,
        retention: RetentionManager | None = None,
    ) -> None:
        self._logging = logging or logging_service
        self._retention = retention or retention_manager

    def apply_context(self, ctx: MonitoringContext) -> None:
        self._logging.set_context(
            correlation_id=ctx.correlation_id or None,
            request_id=ctx.request_id,
            workflow_id=ctx.workflow_id,
            agent_id=ctx.agent_id,
            task_id=ctx.task_id,
            user_id=ctx.user_id,
        )

    def info(self, message: str, **kwargs):
        return self._logging.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        return self._logging.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        return self._logging.error(message, **kwargs)

    def query(self, **kwargs):
        return self._logging.query(**kwargs)

    def set_retention(self, **kwargs):
        return self._retention.set_policy(**kwargs)

    def purge_expired(self) -> dict[str, int]:
        return self._retention.apply()


log_manager = LogManager()
