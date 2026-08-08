"""Resource manager — CPU / GPU / RAM / quotas / concurrency."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResourceSnapshot:
    cpu_cores: int
    cpu_percent_est: float
    ram_mb_est: float
    gpu_available: bool
    gpu_backend: str  # none|cuda|metal|fallback_cpu
    vram_mb_est: float
    concurrent_jobs: int
    max_concurrent: int
    api_quota_remaining: int | None = None


@dataclass
class ResourceLease:
    lease_id: str
    cpu_units: int = 1
    gpu: bool = False
    released: bool = False


class ResourceManager:
    """Tracks compute budgets for Hercules (in-process; production can bind to k8s)."""

    def __init__(self, *, max_concurrent: int | None = None) -> None:
        self._lock = threading.RLock()
        self.max_concurrent = max_concurrent or int(os.environ.get("HERCULES_MAX_CONCURRENT", "32"))
        self._leases: dict[str, ResourceLease] = {}
        self._gpu_reserved = 0
        self.provider_limits: dict[str, int] = {}

    def snapshot(self) -> ResourceSnapshot:
        from platform_hercules.cpu.pool import cpu_pool
        from platform_hercules.gpu.pool import gpu_pool

        cpu = cpu_pool.snapshot()
        gpu = gpu_pool.snapshot()
        with self._lock:
            running = len([L for L in self._leases.values() if not L.released])
        return ResourceSnapshot(
            cpu_cores=cpu["cores"],
            cpu_percent_est=cpu["load_est"],
            ram_mb_est=cpu["ram_mb_est"],
            gpu_available=gpu["available"],
            gpu_backend=gpu["backend"],
            vram_mb_est=gpu["vram_mb_est"],
            concurrent_jobs=running,
            max_concurrent=self.max_concurrent,
        )

    def try_acquire(self, *, lease_id: str, cpu_units: int = 1, gpu: bool = False) -> ResourceLease | None:
        with self._lock:
            active = len([L for L in self._leases.values() if not L.released])
            if active >= self.max_concurrent:
                return None
            if gpu:
                from platform_hercules.gpu.pool import gpu_pool

                if not gpu_pool.try_reserve(lease_id):
                    # Fallback: allow on CPU path
                    gpu = False
            lease = ResourceLease(lease_id=lease_id, cpu_units=cpu_units, gpu=gpu)
            self._leases[lease_id] = lease
            return lease

    def release(self, lease_id: str) -> None:
        with self._lock:
            lease = self._leases.get(lease_id)
            if not lease or lease.released:
                return
            lease.released = True
            if lease.gpu:
                from platform_hercules.gpu.pool import gpu_pool

                gpu_pool.release(lease_id)

    def dashboard(self) -> dict[str, Any]:
        snap = self.snapshot()
        return {
            "cpu_cores": snap.cpu_cores,
            "cpu_load": snap.cpu_percent_est,
            "ram_mb": snap.ram_mb_est,
            "gpu": snap.gpu_backend,
            "vram_mb": snap.vram_mb_est,
            "running": snap.concurrent_jobs,
            "max_concurrent": snap.max_concurrent,
        }


resource_manager = ResourceManager()
