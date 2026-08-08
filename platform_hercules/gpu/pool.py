"""GPU pool — CUDA / Apple Metal detect + reservation + CPU fallback."""

from __future__ import annotations

import platform
import threading
from typing import Any


def detect_gpu_backend() -> str:
    # Prefer env override for CI/tests
    import os

    forced = os.environ.get("HERCULES_GPU_BACKEND")
    if forced:
        return forced
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "metal"
    except Exception:
        pass
    if platform.system() == "Darwin":
        # Metal may exist without torch; report soft availability
        return "metal_soft"
    return "fallback_cpu"


class GPUPool:
    def __init__(self, *, slots: int = 2) -> None:
        self._lock = threading.RLock()
        self.slots = slots
        self._reserved: set[str] = set()
        self.backend = detect_gpu_backend()
        self.temperature_c: float | None = None

    @property
    def available(self) -> bool:
        return self.backend not in ("fallback_cpu", "none")

    def try_reserve(self, lease_id: str) -> bool:
        with self._lock:
            if not self.available:
                return False
            if len(self._reserved) >= self.slots:
                return False
            self._reserved.add(lease_id)
            return True

    def release(self, lease_id: str) -> None:
        with self._lock:
            self._reserved.discard(lease_id)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            used = len(self._reserved)
        vram = 0.0
        if self.backend == "cuda":
            vram = 8192.0  # soft estimate without nvidia-smi
        elif self.backend.startswith("metal"):
            vram = 4096.0
        return {
            "available": self.available,
            "backend": self.backend,
            "slots": self.slots,
            "used": used,
            "vram_mb_est": vram,
            "temperature_c": self.temperature_c,
            "fallback": "cpu" if not self.available else None,
        }


gpu_pool = GPUPool()
