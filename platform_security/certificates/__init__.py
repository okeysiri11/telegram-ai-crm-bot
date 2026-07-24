"""Certificate inventory — Sprint 21.4."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CertificateStore:
    def __init__(self) -> None:
        self._certs: list[dict[str, Any]] = []

    def issue(self, *, subject: str, days: int = 365) -> dict[str, Any]:
        exp = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
        cert = {
            "cert_id": f"crt_{uuid.uuid4().hex[:12]}",
            "subject": subject,
            "algorithm": "ed25519",
            "expires_at": exp,
            "issued_at": _now(),
        }
        self._certs.append(cert)
        return cert

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._certs)
