# CircuitBreaker — closed, open, half-open states with automatic reset.

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from platform_reliability.config import DEFAULT_RELIABILITY_CONFIG, ReliabilityConfig
from platform_reliability.exceptions import CircuitOpenError
from platform_reliability.models import CircuitBreakerState, CircuitState

logger = logging.getLogger(__name__)


class CircuitBreaker:
    def __init__(self, *, config: ReliabilityConfig | None = None) -> None:
        self._config = config or DEFAULT_RELIABILITY_CONFIG
        self._circuits: dict[str, CircuitBreakerState] = {}
        self._events: list[dict[str, Any]] = []

    def reset(self) -> None:
        self._circuits.clear()
        self._events.clear()

    def get_or_create(self, circuit_id: str) -> CircuitBreakerState:
        if circuit_id not in self._circuits:
            self._circuits[circuit_id] = CircuitBreakerState(
                circuit_id=circuit_id,
                failure_threshold=self._config.circuit_failure_threshold,
                recovery_timeout_sec=self._config.circuit_recovery_timeout_sec,
            )
        return self._circuits[circuit_id]

    def state(self, circuit_id: str) -> CircuitState:
        cb = self.get_or_create(circuit_id)
        self._maybe_half_open(cb)
        return cb.state

    def record_success(self, circuit_id: str) -> None:
        cb = self.get_or_create(circuit_id)
        if cb.state == CircuitState.HALF_OPEN:
            cb.state = CircuitState.CLOSED
            cb.failure_count = 0
            cb.success_count += 1
            self._events.append({"circuit_id": circuit_id, "event": "closed", "timestamp": time.time()})
            logger.info("circuit_closed id=%s", circuit_id)
        elif cb.state == CircuitState.CLOSED:
            cb.failure_count = max(0, cb.failure_count - 1)

    def record_failure(self, circuit_id: str) -> None:
        cb = self.get_or_create(circuit_id)
        cb.failure_count += 1
        cb.last_failure_at = time.time()
        if cb.state == CircuitState.HALF_OPEN:
            cb.state = CircuitState.OPEN
            cb.opened_at = time.time()
            self._events.append({"circuit_id": circuit_id, "event": "reopened", "timestamp": time.time()})
        elif cb.failure_count >= cb.failure_threshold:
            cb.state = CircuitState.OPEN
            cb.opened_at = time.time()
            self._events.append({"circuit_id": circuit_id, "event": "opened", "timestamp": time.time()})
            logger.warning("circuit_opened id=%s failures=%d", circuit_id, cb.failure_count)

    def _maybe_half_open(self, cb: CircuitBreakerState) -> None:
        if cb.state == CircuitState.OPEN:
            elapsed = time.time() - cb.opened_at
            if elapsed >= cb.recovery_timeout_sec:
                cb.state = CircuitState.HALF_OPEN
                self._events.append({"circuit_id": cb.circuit_id, "event": "half_open", "timestamp": time.time()})

    def allow_request(self, circuit_id: str) -> bool:
        cb = self.get_or_create(circuit_id)
        self._maybe_half_open(cb)
        return cb.state != CircuitState.OPEN

    async def call(
        self,
        circuit_id: str,
        fn: Callable[[], Awaitable[Any]],
    ) -> Any:
        if not self.allow_request(circuit_id):
            raise CircuitOpenError(circuit_id)
        try:
            result = await fn()
            self.record_success(circuit_id)
            return result
        except Exception:
            self.record_failure(circuit_id)
            raise

    def force_reset(self, circuit_id: str) -> None:
        cb = self.get_or_create(circuit_id)
        cb.state = CircuitState.CLOSED
        cb.failure_count = 0
        self._events.append({"circuit_id": circuit_id, "event": "manual_reset", "timestamp": time.time()})

    def event_log(self) -> list[dict[str, Any]]:
        return list(self._events)


circuit_breaker = CircuitBreaker()
