"""Domain capability seeds — maritime (Sprint 20.11)."""

from __future__ import annotations

from typing import Any


def definitions() -> list[dict[str, Any]]:
    return [
        {"key": "maritime", "name": "Maritime / Port Operations", "domain": "maritime", "parent_key": 'operations', "maturity_level": 3, "owner": "capability-owner@maritime", "description": "Maritime / Port Operations business capability", "strategic_goal": "Strengthen Maritime / Port Operations", "kpi": ["cycle_time", "cost", "sla"], "processes": ["maritime.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:maritime"},
        {"key": "maritime.cargo", "name": "Cargo Handling", "domain": "maritime", "parent_key": 'maritime', "maturity_level": 3, "owner": "capability-owner@maritime", "description": "Cargo Handling business capability", "strategic_goal": "Strengthen Cargo Handling", "kpi": ["cycle_time", "cost", "sla"], "processes": ["maritime.cargo.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:maritime.cargo"},
        {"key": "maritime.containers", "name": "Container Operations", "domain": "maritime", "parent_key": 'maritime', "maturity_level": 4, "owner": "capability-owner@maritime", "description": "Container Operations business capability", "strategic_goal": "Strengthen Container Operations", "kpi": ["cycle_time", "cost", "sla"], "processes": ["maritime.containers.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:maritime.containers"},
        {"key": "maritime.customs", "name": "Customs Processing", "domain": "maritime", "parent_key": 'maritime', "maturity_level": 3, "owner": "capability-owner@maritime", "description": "Customs Processing business capability", "strategic_goal": "Strengthen Customs Processing", "kpi": ["cycle_time", "cost", "sla"], "processes": ["maritime.customs.process"], "ai_components": ["advisor"], "digital_twin_ref": "twin:maritime.customs"},
    ]

