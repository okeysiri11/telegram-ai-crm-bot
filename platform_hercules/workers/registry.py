"""Hercules workers registry."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkerSpec:
    id: str
    kind: str  # universal|image|video|voice|llm|telegram|crm|erp|automation|background
    online: bool = True
    gpu: bool = False
    load: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


class WorkerRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._workers: dict[str, WorkerSpec] = {}
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        defaults = [
            WorkerSpec("w-universal", "universal"),
            WorkerSpec("w-image", "image", gpu=True),
            WorkerSpec("w-video", "video", gpu=True),
            WorkerSpec("w-voice", "voice"),
            WorkerSpec("w-llm", "llm"),
            WorkerSpec("w-telegram", "telegram"),
            WorkerSpec("w-crm", "crm"),
            WorkerSpec("w-erp", "erp"),
            WorkerSpec("w-automation", "automation"),
            WorkerSpec("w-background", "background"),
        ]
        for w in defaults:
            self._workers[w.id] = w

    def list(self) -> list[WorkerSpec]:
        with self._lock:
            return list(self._workers.values())

    def as_dicts(self) -> list[dict[str, Any]]:
        return [
            {"id": w.id, "kind": w.kind, "online": w.online, "gpu": w.gpu, "load": w.load}
            for w in self.list()
        ]

    def heartbeat(self, worker_id: str, *, load: float = 0.0) -> None:
        with self._lock:
            w = self._workers.get(worker_id)
            if w:
                w.online = True
                w.load = load

    def pick(self, kind: str | None = None, *, need_gpu: bool = False) -> WorkerSpec | None:
        workers = self.list()
        if kind:
            workers = [w for w in workers if w.kind == kind or w.kind == "universal"]
        if need_gpu:
            gpu_workers = [w for w in workers if w.gpu and w.online]
            if gpu_workers:
                workers = gpu_workers
        online = [w for w in workers if w.online]
        if not online:
            return None
        online.sort(key=lambda w: w.load)
        return online[0]


worker_registry = WorkerRegistry()
