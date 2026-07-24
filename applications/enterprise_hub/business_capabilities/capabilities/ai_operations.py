"""Domain capability seeds — ai_operations (Sprint 20.11)."""

from __future__ import annotations

from typing import Any


def definitions() -> list[dict[str, Any]]:
    return [
        {"key": "ai_operations", "name": "AI Operations", "domain": "ai_operations", "parent_key": 'enterprise', "maturity_level": 4, "owner": "capability-owner@ai_operations", "description": "AI Operations business capability", "strategic_goal": "Strengthen AI Operations", "kpi": ["cycle_time", "cost", "sla"], "processes": ["ai_operations.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:ai_operations"},
        {"key": "ai_operations.agents", "name": "AI Agents", "domain": "ai_operations", "parent_key": 'ai_operations', "maturity_level": 5, "owner": "capability-owner@ai_operations", "description": "AI Agents business capability", "strategic_goal": "Strengthen AI Agents", "kpi": ["cycle_time", "cost", "sla"], "processes": ["ai_operations.agents.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:ai_operations.agents"},
        {"key": "ai_operations.orchestration", "name": "AI Orchestration", "domain": "ai_operations", "parent_key": 'ai_operations', "maturity_level": 4, "owner": "capability-owner@ai_operations", "description": "AI Orchestration business capability", "strategic_goal": "Strengthen AI Orchestration", "kpi": ["cycle_time", "cost", "sla"], "processes": ["ai_operations.orchestration.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:ai_operations.orchestration"},
    ]

