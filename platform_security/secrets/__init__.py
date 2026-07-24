"""Secrets management — Sprint 21.4."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import hashlib
import uuid

from platform_security.models import SECRET_KINDS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SecretsManager:
    def __init__(self) -> None:
        self._secrets: dict[str, dict[str, Any]] = {}

    def put(self, *, name: str, kind: str, value: str) -> dict[str, Any]:
        if kind not in SECRET_KINDS:
            raise ValueError(f"invalid secret kind: {kind}")
        if not name or not value:
            raise ValueError("name and value are required")
        sid = f"sec_{uuid.uuid4().hex[:12]}"
        record = {
            "secret_id": sid,
            "name": name,
            "kind": kind,
            "fingerprint": hashlib.sha256(value.encode()).hexdigest()[:16],
            "stored_at": _now(),
        }
        self._secrets[name] = record
        return record

    def get_fingerprint(self, name: str) -> dict[str, Any]:
        item = self._secrets.get(name)
        if not item:
            raise KeyError(f"secret not found: {name}")
        return item

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._secrets.values())

    def status(self) -> dict[str, Any]:
        return {"secrets": len(self._secrets), "kinds": list(SECRET_KINDS)}
