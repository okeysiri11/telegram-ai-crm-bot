"""CPU pool — cores, threads, load estimate."""

from __future__ import annotations

import os
import threading
from typing import Any


class CPUPool:
    def __init__(self, *, workers: int | None = None) -> None:
        self.cores = os.cpu_count() or 4
        self.workers = workers or min(self.cores, 8)
        self._lock = threading.RLock()
        self._active = 0
        self._load_samples: list[float] = []

    def acquire(self) -> bool:
        with self._lock:
            if self._active >= self.workers:
                return False
            self._active += 1
            return True

    def release(self) -> None:
        with self._lock:
            self._active = max(0, self._active - 1)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            active = self._active
        load = (active / max(self.workers, 1)) * 100.0
        # Rough RAM estimate without psutil dependency
        ram_mb = float(os.environ.get("HERCULES_RAM_MB", "4096"))
        return {
            "cores": self.cores,
            "workers": self.workers,
            "active": active,
            "load_est": round(load, 1),
            "ram_mb_est": ram_mb,
        }


cpu_pool = CPUPool()
