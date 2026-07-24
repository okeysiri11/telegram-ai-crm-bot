"""Domain capability seeds — construction (Sprint 20.11)."""

from __future__ import annotations

from typing import Any


def definitions() -> list[dict[str, Any]]:
    return [
        {"key": "construction", "name": "Construction", "domain": "construction", "parent_key": 'operations', "maturity_level": 2, "owner": "capability-owner@construction", "description": "Construction business capability", "strategic_goal": "Strengthen Construction", "kpi": ["cycle_time", "cost", "sla"], "processes": ["construction.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:construction"},
        {"key": "construction.sites", "name": "Site Management", "domain": "construction", "parent_key": 'construction', "maturity_level": 2, "owner": "capability-owner@construction", "description": "Site Management business capability", "strategic_goal": "Strengthen Site Management", "kpi": ["cycle_time", "cost", "sla"], "processes": ["construction.sites.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:construction.sites"},
    ]

