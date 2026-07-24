"""Domain capability seeds — warehouse (Sprint 20.11)."""

from __future__ import annotations

from typing import Any


def definitions() -> list[dict[str, Any]]:
    return [
        {"key": "warehouse", "name": "Warehouse", "domain": "warehouse", "parent_key": 'operations', "maturity_level": 3, "owner": "capability-owner@warehouse", "description": "Warehouse business capability", "strategic_goal": "Strengthen Warehouse", "kpi": ["cycle_time", "cost", "sla"], "processes": ["warehouse.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:warehouse"},
        {"key": "warehouse.inventory", "name": "Inventory Control", "domain": "warehouse", "parent_key": 'warehouse', "maturity_level": 4, "owner": "capability-owner@warehouse", "description": "Inventory Control business capability", "strategic_goal": "Strengthen Inventory Control", "kpi": ["cycle_time", "cost", "sla"], "processes": ["warehouse.inventory.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:warehouse.inventory"},
        {"key": "warehouse.picking", "name": "Picking & Packing", "domain": "warehouse", "parent_key": 'warehouse', "maturity_level": 3, "owner": "capability-owner@warehouse", "description": "Picking & Packing business capability", "strategic_goal": "Strengthen Picking & Packing", "kpi": ["cycle_time", "cost", "sla"], "processes": ["warehouse.picking.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:warehouse.picking"},
    ]

