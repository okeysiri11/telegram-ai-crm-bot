# Per-skill cache with TTL and invalidation.

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from platform_ai.skills.models import SkillExecutionResult


class SkillCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, SkillExecutionResult]] = {}

    def reset(self) -> None:
        self._store.clear()

    def _key(self, skill_id: str, input_data: dict[str, Any]) -> str:
        payload = json.dumps({"skill_id": skill_id, "input": input_data}, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, skill_id: str, input_data: dict[str, Any], ttl: float) -> SkillExecutionResult | None:
        key = self._key(skill_id, input_data)
        entry = self._store.get(key)
        if not entry:
            return None
        expires_at, result = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        cached = SkillExecutionResult(
            skill_id=result.skill_id,
            execution_id=result.execution_id,
            success=result.success,
            output=dict(result.output),
            raw_content=result.raw_content,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            latency_ms=result.latency_ms,
            cached=True,
            provider_id=result.provider_id,
            model_id=result.model_id,
        )
        return cached

    def set(self, skill_id: str, input_data: dict[str, Any], result: SkillExecutionResult, ttl: float) -> None:
        key = self._key(skill_id, input_data)
        self._store[key] = (time.time() + ttl, result)

    def invalidate(self, skill_id: str | None = None) -> int:
        if skill_id is None:
            count = len(self._store)
            self._store.clear()
            return count
        keys = [k for k, (_, r) in self._store.items() if r.skill_id == skill_id]
        for k in keys:
            del self._store[k]
        return len(keys)

    def stats(self) -> dict[str, Any]:
        return {"entries": len(self._store)}


skill_cache = SkillCache()
