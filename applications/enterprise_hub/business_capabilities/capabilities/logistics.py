"""Domain capability seeds — logistics (Sprint 20.11)."""

from __future__ import annotations

from typing import Any


def definitions() -> list[dict[str, Any]]:
    return [
        {"key": "logistics", "name": "Logistics", "domain": "logistics", "parent_key": 'operations', "maturity_level": 3, "owner": "capability-owner@logistics", "description": "Logistics business capability", "strategic_goal": "Strengthen Logistics", "kpi": ["cycle_time", "cost", "sla"], "processes": ["logistics.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:logistics"},
        {"key": "logistics.fleet", "name": "Fleet Coordination", "domain": "logistics", "parent_key": 'logistics', "maturity_level": 2, "owner": "capability-owner@logistics", "description": "Fleet Coordination business capability", "strategic_goal": "Strengthen Fleet Coordination", "kpi": ["cycle_time", "cost", "sla"], "processes": ["logistics.fleet.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:logistics.fleet"},
        {"key": "logistics.dispatch", "name": "Dispatch", "domain": "logistics", "parent_key": 'logistics', "maturity_level": 3, "owner": "capability-owner@logistics", "description": "Dispatch business capability", "strategic_goal": "Strengthen Dispatch", "kpi": ["cycle_time", "cost", "sla"], "processes": ["logistics.dispatch.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:logistics.dispatch"},
    ]

