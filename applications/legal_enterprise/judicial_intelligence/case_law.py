"""Case law intelligence — classification, citations, conflicts."""

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


class CaseLawIntelligence:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.case_classes = list(DEFAULT_CONFIG.ji_case_classes)
        self.topics = list(DEFAULT_CONFIG.ji_topics)

    def classify_case(
        self, *, decision_id: str, label: str, confidence: float = 0.85
    ) -> dict[str, Any]:
        if not decision_id:
            raise ValidationError("decision_id required")
        if label not in self.case_classes:
            raise ValidationError(f"label must be one of {self.case_classes}")
        cid = _id("ji_cls")
        return self.store.ji_classifications.save(
            cid,
            {
                "classification_id": cid,
                "decision_id": decision_id,
                "kind": "case",
                "label": label,
                "confidence": max(0.0, min(1.0, float(confidence))),
                "at": _now(),
            },
        )

    def classify_topic(
        self, *, decision_id: str, label: str, confidence: float = 0.8
    ) -> dict[str, Any]:
        if not decision_id:
            raise ValidationError("decision_id required")
        if label not in self.topics:
            raise ValidationError(f"topic must be one of {self.topics}")
        cid = _id("ji_top")
        return self.store.ji_classifications.save(
            cid,
            {
                "classification_id": cid,
                "decision_id": decision_id,
                "kind": "topic",
                "label": label,
                "confidence": max(0.0, min(1.0, float(confidence))),
                "at": _now(),
            },
        )

    def relate(
        self,
        *,
        from_decision_id: str,
        to_decision_id: str,
        relation: str = "related",
        detail: str = "",
    ) -> dict[str, Any]:
        if not from_decision_id or not to_decision_id:
            raise ValidationError("from_decision_id and to_decision_id required")
        rid = _id("ji_rel")
        return self.store.ji_relationships.save(
            rid,
            {
                "relationship_id": rid,
                "from_decision_id": from_decision_id,
                "to_decision_id": to_decision_id,
                "relation": relation,
                "detail": detail,
                "at": _now(),
            },
        )

    def cite_article(self, *, decision_id: str, article_ref: str, detail: str = "") -> dict[str, Any]:
        if not decision_id or not article_ref:
            raise ValidationError("decision_id and article_ref required")
        cid = _id("ji_cite_a")
        return self.store.ji_citations.save(
            cid,
            {
                "citation_id": cid,
                "decision_id": decision_id,
                "citation_type": "article",
                "reference": article_ref,
                "detail": detail,
                "at": _now(),
            },
        )

    def cite_decision(
        self, *, decision_id: str, referenced_decision_id: str, detail: str = ""
    ) -> dict[str, Any]:
        if not decision_id or not referenced_decision_id:
            raise ValidationError("decision_id and referenced_decision_id required")
        cid = _id("ji_cite_d")
        row = self.store.ji_citations.save(
            cid,
            {
                "citation_id": cid,
                "decision_id": decision_id,
                "citation_type": "decision",
                "reference": referenced_decision_id,
                "detail": detail,
                "at": _now(),
            },
        )
        self.relate(
            from_decision_id=decision_id,
            to_decision_id=referenced_decision_id,
            relation="cites",
            detail=detail,
        )
        return row

    def detect_conflict(
        self,
        *,
        decision_a: str,
        decision_b: str,
        severity: str = "medium",
        detail: str = "",
    ) -> dict[str, Any]:
        if not decision_a or not decision_b:
            raise ValidationError("decision_a and decision_b required")
        cid = _id("ji_conf")
        row = {
            "conflict_id": cid,
            "decision_a": decision_a,
            "decision_b": decision_b,
            "severity": severity,
            "detail": detail or "conflicting judicial outcomes",
            "at": _now(),
        }
        self.store.ji_conflicts.save(cid, row)
        self.relate(
            from_decision_id=decision_a,
            to_decision_id=decision_b,
            relation="conflicts_with",
            detail=detail or severity,
        )
        return row

    def status(self) -> dict[str, Any]:
        return {
            "classifications": self.store.ji_classifications.count(),
            "relationships": self.store.ji_relationships.count(),
            "citations": self.store.ji_citations.count(),
            "conflicts": self.store.ji_conflicts.count(),
        }
