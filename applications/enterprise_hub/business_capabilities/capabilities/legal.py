"""Domain capability seeds — legal (Sprint 20.11)."""

from __future__ import annotations

from typing import Any


def definitions() -> list[dict[str, Any]]:
    return [
        {"key": "legal", "name": "Legal", "domain": "legal", "parent_key": 'enterprise', "maturity_level": 3, "owner": "capability-owner@legal", "description": "Legal business capability", "strategic_goal": "Strengthen Legal", "kpi": ["cycle_time", "cost", "sla"], "processes": ["legal.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:legal"},
        {"key": "legal.contracts", "name": "Contract Management", "domain": "legal", "parent_key": 'legal', "maturity_level": 3, "owner": "capability-owner@legal", "description": "Contract Management business capability", "strategic_goal": "Strengthen Contract Management", "kpi": ["cycle_time", "cost", "sla"], "processes": ["legal.contracts.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:legal.contracts"},
        {"key": "legal.compliance", "name": "Compliance", "domain": "legal", "parent_key": 'legal', "maturity_level": 4, "owner": "capability-owner@legal", "description": "Compliance business capability", "strategic_goal": "Strengthen Compliance", "kpi": ["cycle_time", "cost", "sla"], "processes": ["legal.compliance.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:legal.compliance"},
    ]

