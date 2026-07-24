"""Simulation Engine — Sprint 24.4."""

from __future__ import annotations

from typing import Any

from platform_enterprise_simulation_lab.models import SIMULATION_DOMAINS


class SimulationEngine:
    def run(self, *, domain: str, baseline: float = 100.0, delta_pct: float = 0.0) -> dict[str, Any]:
        domain = (domain or "").lower()
        if domain not in SIMULATION_DOMAINS:
            raise ValueError(f"unsupported domain: {domain}")
        baseline = float(baseline)
        delta_pct = float(delta_pct)
        projected = round(baseline * (1 + delta_pct), 2)
        return {
            "domain": domain,
            "baseline": baseline,
            "delta_pct": delta_pct,
            "projected": projected,
            "sandbox": True,
            "mutates_production": False,
        }

    def run_bundle(self, *, changes: dict[str, float] | None = None, baselines: dict[str, float] | None = None) -> dict[str, Any]:
        changes = dict(changes or {})
        baselines = dict(baselines or {})
        results = []
        for domain in SIMULATION_DOMAINS:
            results.append(
                self.run(
                    domain=domain,
                    baseline=float(baselines.get(domain, 100.0)),
                    delta_pct=float(changes.get(domain, 0.0)),
                )
            )
        return {"results": results, "sandbox": True, "domains": list(SIMULATION_DOMAINS)}
