"""Court decision repository — judgments, rulings, orders, opinions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


DECISION_TYPES = ("judgment", "ruling", "order", "opinion")

_TYPE_STORE = {
    "judgment": "ji_judgments",
    "ruling": "ji_rulings",
    "order": "ji_orders",
    "opinion": "ji_opinions",
}


class CourtDecisionRepository:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.ji_decision_types)

    def _bucket(self, decision_type: str) -> Any:
        attr = _TYPE_STORE.get(decision_type)
        if attr is None:
            raise ValidationError(f"decision_type must be one of {self.types}")
        return getattr(self.store, attr)

    def register(
        self,
        *,
        decision_type: str,
        title: str,
        decision_number: str = "",
        case_number: str = "",
        court_id: str = "",
        court_name: str = "",
        judge_id: str = "",
        judge_name: str = "",
        decided_on: str = "",
        outcome: str = "",
        summary: str = "",
        body: str = "",
        participants: list[str] | None = None,
        articles: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not title:
            raise ValidationError("title required")
        dt = decision_type.lower().strip()
        bucket = self._bucket(dt)
        did = _id(f"ji_{dt[:3]}")
        record = {
            "decision_id": did,
            "decision_type": dt,
            "title": title,
            "decision_number": decision_number or did,
            "case_number": case_number,
            "court_id": court_id,
            "court_name": court_name,
            "judge_id": judge_id,
            "judge_name": judge_name,
            "decided_on": decided_on,
            "outcome": outcome,
            "summary": summary,
            "body": body,
            "participants": participants or [],
            "articles": articles or [],
            "metadata": metadata or {},
            "version": "1.0",
            "created_at": _now(),
        }
        bucket.save(did, record)
        self.store.ji_decisions.save(did, record)
        self.record_version(decision_id=did, version="1.0", summary="initial registration")
        return record

    def register_judgment(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(decision_type="judgment", **kwargs)

    def register_ruling(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(decision_type="ruling", **kwargs)

    def register_order(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(decision_type="order", **kwargs)

    def register_opinion(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(decision_type="opinion", **kwargs)

    def record_version(
        self,
        *,
        decision_id: str,
        version: str,
        summary: str = "",
    ) -> dict[str, Any]:
        if not decision_id or not version:
            raise ValidationError("decision_id and version required")
        vid = _id("ji_ver")
        return self.store.ji_versions.save(
            vid,
            {
                "version_id": vid,
                "decision_id": decision_id,
                "version": version,
                "summary": summary,
                "recorded_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "decisions": self.store.ji_decisions.count(),
            "judgments": self.store.ji_judgments.count(),
            "rulings": self.store.ji_rulings.count(),
            "orders": self.store.ji_orders.count(),
            "opinions": self.store.ji_opinions.count(),
            "versions": self.store.ji_versions.count(),
        }
