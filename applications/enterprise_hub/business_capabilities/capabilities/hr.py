"""Domain capability seeds — hr (Sprint 20.11)."""

from __future__ import annotations

from typing import Any


def definitions() -> list[dict[str, Any]]:
    return [
        {"key": "hr", "name": "Human Resources", "domain": "hr", "parent_key": 'enterprise', "maturity_level": 3, "owner": "capability-owner@hr", "description": "Human Resources business capability", "strategic_goal": "Strengthen Human Resources", "kpi": ["cycle_time", "cost", "sla"], "processes": ["hr.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:hr"},
        {"key": "hr.talent", "name": "Talent Management", "domain": "hr", "parent_key": 'hr', "maturity_level": 2, "owner": "capability-owner@hr", "description": "Talent Management business capability", "strategic_goal": "Strengthen Talent Management", "kpi": ["cycle_time", "cost", "sla"], "processes": ["hr.talent.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:hr.talent"},
        {"key": "hr.payroll", "name": "Payroll", "domain": "hr", "parent_key": 'hr', "maturity_level": 4, "owner": "capability-owner@hr", "description": "Payroll business capability", "strategic_goal": "Strengthen Payroll", "kpi": ["cycle_time", "cost", "sla"], "processes": ["hr.payroll.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:hr.payroll"},
    ]

