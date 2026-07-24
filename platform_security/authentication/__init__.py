"""Identity & authentication — Sprint 21.4."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import hashlib
import uuid

from platform_security.models import AUTH_METHODS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class IdentitySecurity:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    def methods(self) -> list[str]:
        return list(AUTH_METHODS)

    def authenticate(
        self,
        *,
        method: str,
        principal: str,
        secret: str = "",
        mfa_code: str | None = None,
    ) -> dict[str, Any]:
        if method not in AUTH_METHODS:
            raise ValueError(f"unsupported auth method: {method}")
        if not principal:
            raise ValueError("principal is required")
        if method == "mfa" and not mfa_code:
            raise ValueError("mfa_code is required")
        token = hashlib.sha256(f"{principal}:{secret}:{uuid.uuid4().hex}".encode()).hexdigest()[:32]
        refresh = hashlib.sha256(f"refresh:{token}".encode()).hexdigest()[:32]
        sid = f"sess_{uuid.uuid4().hex[:12]}"
        record = {
            "session_id": sid,
            "method": method,
            "principal": principal,
            "access_token": token,
            "refresh_token": refresh if method in ("oauth2", "oidc", "jwt", "refresh_token") else None,
            "mfa_verified": bool(mfa_code) if method == "mfa" else method != "mfa",
            "authenticated_at": _now(),
        }
        self._sessions[sid] = record
        return record

    def status(self) -> dict[str, Any]:
        return {"sessions": len(self._sessions), "methods": self.methods()}
