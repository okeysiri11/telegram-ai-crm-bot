
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

from applications.enterprise_hub.developer_platform.models import SANDBOX_LIMITS


class PluginSandbox:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def create(
        self,
        *,
        plugin_id: str,
        allow_network: bool = False,
        allow_filesystem: bool = False,
        memory_mb: int = 128,
        cpu_ms: int = 1000,
        allow_syscalls: bool = False,
    ) -> dict[str, Any]:
        if memory_mb <= 0 or cpu_ms <= 0:
            raise ValidationError("memory_mb and cpu_ms must be positive")
        sid = _id("sdp_sbx")
        return self.store.sdp_sandboxes.save(
            sid,
            {
                "sandbox_id": sid,
                "plugin_id": plugin_id,
                "allow_network": allow_network,
                "allow_filesystem": allow_filesystem,
                "allow_syscalls": allow_syscalls,
                "memory_mb": int(memory_mb),
                "cpu_ms": int(cpu_ms),
                "limits": list(SANDBOX_LIMITS),
                "created_at": _now(),
            },
        )

    def check(
        self,
        *,
        sandbox_id: str,
        needs_network: bool = False,
        needs_filesystem: bool = False,
        needs_syscalls: bool = False,
        memory_mb: int = 0,
        cpu_ms: int = 0,
    ) -> dict[str, Any]:
        sbx = self.store.sdp_sandboxes.get(sandbox_id)
        if not sbx:
            raise NotFoundError(f"sandbox not found: {sandbox_id}")
        reasons: list[str] = []
        if needs_network and not sbx.get("allow_network"):
            reasons.append("network denied")
        if needs_filesystem and not sbx.get("allow_filesystem"):
            reasons.append("filesystem denied")
        if needs_syscalls and not sbx.get("allow_syscalls"):
            reasons.append("syscalls denied")
        if memory_mb and memory_mb > int(sbx.get("memory_mb", 0)):
            reasons.append("memory exceeded")
        if cpu_ms and cpu_ms > int(sbx.get("cpu_ms", 0)):
            reasons.append("cpu exceeded")
        return {
            "sandbox_id": sandbox_id,
            "allowed": not reasons,
            "reasons": reasons,
            "profile": sbx,
        }

    def status(self) -> dict[str, Any]:
        return {"sandboxes": len(self.store.sdp_sandboxes.list_all())}
