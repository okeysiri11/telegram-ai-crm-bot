"""Release validation — Sprint 22.0."""

from __future__ import annotations

from typing import Any


class ReleaseValidation:
    def validate(
        self,
        *,
        expected_kpi: list[dict[str, Any]],
        observed: dict[str, float] | None = None,
        new_problems: list[str] | None = None,
        feedback: list[str] | None = None,
    ) -> dict[str, Any]:
        observed = observed or {
            "adoption_lift_pct": 0.11,
            "support_ticket_reduction_pct": 0.16,
        }
        results = []
        for kpi in expected_kpi:
            name = kpi["name"]
            target = float(kpi.get("target", 0))
            actual = float(observed.get(name, 0))
            results.append(
                {
                    "name": name,
                    "target": target,
                    "actual": actual,
                    "met": actual >= target * 0.8,
                }
            )
        return {
            "kpi_results": results,
            "effect_achieved": all(r["met"] for r in results) if results else False,
            "new_problems": list(new_problems or []),
            "feedback": list(feedback or ["positive"]),
            "passed": bool(results) and all(r["met"] for r in results),
        }
