"""MFA challenge helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.security.models import MFA_METHODS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def challenge_mfa(
    store: EnterpriseHubStore,
    *,
    method: str,
    subject: str,
    code: str = "",
) -> dict[str, Any]:
    m = method.lower().strip()
    if m not in MFA_METHODS:
        raise ValidationError(f"method must be one of {list(MFA_METHODS)}")
    if not subject:
        raise ValidationError("subject required")
    mid = _id("isam_mfa")
    return store.isam_mfa.save(
        mid,
        {
            "mfa_id": mid,
            "method": m,
            "subject": subject,
            "verified": True,
            "code_ref": code or "******",
            "at": _now(),
        },
    )
