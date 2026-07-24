"""Domain capability seeds — manufacturing (Sprint 20.11)."""

from __future__ import annotations

from typing import Any


def definitions() -> list[dict[str, Any]]:
    return [
        {"key": "manufacturing", "name": "Manufacturing", "domain": "manufacturing", "parent_key": 'operations', "maturity_level": 3, "owner": "capability-owner@manufacturing", "description": "Manufacturing business capability", "strategic_goal": "Strengthen Manufacturing", "kpi": ["cycle_time", "cost", "sla"], "processes": ["manufacturing.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:manufacturing"},
        {"key": "manufacturing.planning", "name": "Production Planning", "domain": "manufacturing", "parent_key": 'manufacturing', "maturity_level": 3, "owner": "capability-owner@manufacturing", "description": "Production Planning business capability", "strategic_goal": "Strengthen Production Planning", "kpi": ["cycle_time", "cost", "sla"], "processes": ["manufacturing.planning.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:manufacturing.planning"},
        {"key": "manufacturing.quality", "name": "Quality Control", "domain": "manufacturing", "parent_key": 'manufacturing', "maturity_level": 2, "owner": "capability-owner@manufacturing", "description": "Quality Control business capability", "strategic_goal": "Strengthen Quality Control", "kpi": ["cycle_time", "cost", "sla"], "processes": ["manufacturing.quality.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:manufacturing.quality"},
    ]

