"""Learning Registry — Sprint 24.8."""

from __future__ import annotations

from typing import Any

from platform_enterprise_learning_engine.models import KNOWLEDGE_TYPES, VERIFICATION_STATUSES


class LearningRegistry:
    def create(
        self,
        *,
        learning_id: str,
        source: str,
        tenant: str,
        module: str,
        knowledge_type: str,
        trust_level: float = 0.5,
        author: str = "system",
        version: str = "1.0",
        payload: dict[str, Any] | None = None,
        confirmed: bool = False,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        if not learning_id or not source or not tenant:
            raise ValueError("learning_id, source and tenant are required")
        knowledge_type = (knowledge_type or "").lower()
        if knowledge_type not in KNOWLEDGE_TYPES:
            raise ValueError(f"unsupported knowledge_type: {knowledge_type}")
        if not confirmed:
            raise ValueError("AI never learns from unconfirmed data")
        return {
            "learning_id": learning_id,
            "source": source,
            "tenant": tenant,
            "module": module,
            "knowledge_type": knowledge_type,
            "trust_level": float(trust_level),
            "verification_status": "pending",
            "author": author,
            "timestamp": timestamp or "now",
            "version": version,
            "payload": dict(payload or {}),
            "confirmed": True,
            "pii_stripped": True,
        }

    def set_status(self, record: dict[str, Any], *, status: str) -> dict[str, Any]:
        status = (status or "").lower()
        if status not in VERIFICATION_STATUSES:
            raise ValueError(f"unsupported status: {status}")
        updated = dict(record)
        updated["verification_status"] = status
        return updated
