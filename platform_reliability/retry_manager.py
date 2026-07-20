# RetryManager — configurable retry with exponential/linear backoff.

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from platform_reliability.config import DEFAULT_RELIABILITY_CONFIG, ReliabilityConfig
from platform_reliability.exceptions import MaxRetriesExceededError
from platform_reliability.models import RecoveryPolicy, RetryResult, RetryStrategy

logger = logging.getLogger(__name__)


class RetryManager:
    def __init__(self, *, config: ReliabilityConfig | None = None) -> None:
        self._config = config or DEFAULT_RELIABILITY_CONFIG
        self._metrics: list[dict[str, Any]] = []

    def reset(self) -> None:
        self._metrics.clear()

    def compute_delay_ms(self, attempt: int, policy: RecoveryPolicy) -> float:
        if policy.retry_strategy == RetryStrategy.LINEAR:
            delay = policy.backoff_base_ms * attempt
        elif policy.retry_strategy == RetryStrategy.FIXED:
            delay = policy.backoff_base_ms
        else:
            delay = policy.backoff_base_ms * (2 ** (attempt - 1))
        return min(delay, policy.backoff_max_ms)

    def should_retry(self, error_type: str, policy: RecoveryPolicy) -> bool:
        return error_type in policy.retry_on or "transient" in policy.retry_on

    async def execute(
        self,
        fn: Callable[[], Awaitable[Any]],
        *,
        policy: RecoveryPolicy | None = None,
        error_type: str = "transient",
    ) -> RetryResult:
        policy = policy or RecoveryPolicy(max_retries=self._config.default_max_retries)
        started = time.monotonic()
        total_delay = 0.0
        last_error = ""

        for attempt in range(1, policy.max_retries + 2):
            try:
                result = await fn()
                self._record(attempt, True, total_delay)
                return RetryResult(success=True, attempts=attempt, result=result, total_delay_ms=total_delay)
            except Exception as exc:
                last_error = str(exc)
                if attempt > policy.max_retries or not self.should_retry(error_type, policy):
                    self._record(attempt, False, total_delay)
                    break
                delay_ms = self.compute_delay_ms(attempt, policy)
                total_delay += delay_ms
                logger.debug("retry attempt=%d delay_ms=%.1f error=%s", attempt, delay_ms, last_error)
                await asyncio.sleep(delay_ms / 1000)

        raise MaxRetriesExceededError(policy.max_retries + 1)

    async def execute_safe(
        self,
        fn: Callable[[], Awaitable[Any]],
        *,
        policy: RecoveryPolicy | None = None,
        error_type: str = "transient",
    ) -> RetryResult:
        try:
            return await self.execute(fn, policy=policy, error_type=error_type)
        except MaxRetriesExceededError as exc:
            return RetryResult(success=False, attempts=exc.attempts, error=str(exc))

    def _record(self, attempts: int, success: bool, delay_ms: float) -> None:
        self._metrics.append({"attempts": attempts, "success": success, "delay_ms": delay_ms})

    def metrics(self) -> dict[str, Any]:
        total = len(self._metrics)
        if total == 0:
            return {"retries": 0, "success_rate": 0.0, "avg_attempts": 0.0}
        successes = sum(1 for m in self._metrics if m["success"])
        return {
            "retries": total,
            "success_rate": round(successes / total, 4),
            "avg_attempts": round(sum(m["attempts"] for m in self._metrics) / total, 2),
        }


retry_manager = RetryManager()
