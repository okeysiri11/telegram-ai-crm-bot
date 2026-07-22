from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.firmware.repository import FirmwareRepository, firmware_repository
from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


class FirmwareSigning:
    """Engineering signing records for release integrity (not a PKI substitute)."""

    def __init__(self, store: DroneStore | None = None, repository: FirmwareRepository | None = None) -> None:
        self.store = store or drone_store
        self.repository = repository or firmware_repository

    def sign_artifact(self, artifact_id: str, signer: str = "drone-engineering") -> dict[str, Any]:
        art = self.repository.get(artifact_id)
        sid = f"sig_{uuid.uuid4().hex[:12]}"
        payload = f"{art.get('sha256')}:{signer}:{sid}"
        signature = hashlib.sha256(payload.encode()).hexdigest()
        record = {
            "signature_id": sid,
            "artifact_id": artifact_id,
            "signer": signer,
            "algorithm": "sha256-hmac-sim",
            "signature": signature,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.firmware_signatures.save(sid, record)
        return record

    def verify(self, signature_id: str) -> dict[str, Any]:
        sig = self.store.firmware_signatures.get(signature_id)
        if sig is None:
            raise NotFoundError("firmware_signature", signature_id)
        art = self.repository.get(sig["artifact_id"])
        payload = f"{art.get('sha256')}:{sig['signer']}:{sig['signature_id']}"
        expected = hashlib.sha256(payload.encode()).hexdigest()
        ok = expected == sig.get("signature")
        if not ok:
            raise ValidationError("Signature verification failed")
        return {"valid": True, "signature_id": signature_id, "artifact_id": sig["artifact_id"]}


firmware_signing = FirmwareSigning()
