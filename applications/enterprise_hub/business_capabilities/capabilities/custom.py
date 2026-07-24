"""Domain capability seeds — custom (Sprint 20.11)."""

from __future__ import annotations

from typing import Any


def definitions() -> list[dict[str, Any]]:
    return [
        {"key": "custom", "name": "Custom Capability", "domain": "custom", "parent_key": 'enterprise', "maturity_level": 1, "owner": "capability-owner@custom", "description": "Custom Capability business capability", "strategic_goal": "Strengthen Custom Capability", "kpi": ["cycle_time", "cost", "sla"], "processes": ["custom.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:custom"},
    ]

