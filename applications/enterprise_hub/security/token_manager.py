"""Token manager — access/refresh/api/PAT, rotation, revocation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.security.models import TOKEN_TYPES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TokenManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def issue(
        self,
        *,
        identity_id: str,
        token_type: str = "access",
    ) -> dict[str, Any]:
        tt = token_type.lower().strip()
        if tt not in TOKEN_TYPES:
            raise ValidationError(f"token_type must be one of {list(TOKEN_TYPES)}")
        if self.store.isam_identities.get(identity_id) is None:
            raise NotFoundError(f"identity not found: {identity_id}")
        tid = _id("isam_tok")
        return self.store.isam_tokens.save(
            tid,
            {
                "token_id": tid,
                "identity_id": identity_id,
                "token_type": tt,
                "value": f"{tt}_{uuid.uuid4().hex}",
                "status": "active",
                "rotated": False,
                "at": _now(),
            },
        )

    def rotate(self, *, token_id: str) -> dict[str, Any]:
        tok = self.store.isam_tokens.get(token_id)
        if tok is None:
            raise NotFoundError(f"token not found: {token_id}")
        tok["rotated"] = True
        tok["value"] = f"{tok['token_type']}_{uuid.uuid4().hex}"
        tok["at"] = _now()
        return self.store.isam_tokens.save(token_id, tok)

    def revoke(self, *, token_id: str) -> dict[str, Any]:
        tok = self.store.isam_tokens.get(token_id)
        if tok is None:
            raise NotFoundError(f"token not found: {token_id}")
        tok["status"] = "revoked"
        tok["at"] = _now()
        return self.store.isam_tokens.save(token_id, tok)

    def status(self) -> dict[str, Any]:
        return {"tokens": self.store.isam_tokens.count(), "types": list(TOKEN_TYPES)}
