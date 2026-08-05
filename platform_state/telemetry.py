"""Enterprise telemetry for platform state / sync (Sprint 34.2D)."""

from __future__ import annotations

import statistics
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LatencySample:
    name: str
    ms: float
    at: float = field(default_factory=time.monotonic)


class EnterpriseTelemetry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._event_times: deque[float] = deque(maxlen=10_000)
        self._latencies: dict[str, deque[float]] = {}
        self._counters: dict[str, int] = {
            "events_total": 0,
            "failed_syncs": 0,
            "conflicts": 0,
            "replays": 0,
            "rollbacks": 0,
            "transactions_committed": 0,
            "transactions_rolled_back": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "heals": 0,
        }
        self._gauges: dict[str, float] = {
            "queue_size": 0.0,
            "memory_mb": 0.0,
        }
        self._started = time.monotonic()

    def incr(self, name: str, by: int = 1) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + by

    def gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = float(value)

    def record_event(self) -> None:
        with self._lock:
            now = time.monotonic()
            self._event_times.append(now)
            self._counters["events_total"] += 1

    def record_latency(self, name: str, ms: float) -> None:
        with self._lock:
            bucket = self._latencies.setdefault(name, deque(maxlen=2_000))
            bucket.append(float(ms))

    def time_block(self, name: str):
        return _Timer(self, name)

    def events_per_sec(self, window_s: float = 5.0) -> float:
        with self._lock:
            now = time.monotonic()
            recent = [t for t in self._event_times if now - t <= window_s]
        if window_s <= 0:
            return 0.0
        return len(recent) / window_s

    def _latency_stats(self, name: str) -> dict[str, float]:
        samples = list(self._latencies.get(name, []))
        if not samples:
            return {"count": 0, "p50": 0.0, "p95": 0.0, "avg": 0.0}
        ordered = sorted(samples)
        p50 = ordered[len(ordered) // 2]
        p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
        return {
            "count": float(len(ordered)),
            "p50": p50,
            "p95": p95,
            "avg": float(statistics.fmean(ordered)),
        }

    def cache_hit_rate(self) -> float:
        with self._lock:
            hits = int(self._counters.get("cache_hits", 0))
            misses = int(self._counters.get("cache_misses", 0))
        total = hits + misses
        if total <= 0:
            return 0.0
        return hits / total

    def snapshot(self) -> dict[str, Any]:
        self._refresh_memory()
        with self._lock:
            counters = dict(self._counters)
            gauges = dict(self._gauges)
            latency_names = list(self._latencies.keys())
        latencies = {n: self._latency_stats(n) for n in latency_names}
        hit_rate = self.cache_hit_rate()
        # Sprint 37.3 — emit cache hit ratio into enterprise metrics catalog
        try:
            from platform_observability.enterprise_metrics import enterprise_metrics

            enterprise_metrics.record_cache_hit_rate(hit_rate)
        except Exception:  # noqa: BLE001
            pass
        return {
            "sprint": "34.2D",
            "uptime_s": round(time.monotonic() - self._started, 3),
            "events_per_sec": round(self.events_per_sec(), 3),
            "counters": counters,
            "gauges": gauges,
            "latencies": latencies,
            "cache_hit_rate": round(hit_rate, 4),
            "tracks": [
                "events/sec",
                "queue_size",
                "sync_latency",
                "client_latency",
                "failed_syncs",
                "conflicts",
                "ai_execution_time",
                "database_timing",
                "api_timing",
                "memory_usage",
                "cache_hit_rate",
            ],
        }

    def _refresh_memory(self) -> None:
        try:
            import resource

            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # macOS reports bytes; Linux often KB — normalize roughly to MB
            mb = usage / (1024 * 1024) if usage > 10_000_000 else usage / 1024
            self.gauge("memory_mb", round(mb, 3))
        except Exception:  # noqa: BLE001
            pass

    def reset(self) -> None:
        with self._lock:
            self._event_times.clear()
            self._latencies.clear()
            for k in list(self._counters):
                self._counters[k] = 0
            self._gauges = {"queue_size": 0.0, "memory_mb": 0.0}
            self._started = time.monotonic()


class _Timer:
    def __init__(self, telemetry: EnterpriseTelemetry, name: str) -> None:
        self._t = telemetry
        self._name = name
        self._start = 0.0

    def __enter__(self) -> _Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc: Any) -> None:
        ms = (time.perf_counter() - self._start) * 1000.0
        self._t.record_latency(self._name, ms)


enterprise_telemetry = EnterpriseTelemetry()
