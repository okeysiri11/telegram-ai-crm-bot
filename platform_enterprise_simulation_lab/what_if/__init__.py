"""What-if Analysis — Sprint 24.4."""

from __future__ import annotations

from typing import Any

from platform_enterprise_simulation_lab.models import WHAT_IF_QUESTIONS


class WhatIfAnalysis:
    EFFECTS = {
        "increase_prices": {"sales": -0.05, "finance": 0.08, "marketing": -0.02},
        "open_branch": {"finance": -0.12, "sales": 0.15, "workforce": 0.2, "branch_load": -0.1},
        "change_schedule": {"schedule": 0.05, "workforce": -0.03, "sales": 0.04},
        "increase_ad_budget": {"marketing": 0.2, "sales": 0.1, "finance": -0.08},
        "hire_staff": {"workforce": 0.25, "finance": -0.1, "branch_load": -0.15, "sales": 0.06},
        "change_loyalty": {"sales": 0.07, "marketing": 0.05, "finance": -0.03},
    }

    def analyze(self, *, question: str, intensity: float = 1.0) -> dict[str, Any]:
        question = (question or "").lower()
        if question not in WHAT_IF_QUESTIONS:
            raise ValueError(f"unsupported what-if: {question}")
        intensity = float(intensity)
        effects = {k: round(v * intensity, 4) for k, v in self.EFFECTS[question].items()}
        return {
            "question": question,
            "intensity": intensity,
            "domain_deltas": effects,
            "sandbox": True,
            "ai_may_act": False,
        }
