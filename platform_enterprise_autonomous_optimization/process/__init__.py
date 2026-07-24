"""Process Optimizer — Sprint 24.6."""

from __future__ import annotations

from typing import Any


class ProcessOptimizer:
    DOMAINS = ("workflow", "crm", "commerce", "marketing", "finance", "operations", "communications")

    def analyze(self, *, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        signals = dict(signals or {})
        findings = []
        if float(signals.get("redundant_steps", 0)) > 0:
            findings.append({"type": "redundant_actions", "count": signals["redundant_steps"]})
        if float(signals.get("repeated_ops", 0)) > 0:
            findings.append({"type": "repeated_operations", "count": signals["repeated_ops"]})
        if float(signals.get("bottleneck_ms", 0)) > 1000:
            findings.append({"type": "bottleneck", "ms": signals["bottleneck_ms"]})
        if float(signals.get("idle_pct", 0)) > 0.2:
            findings.append({"type": "idle_time", "pct": signals["idle_pct"]})
        if float(signals.get("delay_ms", 0)) > 500:
            findings.append({"type": "delays", "ms": signals["delay_ms"]})
        if float(signals.get("costly_processes", 0)) > 0:
            findings.append({"type": "expensive_processes", "count": signals["costly_processes"]})
        if not findings:
            findings.append({"type": "stable", "note": "no_critical_waste"})
        return {"domains": list(self.DOMAINS), "findings": findings, "category": "process"}
