"""Sprint 43.1 — AI pipeline analytics."""

from __future__ import annotations

from collections import Counter
from threading import Lock
from typing import Any


class AiPipelineAnalytics:
    def __init__(self) -> None:
        self._lock = Lock()
        self.generations = 0
        self.errors = 0
        self.cache_hits = 0
        self.total_cost = 0.0
        self.total_duration = 0.0
        self.by_modality: Counter[str] = Counter()
        self.by_provider: Counter[str] = Counter()
        self.by_channel: Counter[str] = Counter()
        self.by_status: Counter[str] = Counter()
        self.wait_samples: list[float] = []

    def reset(self) -> None:
        with self._lock:
            self.generations = 0
            self.errors = 0
            self.cache_hits = 0
            self.total_cost = 0.0
            self.total_duration = 0.0
            self.by_modality.clear()
            self.by_provider.clear()
            self.by_channel.clear()
            self.by_status.clear()
            self.wait_samples.clear()

    def record(self, task: Any) -> None:
        with self._lock:
            self.generations += 1
            self.by_modality[task.modality] += 1
            self.by_channel[task.channel] += 1
            self.by_status[task.status] += 1
            if task.provider_id:
                self.by_provider[task.provider_id] += 1
            self.total_cost += float(task.cost_estimate or 0)
            self.total_duration += float(task.duration_sec())
            if getattr(task, "cache_hit", False):
                self.cache_hits += 1
            if task.status == "ошибка":
                self.errors += 1
            self.wait_samples.append(float(task.duration_sec()))
            if len(self.wait_samples) > 500:
                self.wait_samples = self.wait_samples[-500:]

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            waits = list(self.wait_samples)
            avg_wait = round(sum(waits) / len(waits), 3) if waits else 0.0
            return {
                "generations": self.generations,
                "errors": self.errors,
                "cache_hits": self.cache_hits,
                "total_cost": round(self.total_cost, 4),
                "avg_duration_sec": round(self.total_duration / max(1, self.generations), 3),
                "avg_wait_sec": avg_wait,
                "popular_models": dict(self.by_provider.most_common(10)),
                "by_modality": dict(self.by_modality),
                "by_channel": dict(self.by_channel),
                "by_status": dict(self.by_status),
                "load": self.by_status.get("генерируется", 0) + self.by_status.get("в_очереди", 0),
            }


ai_pipeline_analytics = AiPipelineAnalytics()
