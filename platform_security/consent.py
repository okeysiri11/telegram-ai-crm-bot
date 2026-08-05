"""AI Production Center consent-record gate — Sprint 30.0 (TD-46).

Hard prerequisite before any avatar/voice-likeness generation provider work.
No generation providers are wired here — only the governance gate.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


class ConsentRequiredError(PermissionError):
    """Raised when likeness generation is attempted without a valid consent record."""


@dataclass
class ConsentRecord:
    consent_id: str
    subject_id: str
    purpose: str  # avatar | voice | likeness
    granted_by: str
    granted_at: float
    expires_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    revoked: bool = False


class ConsentRegistry:
    def __init__(self) -> None:
        self._records: dict[str, ConsentRecord] = {}

    def clear(self) -> None:
        self._records.clear()

    def grant(
        self,
        *,
        subject_id: str,
        purpose: str,
        granted_by: str,
        expires_at: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConsentRecord:
        record = ConsentRecord(
            consent_id=str(uuid.uuid4()),
            subject_id=subject_id,
            purpose=purpose,
            granted_by=granted_by,
            granted_at=time.time(),
            expires_at=expires_at,
            metadata=metadata or {},
        )
        self._records[record.consent_id] = record
        return record

    def revoke(self, consent_id: str) -> None:
        record = self._records.get(consent_id)
        if record:
            record.revoked = True

    def find_valid(self, *, subject_id: str, purpose: str) -> ConsentRecord | None:
        now = time.time()
        for record in self._records.values():
            if record.subject_id != subject_id or record.purpose != purpose:
                continue
            if record.revoked:
                continue
            if record.expires_at is not None and record.expires_at < now:
                continue
            return record
        return None

    def require(self, *, subject_id: str, purpose: str) -> ConsentRecord:
        record = self.find_valid(subject_id=subject_id, purpose=purpose)
        if record is None:
            raise ConsentRequiredError(
                f"Consent required for purpose={purpose} subject={subject_id} "
                "(TD-46 — build consent before avatar/voice providers)"
            )
        return record

    def list_for_subject(self, subject_id: str) -> list[ConsentRecord]:
        return [r for r in self._records.values() if r.subject_id == subject_id]


consent_registry = ConsentRegistry()


def require_likeness_consent(*, subject_id: str, purpose: str) -> ConsentRecord:
    """Call this before any avatar/voice generation path."""
    return consent_registry.require(subject_id=subject_id, purpose=purpose)
