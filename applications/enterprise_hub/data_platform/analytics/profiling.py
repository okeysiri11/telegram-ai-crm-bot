"""Data analytics — profiling, statistics, quality dashboard."""

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


class DataProfiler:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def profile(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        for item in self.store.edp_entities.list_all():
            if isinstance(item, dict):
                et = item.get("entity_type", "unknown")
                by_type[et] = by_type.get(et, 0) + 1
        pid = _id("edp_prof")
        return self.store.edp_profiles.save(
            pid,
            {
                "profile_id": pid,
                "by_type": by_type,
                "total": self.store.edp_entities.count(),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"profiles": self.store.edp_profiles.count()}


class DataStatistics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def summarize(self) -> dict[str, Any]:
        sid = _id("edp_stat")
        return self.store.edp_stats.save(
            sid,
            {
                "stats_id": sid,
                "entities": self.store.edp_entities.count(),
                "relationships": self.store.edp_relationships.count(),
                "catalog": self.store.edp_catalog.count(),
                "quality_runs": self.store.edp_quality.count(),
                "versions": self.store.edp_versions.count(),
                "lineage": self.store.edp_lineage.count(),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"summaries": self.store.edp_stats.count()}


class AIDataAssistant:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def assist(self, *, action: str, subject: str, detail: str = "") -> dict[str, Any]:
        act = action.lower().strip()
        allowed = (
            "find_duplicates",
            "merge_records",
            "fix_errors",
            "suggest_normalization",
            "detect_anomalies",
            "score_quality",
        )
        if act not in allowed:
            raise ValidationError(f"action must be one of {list(allowed)}")
        if not subject:
            raise ValidationError("subject required")
        aid = _id("edp_ai")
        return self.store.edp_ai_assists.save(
            aid,
            {
                "assist_id": aid,
                "action": act,
                "subject": subject,
                "detail": detail,
                "suggestion": f"{act}:{subject}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"assists": self.store.edp_ai_assists.count()}


class QualityDashboard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.types = list(DEFAULT_CONFIG.edp_dashboard_types)

    def render(self, *, dashboard_type: str) -> dict[str, Any]:
        dt = dashboard_type.lower().strip()
        if dt not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "quality": {
                "runs": self.store.edp_quality.count(),
                "duplicates": self.store.edp_duplicates.count(),
                "consistency": self.store.edp_consistency.count(),
            },
            "catalog": {
                "entries": self.store.edp_catalog.count(),
                "schemas": self.store.edp_metadata.count(),
            },
            "governance": {
                "policies": self.store.edp_governance.count(),
                "audit": self.store.edp_audit.count(),
            },
            "lineage": {
                "entries": self.store.edp_lineage.count(),
                "versions": self.store.edp_versions.count(),
                "rollbacks": self.store.edp_rollbacks.count(),
            },
            "analytics": {
                "profiles": self.store.edp_profiles.count(),
                "stats": self.store.edp_stats.count(),
                "ai_assists": self.store.edp_ai_assists.count(),
                "entities": self.store.edp_entities.count(),
            },
        }.get(dt, {})
        did = _id("edp_dash")
        return self.store.edp_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dt,
                "metrics": metrics,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.edp_dashboards.count(), "types": self.types}
