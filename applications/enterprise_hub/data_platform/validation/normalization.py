"""Normalization helpers for master data values."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class Normalizer:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def normalize(self, *, value: str, kind: str = "text") -> dict[str, Any]:
        if value is None:
            raise ValidationError("value required")
        raw = str(value)
        kind_n = kind.lower().strip()
        if kind_n == "email":
            out = raw.strip().lower()
        elif kind_n == "phone":
            out = "".join(ch for ch in raw if ch.isdigit() or ch == "+")
        elif kind_n == "name":
            out = " ".join(raw.strip().split()).title()
        else:
            out = raw.strip()
        nid = _id("edp_norm")
        return self.store.edp_normalizations.save(
            nid,
            {
                "normalization_id": nid,
                "kind": kind_n,
                "input": raw,
                "output": out,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"normalizations": self.store.edp_normalizations.count()}
