# Management request context — actor, timing, audit metadata.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from aiohttp import web


@dataclass
class ManagementContext:
    request_id: str
    actor_telegram_id: int | None
    role: str
    method: str
    path: str
    remote_ip: str
    started_at: float = field(default_factory=time.perf_counter)
    audit_id: str | None = None

    @classmethod
    def from_request(
        cls,
        request: web.Request,
        *,
        role: str,
        request_id: str | None = None,
    ) -> ManagementContext:
        actor = _extract_actor(request)
        return cls(
            request_id=request_id or str(uuid.uuid4()),
            actor_telegram_id=actor,
            role=role,
            method=request.method,
            path=request.path,
            remote_ip=_client_ip(request),
        )

    @property
    def duration_ms(self) -> float:
        return round((time.perf_counter() - self.started_at) * 1000, 2)

    def log_fields(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "actor_telegram_id": self.actor_telegram_id,
            "role": self.role,
            "method": self.method,
            "path": self.path,
            "remote_ip": self.remote_ip,
            "duration_ms": self.duration_ms,
            "audit_id": self.audit_id,
        }


def _client_ip(request: web.Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    peer = request.transport.get_extra_info("peername") if request.transport else None
    if peer:
        return str(peer[0])
    return "unknown"


def _extract_actor(request: web.Request) -> int | None:
    header = request.headers.get("X-Actor-Telegram-Id", "").strip()
    if header:
        try:
            return int(header)
        except ValueError:
            pass

    query = request.query.get("actor_telegram_id")
    if query:
        try:
            return int(query)
        except ValueError:
            pass

    jwt = request.get("jwt")
    if isinstance(jwt, dict):
        for key in ("telegram_id", "sub", "user_id"):
            raw = jwt.get(key)
            if raw is not None:
                try:
                    return int(raw)
                except (TypeError, ValueError):
                    continue
    return None
