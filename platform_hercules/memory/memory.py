"""Hercules memory layers — task / conversation / agent / workflow."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryEntry:
    key: str
    value: Any
    kind: str
    created_at: float = field(default_factory=time.time)
    ttl_sec: float | None = None

    def expired(self) -> bool:
        if self.ttl_sec is None:
            return False
        return time.time() > self.created_at + self.ttl_sec


class HerculesMemory:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._store: dict[str, MemoryEntry] = {}
        self._snapshots: dict[str, dict[str, Any]] = {}

    def put(self, key: str, value: Any, *, kind: str = "temporary", ttl_sec: float | None = None) -> None:
        with self._lock:
            self._store[key] = MemoryEntry(key=key, value=value, kind=kind, ttl_sec=ttl_sec)

    def get(self, key: str) -> Any | None:
        with self._lock:
            e = self._store.get(key)
            if not e or e.expired():
                self._store.pop(key, None)
                return None
            return e.value

    def snapshot(self, session_id: str) -> dict[str, Any]:
        with self._lock:
            data = {k: e.value for k, e in self._store.items() if not e.expired()}
            self._snapshots[session_id] = data
            return dict(data)

    def restore(self, session_id: str) -> dict[str, Any]:
        with self._lock:
            data = self._snapshots.get(session_id) or {}
            for k, v in data.items():
                self._store[k] = MemoryEntry(key=k, value=v, kind="persistent")
            return dict(data)


hercules_memory = HerculesMemory()
