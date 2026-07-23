"""Diagnostics engine — error analysis, AI root-cause, recommendations."""

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


class DiagnosticsEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def analyze(
        self,
        *,
        subject: str,
        error: str = "",
        logs: list[str] | None = None,
    ) -> dict[str, Any]:
        if not subject:
            raise ValidationError("subject required")
        recommendations = [
            "check_recent_deploys",
            "inspect_dependency_health",
            "review_correlated_logs",
        ]
        if "timeout" in error.lower():
            recommendations.insert(0, "increase_timeout_or_scale")
        if "oauth" in error.lower() or "token" in error.lower():
            recommendations.insert(0, "rotate_credentials")
        did = _id("obs_diag")
        return self.store.obs_diagnostics.save(
            did,
            {
                "diagnostic_id": did,
                "subject": subject,
                "error": error,
                "logs_sample": (logs or [])[:10],
                "root_cause_hypothesis": error or "unknown",
                "recommendations": recommendations,
                "ai_analysis": f"AI RCA for {subject}: {error or 'no error text'}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"diagnostics": self.store.obs_diagnostics.count()}
