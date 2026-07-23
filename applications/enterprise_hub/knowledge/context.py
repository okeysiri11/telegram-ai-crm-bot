"""Cross-platform context — automotive, agro, port, crypto, legal, finance, unified."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CrossPlatformContext:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.contexts = list(DEFAULT_CONFIG.kg_context_types)

    def attach(
        self,
        *,
        context_type: str,
        subject: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ct = context_type.lower().strip()
        if ct not in self.contexts:
            raise ValidationError(f"context_type must be one of {self.contexts}")
        if not subject:
            raise ValidationError("subject required")
        cid = _id("kg_ctx")
        return self.store.kg_contexts.save(
            cid,
            {
                "context_id": cid,
                "context_type": ct,
                "subject": subject,
                "payload": payload or {},
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "contexts": self.store.kg_contexts.count(),
            "types": self.contexts,
        }
