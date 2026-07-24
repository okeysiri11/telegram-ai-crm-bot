"""Domain capability seeds — healthcare (Sprint 20.11)."""

from __future__ import annotations

from typing import Any


def definitions() -> list[dict[str, Any]]:
    return [
        {"key": "healthcare", "name": "Healthcare", "domain": "healthcare", "parent_key": 'operations', "maturity_level": 2, "owner": "capability-owner@healthcare", "description": "Healthcare business capability", "strategic_goal": "Strengthen Healthcare", "kpi": ["cycle_time", "cost", "sla"], "processes": ["healthcare.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:healthcare"},
        {"key": "healthcare.clinical", "name": "Clinical Operations", "domain": "healthcare", "parent_key": 'healthcare', "maturity_level": 2, "owner": "capability-owner@healthcare", "description": "Clinical Operations business capability", "strategic_goal": "Strengthen Clinical Operations", "kpi": ["cycle_time", "cost", "sla"], "processes": ["healthcare.clinical.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:healthcare.clinical"},
    ]

