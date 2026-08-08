"""Epic 45.3 — Retry Engine with provider failover."""
from __future__ import annotations
from typing import Any, Callable

class RetryEngine:
    def __init__(self, *, max_attempts: int = 3) -> None:
        self.max_attempts = max_attempts
        self.providers = ["primary", "fallback", "emergency"]
    def run(self, fn: Callable[[str], Any], *, providers: list[str] | None = None) -> dict[str, Any]:
        providers = providers or self.providers
        errors: list[str] = []
        for attempt in range(1, self.max_attempts + 1):
            provider = providers[(attempt - 1) % len(providers)]
            try:
                result = fn(provider)
                return {"ok": True, "attempt": attempt, "provider": provider, "result": result, "errors": errors}
            except Exception as e:  # noqa: BLE001
                errors.append(f"{provider}:{e}")
        return {"ok": False, "attempt": self.max_attempts, "provider": providers[-1], "result": None, "errors": errors}

retry_engine = RetryEngine()
