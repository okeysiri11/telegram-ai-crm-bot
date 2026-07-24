"""Domain capability seeds — finance (Sprint 20.11)."""

from __future__ import annotations

from typing import Any


def definitions() -> list[dict[str, Any]]:
    return [
        {"key": "enterprise", "name": "Enterprise", "domain": "finance", "parent_key": None, "maturity_level": 3, "owner": "capability-owner@finance", "description": "Enterprise business capability", "strategic_goal": "Strengthen Enterprise", "kpi": ["cycle_time", "cost", "sla"], "processes": ["enterprise.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:enterprise"},
        {"key": "operations", "name": "Operations", "domain": "finance", "parent_key": 'enterprise', "maturity_level": 3, "owner": "capability-owner@finance", "description": "Operations business capability", "strategic_goal": "Strengthen Operations", "kpi": ["cycle_time", "cost", "sla"], "processes": ["operations.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:operations"},
        {"key": "finance", "name": "Finance", "domain": "finance", "parent_key": 'operations', "maturity_level": 4, "owner": "capability-owner@finance", "description": "Finance business capability", "strategic_goal": "Strengthen Finance", "kpi": ["cycle_time", "cost", "sla"], "processes": ["finance.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:finance"},
        {"key": "finance.treasury", "name": "Treasury", "domain": "finance", "parent_key": 'finance', "maturity_level": 3, "owner": "capability-owner@finance", "description": "Treasury business capability", "strategic_goal": "Strengthen Treasury", "kpi": ["cycle_time", "cost", "sla"], "processes": ["finance.treasury.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:finance.treasury"},
        {"key": "finance.ap", "name": "Accounts Payable", "domain": "finance", "parent_key": 'finance', "maturity_level": 4, "owner": "capability-owner@finance", "description": "Accounts Payable business capability", "strategic_goal": "Strengthen Accounts Payable", "kpi": ["cycle_time", "cost", "sla"], "processes": ["finance.ap.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:finance.ap"},
        {"key": "finance.ar", "name": "Accounts Receivable", "domain": "finance", "parent_key": 'finance', "maturity_level": 4, "owner": "capability-owner@finance", "description": "Accounts Receivable business capability", "strategic_goal": "Strengthen Accounts Receivable", "kpi": ["cycle_time", "cost", "sla"], "processes": ["finance.ar.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:finance.ar"},
    ]

