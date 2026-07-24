"""Domain capability seeds — procurement (Sprint 20.11)."""

from __future__ import annotations

from typing import Any


def definitions() -> list[dict[str, Any]]:
    return [
        {"key": "procurement", "name": "Procurement", "domain": "procurement", "parent_key": 'operations', "maturity_level": 3, "owner": "capability-owner@procurement", "description": "Procurement business capability", "strategic_goal": "Strengthen Procurement", "kpi": ["cycle_time", "cost", "sla"], "processes": ["procurement.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:procurement"},
        {"key": "procurement.sourcing", "name": "Sourcing", "domain": "procurement", "parent_key": 'procurement', "maturity_level": 2, "owner": "capability-owner@procurement", "description": "Sourcing business capability", "strategic_goal": "Strengthen Sourcing", "kpi": ["cycle_time", "cost", "sla"], "processes": ["procurement.sourcing.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:procurement.sourcing"},
        {"key": "procurement.po", "name": "Purchase Orders", "domain": "procurement", "parent_key": 'procurement', "maturity_level": 3, "owner": "capability-owner@procurement", "description": "Purchase Orders business capability", "strategic_goal": "Strengthen Purchase Orders", "kpi": ["cycle_time", "cost", "sla"], "processes": ["procurement.po.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:procurement.po"},
    ]

