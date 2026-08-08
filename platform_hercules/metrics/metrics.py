"""Hercules metrics — jobs/sec, latency, cost, queues."""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any


class HerculesMetrics:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.finished = 0
        self.failed = 0
        self.retries = 0
        self.running = 0
        self.latencies: deque[float] = deque(maxlen=500)
        self.cost_total = 0.0
        self._timestamps: deque[float] = deque(maxlen=500)

    def on_start(self) -> None:
        with self._lock:
            self.running += 1

    def on_success(self, latency: float, *, cost: float = 0.0) -> None:
        with self._lock:
            self.running = max(0, self.running - 1)
            self.finished += 1
            self.latencies.append(latency)
            self.cost_total += cost
            self._timestamps.append(time.time())

    def on_failure(self, latency: float = 0.0) -> None:
        with self._lock:
            self.running = max(0, self.running - 1)
            self.failed += 1
            if latency:
                self.latencies.append(latency)

    def on_retry(self) -> None:
        with self._lock:
            self.retries += 1

    def jobs_per_sec(self) -> float:
        with self._lock:
            now = time.time()
            recent = [t for t in self._timestamps if now - t <= 60]
            return round(len(recent) / 60.0, 3)

    def dashboard(self) -> dict[str, Any]:
        with self._lock:
            avg_lat = sum(self.latencies) / len(self.latencies) if self.latencies else 0.0
            return {
                "running": self.running,
                "finished": self.finished,
                "failed": self.failed,
                "retry": self.retries,
                "jobs_per_sec": self.jobs_per_sec(),
                "latency_avg_sec": round(avg_lat, 3),
                "cost_total": round(self.cost_total, 4),
            }


hercules_metrics = HerculesMetrics()
