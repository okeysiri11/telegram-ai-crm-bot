"""Risk Intelligence — Sprint 24.3."""

from __future__ import annotations

from typing import Any

from platform_predictive_intelligence.models import RISK_TYPES


class RiskIntelligence:
    def assess(self, *, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        signals = dict(signals or {})
        scores = {
            "financial": float(signals.get("financial", 0.2)),
            "operational": float(signals.get("operational", 0.25)),
            "customer_loss": float(signals.get("customer_loss", 0.3)),
            "process_failure": float(signals.get("process_failure", 0.15)),
            "security": float(signals.get("security", 0.1)),
        }
        for k in RISK_TYPES:
            scores[k] = max(0.0, min(1.0, scores.get(k, 0.2)))
        overall = round(sum(scores.values()) / len(scores), 3)
        return {
            "risks": scores,
            "overall_risk": overall,
            "level": "high" if overall >= 0.7 else ("medium" if overall >= 0.4 else "low"),
            "early_warning": overall >= 0.4 or any(v >= 0.55 for v in scores.values()),
        }
