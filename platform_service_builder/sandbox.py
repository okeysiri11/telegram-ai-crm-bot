"""Service sandbox — isolated runtime context per service."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SandboxContext:
    sandbox_id: str
    service_id: str
    created_at: float = field(default_factory=time.time)
    env: dict[str, str] = field(default_factory=dict)
    resources: dict[str, Any] = field(default_factory=dict)
    isolated: bool = True
    active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sandbox_id": self.sandbox_id,
            "service_id": self.service_id,
            "created_at": self.created_at,
            "env": dict(self.env),
            "resources": dict(self.resources),
            "isolated": self.isolated,
            "active": self.active,
            "metadata": dict(self.metadata),
        }


class ServiceSandbox:
    """Lightweight in-process sandbox registry (no core mutation)."""

    def __init__(self) -> None:
        self._sandboxes: dict[str, SandboxContext] = {}

    def reset(self) -> None:
        self._sandboxes.clear()

    def create(
        self,
        service_id: str,
        *,
        env: dict[str, str] | None = None,
        resources: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SandboxContext:
        sid = f"sbx_{uuid.uuid4().hex[:12]}"
        ctx = SandboxContext(
            sandbox_id=sid,
            service_id=service_id,
            env=dict(env or {}),
            resources=dict(resources or {}),
            metadata=dict(metadata or {}),
        )
        self._sandboxes[sid] = ctx
        return ctx

    def get(self, sandbox_id: str) -> SandboxContext | None:
        return self._sandboxes.get(sandbox_id)

    def destroy(self, sandbox_id: str) -> bool:
        ctx = self._sandboxes.pop(sandbox_id, None)
        if ctx:
            ctx.active = False
            return True
        return False

    def for_service(self, service_id: str) -> list[SandboxContext]:
        return [s for s in self._sandboxes.values() if s.service_id == service_id and s.active]


service_sandbox = ServiceSandbox()
