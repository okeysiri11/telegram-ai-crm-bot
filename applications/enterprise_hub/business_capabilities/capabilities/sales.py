"""Domain capability seeds — sales (Sprint 20.11)."""

from __future__ import annotations

from typing import Any


def definitions() -> list[dict[str, Any]]:
    return [
        {"key": "sales", "name": "Sales", "domain": "sales", "parent_key": 'operations', "maturity_level": 3, "owner": "capability-owner@sales", "description": "Sales business capability", "strategic_goal": "Strengthen Sales", "kpi": ["cycle_time", "cost", "sla"], "processes": ["sales.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:sales"},
        {"key": "sales.pipeline", "name": "Sales Pipeline", "domain": "sales", "parent_key": 'sales', "maturity_level": 3, "owner": "capability-owner@sales", "description": "Sales Pipeline business capability", "strategic_goal": "Strengthen Sales Pipeline", "kpi": ["cycle_time", "cost", "sla"], "processes": ["sales.pipeline.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:sales.pipeline"},
        {"key": "sales.quoting", "name": "Quoting", "domain": "sales", "parent_key": 'sales', "maturity_level": 2, "owner": "capability-owner@sales", "description": "Quoting business capability", "strategic_goal": "Strengthen Quoting", "kpi": ["cycle_time", "cost", "sla"], "processes": ["sales.quoting.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:sales.quoting"},
    ]

