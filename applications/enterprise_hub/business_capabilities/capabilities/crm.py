"""Domain capability seeds — crm (Sprint 20.11)."""

from __future__ import annotations

from typing import Any


def definitions() -> list[dict[str, Any]]:
    return [
        {"key": "crm", "name": "CRM", "domain": "crm", "parent_key": 'operations', "maturity_level": 4, "owner": "capability-owner@crm", "description": "CRM business capability", "strategic_goal": "Strengthen CRM", "kpi": ["cycle_time", "cost", "sla"], "processes": ["crm.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:crm"},
        {"key": "crm.accounts", "name": "Account Management", "domain": "crm", "parent_key": 'crm', "maturity_level": 4, "owner": "capability-owner@crm", "description": "Account Management business capability", "strategic_goal": "Strengthen Account Management", "kpi": ["cycle_time", "cost", "sla"], "processes": ["crm.accounts.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:crm.accounts"},
        {"key": "crm.service", "name": "Customer Service", "domain": "crm", "parent_key": 'crm', "maturity_level": 3, "owner": "capability-owner@crm", "description": "Customer Service business capability", "strategic_goal": "Strengthen Customer Service", "kpi": ["cycle_time", "cost", "sla"], "processes": ["crm.service.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:crm.service"},
    ]

