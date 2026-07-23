"""AI drafting assistant — NL drafting, suggestions, summaries."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


DRAFT_KINDS = (
    "draft",
    "suggest_clause",
    "optimize",
    "plain_language",
    "summary",
    "negotiate",
)


class AIDraftingAssistant:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def _save(self, *, kind: str, prompt: str, output: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
        if not prompt:
            raise ValidationError("prompt required")
        did = _id("di_draft")
        return self.store.di_drafts.save(
            did,
            {
                "draft_id": did,
                "kind": kind,
                "prompt": prompt,
                "output": output,
                "meta": meta or {},
                "at": _now(),
            },
        )

    def draft(self, *, prompt: str, contract_type: str = "custom") -> dict[str, Any]:
        return self._save(
            kind="draft",
            prompt=prompt,
            output=f"Draft {contract_type} agreement based on: {prompt}",
            meta={"contract_type": contract_type},
        )

    def suggest_clause(self, *, prompt: str, kind: str = "general") -> dict[str, Any]:
        return self._save(
            kind="suggest_clause",
            prompt=prompt,
            output=f"Suggested {kind} clause addressing: {prompt}",
            meta={"clause_kind": kind},
        )

    def optimize_language(self, *, prompt: str) -> dict[str, Any]:
        return self._save(
            kind="optimize",
            prompt=prompt,
            output=f"Optimized legal language: {prompt}",
        )

    def plain_language(self, *, prompt: str) -> dict[str, Any]:
        return self._save(
            kind="plain_language",
            prompt=prompt,
            output=f"Plain-language explanation: {prompt}",
        )

    def summarize(self, *, prompt: str) -> dict[str, Any]:
        return self._save(
            kind="summary",
            prompt=prompt,
            output=f"Document summary: {prompt[:200]}",
        )

    def negotiate(self, *, prompt: str) -> dict[str, Any]:
        return self._save(
            kind="negotiate",
            prompt=prompt,
            output="Negotiation recommendations: seek mutual indemnity; clarify SLAs; extend notice period.",
            meta={"recommendations": ["mutual indemnity", "SLA metrics", "notice period"]},
        )

    def status(self) -> dict[str, Any]:
        return {"drafts": self.store.di_drafts.count(), "kinds": list(DRAFT_KINDS)}
