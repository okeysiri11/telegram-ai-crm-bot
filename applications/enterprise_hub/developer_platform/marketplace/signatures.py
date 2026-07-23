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



import hashlib


class MarketplaceSignatures:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def sign(self, *, package_id: str, version: str, signer: str = "bidex") -> dict[str, Any]:
        digest = hashlib.sha256(f"{package_id}:{version}:{signer}".encode()).hexdigest()
        sid = _id("sdp_sig")
        return self.store.sdp_signatures.save(
            sid,
            {
                "signature_id": sid,
                "package_id": package_id,
                "version": version,
                "signer": signer,
                "digest": digest,
                "valid": True,
                "at": _now(),
            },
        )

    def verify(self, *, signature_id: str) -> dict[str, Any]:
        sig = self.store.sdp_signatures.get(signature_id)
        if not sig:
            raise NotFoundError(f"signature not found: {signature_id}")
        return {"signature_id": signature_id, "valid": bool(sig.get("valid")), "digest": sig.get("digest")}

    def status(self) -> dict[str, Any]:
        return {"signatures": len(self.store.sdp_signatures.list_all())}
