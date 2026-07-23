"""Regulatory intelligence — classification engines."""

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


CLASSIFIERS = ("law", "industry", "topic", "jurisdiction", "authority")


class RegulatoryIntelligence:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.law_classes = list(DEFAULT_CONFIG.li_law_classes)
        self.industries = list(DEFAULT_CONFIG.li_industries)
        self.topics = list(DEFAULT_CONFIG.li_topics)

    def classify(
        self,
        *,
        document_id: str,
        classifier: str,
        label: str,
        confidence: float = 0.8,
    ) -> dict[str, Any]:
        if not document_id:
            raise ValidationError("document_id required")
        kind = classifier.lower().strip()
        if kind not in CLASSIFIERS:
            raise ValidationError(f"classifier must be one of {list(CLASSIFIERS)}")
        if not label:
            raise ValidationError("label required")
        if kind == "law" and label not in self.law_classes:
            raise ValidationError(f"law label must be one of {self.law_classes}")
        if kind == "industry" and label not in self.industries:
            raise ValidationError(f"industry label must be one of {self.industries}")
        if kind == "topic" and label not in self.topics:
            raise ValidationError(f"topic label must be one of {self.topics}")
        conf = max(0.0, min(1.0, float(confidence)))
        cid = _id("li_cls")
        return self.store.li_classifications.save(
            cid,
            {
                "classification_id": cid,
                "document_id": document_id,
                "classifier": kind,
                "label": label,
                "confidence": conf,
                "at": _now(),
            },
        )

    def classify_law(self, *, document_id: str, label: str, confidence: float = 0.85) -> dict[str, Any]:
        return self.classify(document_id=document_id, classifier="law", label=label, confidence=confidence)

    def classify_industry(self, *, document_id: str, label: str, confidence: float = 0.8) -> dict[str, Any]:
        return self.classify(document_id=document_id, classifier="industry", label=label, confidence=confidence)

    def classify_topic(self, *, document_id: str, label: str, confidence: float = 0.8) -> dict[str, Any]:
        return self.classify(document_id=document_id, classifier="topic", label=label, confidence=confidence)

    def classify_jurisdiction(self, *, document_id: str, label: str, confidence: float = 0.9) -> dict[str, Any]:
        return self.classify(
            document_id=document_id, classifier="jurisdiction", label=label, confidence=confidence
        )

    def classify_authority(self, *, document_id: str, label: str, confidence: float = 0.9) -> dict[str, Any]:
        return self.classify(document_id=document_id, classifier="authority", label=label, confidence=confidence)

    def status(self) -> dict[str, Any]:
        return {"classifications": self.store.li_classifications.count(), "classifiers": list(CLASSIFIERS)}
