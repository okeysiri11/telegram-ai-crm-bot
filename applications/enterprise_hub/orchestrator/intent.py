"""Intent understanding — NL detection, context, entities, classification, priority, confidence."""

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


class IntentUnderstanding:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.task_classes = list(DEFAULT_CONFIG.orch_task_classes)

    def detect(
        self,
        *,
        utterance: str,
        task_class: str = "operation",
        priority: str = "normal",
        confidence: float = 0.8,
        entities: list[str] | None = None,
        context: str = "",
    ) -> dict[str, Any]:
        if not utterance:
            raise ValidationError("utterance required")
        tc = task_class.lower().strip()
        if tc not in self.task_classes:
            raise ValidationError(f"task_class must be one of {self.task_classes}")
        iid = _id("orch_int")
        return self.store.orch_intents.save(
            iid,
            {
                "intent_id": iid,
                "utterance": utterance,
                "task_class": tc,
                "priority": priority,
                "confidence": max(0.0, min(1.0, float(confidence))),
                "entities": entities or [],
                "context": context,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "intents": self.store.orch_intents.count(),
            "task_classes": self.task_classes,
        }
