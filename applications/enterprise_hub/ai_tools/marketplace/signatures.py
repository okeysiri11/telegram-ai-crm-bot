"""Digital signatures for marketplace packages."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PackageSignatures:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def sign(self, *, package_id: str, signer: str = "bidex") -> dict[str, Any]:
        pkg = self.store.ats_packages.get(package_id)
        if not pkg:
            raise ValidationError(f"package not found: {package_id}")
        digest = hashlib.sha256(f"{package_id}:{pkg.get('version')}:{signer}".encode()).hexdigest()
        sid = _id("ats_sig")
        return self.store.ats_signatures.save(
            sid,
            {
                "signature_id": sid,
                "package_id": package_id,
                "signer": signer,
                "digest": digest,
                "valid": True,
                "at": _now(),
            },
        )

    def verify(self, *, signature_id: str) -> dict[str, Any]:
        from applications.enterprise_hub.shared.exceptions import NotFoundError

        sig = self.store.ats_signatures.get(signature_id)
        if not sig:
            raise NotFoundError(f"signature not found: {signature_id}")
        return {"signature_id": signature_id, "valid": bool(sig.get("valid")), "digest": sig.get("digest")}
