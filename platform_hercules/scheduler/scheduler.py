"""Hercules multi-lane priority scheduler."""

from __future__ import annotations

import heapq
import itertools
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from platform_hercules.core.models import QueueKind


@dataclass(order=True)
class _HeapItem:
    priority: int
    seq: int
    ready_at: float
    job_id: str = field(compare=False)


class HerculesScheduler:
    """Priority + delayed + lane-aware dispatcher (in-memory)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._heaps: dict[QueueKind, list[_HeapItem]] = {k: [] for k in QueueKind}
        self._seq = itertools.count()
        self._delayed: list[_HeapItem] = []

    def enqueue(
        self,
        job_id: str,
        *,
        queue: QueueKind = QueueKind.TASK,
        priority: int = 5,
        delay_sec: float = 0.0,
    ) -> None:
        ready = time.time() + max(0.0, delay_sec)
        item = _HeapItem(priority=priority, seq=next(self._seq), ready_at=ready, job_id=job_id)
        with self._lock:
            if delay_sec > 0:
                heapq.heappush(self._delayed, item)
            else:
                heapq.heappush(self._heaps[queue], item)

    def _promote_delayed(self) -> None:
        now = time.time()
        while self._delayed and self._delayed[0].ready_at <= now:
            item = heapq.heappop(self._delayed)
            # delayed items default to TASK unless stored elsewhere — use TASK
            heapq.heappush(self._heaps[QueueKind.TASK], item)

    def dequeue(self, queues: list[QueueKind] | None = None) -> str | None:
        with self._lock:
            self._promote_delayed()
            kinds = queues or list(QueueKind)
            best: _HeapItem | None = None
            best_q: QueueKind | None = None
            for q in kinds:
                heap = self._heaps[q]
                if heap and (best is None or heap[0] < best):
                    best = heap[0]
                    best_q = q
            if best is None or best_q is None:
                return None
            heapq.heappop(self._heaps[best_q])
            return best.job_id

    def depths(self) -> dict[str, int]:
        with self._lock:
            self._promote_delayed()
            out = {k.value: len(h) for k, h in self._heaps.items()}
            out["delayed"] = len(self._delayed)
            return out

    def select_worker(self, workers: list[dict[str, Any]], *, need_gpu: bool = False) -> str | None:
        """Simple load balancer — least busy matching capability."""
        candidates = [
            w
            for w in workers
            if w.get("online") and (not need_gpu or w.get("gpu"))
        ]
        if not candidates:
            candidates = [w for w in workers if w.get("online")]
        if not candidates:
            return None
        candidates.sort(key=lambda w: w.get("load", 0))
        return candidates[0]["id"]


hercules_scheduler = HerculesScheduler()
