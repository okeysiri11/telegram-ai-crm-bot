"""Sandbox — constrained execution environment."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_tools.models import SANDBOX_LIMITS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class Sandbox:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def create(
        self,
        *,
        tool_id: str,
        allow_network: bool = False,
        allow_files: bool = True,
        cpu_limit: float = 1.0,
        memory_mb: int = 256,
        timeout_ms: int = 5000,
    ) -> dict[str, Any]:
        if timeout_ms <= 0:
            raise ValidationError("timeout_ms must be positive")
        sid = _id("ats_sbx")
        return self.store.ats_sandboxes.save(
            sid,
            {
                "sandbox_id": sid,
                "tool_id": tool_id,
                "allow_network": allow_network,
                "allow_files": allow_files,
                "cpu_limit": float(cpu_limit),
                "memory_mb": int(memory_mb),
                "timeout_ms": int(timeout_ms),
                "limits": list(SANDBOX_LIMITS),
                "created_at": _now(),
            },
        )

    def validate(self, *, sandbox_id: str, needs_network: bool = False, needs_files: bool = False) -> dict[str, Any]:
        from applications.enterprise_hub.shared.exceptions import NotFoundError

        sbx = self.store.ats_sandboxes.get(sandbox_id)
        if not sbx:
            raise NotFoundError(f"sandbox not found: {sandbox_id}")
        ok = True
        reasons = []
        if needs_network and not sbx.get("allow_network"):
            ok = False
            reasons.append("network denied")
        if needs_files and not sbx.get("allow_files"):
            ok = False
            reasons.append("files denied")
        return {"sandbox_id": sandbox_id, "allowed": ok, "reasons": reasons, "profile": sbx}
