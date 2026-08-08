"""Hercules security — sandbox flags, rate limits, audit."""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AuditEntry:
    action: str
    actor: str
    detail: str
    ts: float = field(default_factory=time.time)


class HerculesSecurity:
    def __init__(self, *, rate_limit_per_min: int = 120) -> None:
        self._lock = threading.RLock()
        self.rate_limit = rate_limit_per_min
        self._hits: dict[str, list[float]] = defaultdict(list)
        self.audit: list[AuditEntry] = []
        self.sandbox = True  # default safe mode

    def check_rate(self, actor: str) -> bool:
        now = time.time()
        with self._lock:
            window = [t for t in self._hits[actor] if now - t < 60]
            if len(window) >= self.rate_limit:
                self._hits[actor] = window
                return False
            window.append(now)
            self._hits[actor] = window
            return True

    def validate_role(self, roles: list[str], required: str = "owner") -> bool:
        return required in roles or "admin" in roles or "platform_owner" in roles

    def record(self, action: str, actor: str, detail: str = "") -> None:
        with self._lock:
            self.audit.append(AuditEntry(action=action, actor=actor, detail=detail))
            if len(self.audit) > 2000:
                self.audit = self.audit[-1000:]

    def audit_tail(self, n: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {"action": a.action, "actor": a.actor, "detail": a.detail, "ts": a.ts}
                for a in self.audit[-n:]
            ]


hercules_security = HerculesSecurity()
