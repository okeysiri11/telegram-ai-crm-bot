"""Explainability, alerts, dashboards, and knowledge."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

ALERT_TYPES = [
    "high_confidence",
    "risk",
    "regime_change",
    "whale",
    "liquidation",
    "volatility",
    "portfolio",
]
DASHBOARD_TYPES = ["ai_trader", "decision", "portfolio_intel", "executive", "alert"]
REGISTRY_TYPES = ["decision", "recommendation", "portfolio", "alert"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIExplainability:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def trace(self, *, decision_id: str, steps: list[str]) -> dict[str, Any]:
        if not steps:
            raise ValidationError("steps required")
        tid = _id("at_trace")
        return self.store.at_traces.save(
            tid,
            {"trace_id": tid, "decision_id": decision_id, "steps": steps, "at": _now()},
        )

    def evidence(self, *, decision_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
        eid = _id("at_evid")
        return self.store.at_evidence.save(
            eid,
            {"evidence_id": eid, "decision_id": decision_id, "evidence": evidence, "at": _now()},
        )

    def summarize(
        self,
        *,
        decision_id: str,
        indicators: str = "",
        news: str = "",
        onchain: str = "",
        risk: str = "",
        confidence_explanation: str = "",
    ) -> dict[str, Any]:
        sid = _id("at_sum")
        return self.store.at_explanations.save(
            sid,
            {
                "explanation_id": sid,
                "decision_id": decision_id,
                "indicators": indicators,
                "news": news,
                "onchain": onchain,
                "risk": risk,
                "confidence_explanation": confidence_explanation,
                "at": _now(),
            },
        )

    def report(self, *, decision_id: str, narrative: str) -> dict[str, Any]:
        if not narrative:
            raise ValidationError("narrative required")
        rid = _id("at_explrpt")
        return self.store.at_decision_reports.save(
            rid,
            {
                "report_id": rid,
                "decision_id": decision_id,
                "narrative": narrative,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "traces": self.store.at_traces.count(),
            "explanations": self.store.at_explanations.count(),
            "reports": self.store.at_decision_reports.count(),
        }


class AlertCenter:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.alert_types = list(ALERT_TYPES)

    def raise_alert(
        self,
        *,
        alert_type: str,
        symbol: str = "",
        severity: str = "info",
        message: str,
    ) -> dict[str, Any]:
        if alert_type not in ALERT_TYPES:
            raise ValidationError(f"alert_type must be one of {ALERT_TYPES}")
        if severity not in ("info", "warning", "critical"):
            raise ValidationError("severity must be info|warning|critical")
        if not message:
            raise ValidationError("message required")
        aid = _id("at_alrt")
        return self.store.at_alerts.save(
            aid,
            {
                "alert_id": aid,
                "alert_type": alert_type,
                "symbol": symbol.upper() if symbol else "",
                "severity": severity,
                "message": message,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"alerts": self.store.at_alerts.count(), "types": self.alert_types}


class AITraderDashboard:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "ai_trader") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "ai_trader": {
                "decisions": self.store.at_decisions.count(),
                "recommendations": self.store.at_recommendations.count(),
            },
            "decision": {
                "decisions": self.store.at_decisions.count(),
                "scenarios": self.store.at_scenarios.count(),
            },
            "portfolio_intel": {
                "health": self.store.at_port_health.count(),
                "drawdown": self.store.at_drawdown.count(),
            },
            "executive": {
                "overviews": self.store.at_market_overview.count(),
                "actions": self.store.at_exec_actions.count(),
            },
            "alert": {
                "alerts": self.store.at_alerts.count(),
            },
        }[dashboard_type]
        did = _id("at_dash")
        return self.store.at_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.at_dashboards.count(), "types": self.types}


class AITraderKnowledge:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("at_reg")
        return self.store.at_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"at:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.at_registries.count(), "types": self.types}
