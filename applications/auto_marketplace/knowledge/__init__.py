"""Knowledge package — sales KB and vehicle knowledge cards."""

from __future__ import annotations

from typing import Any

__all__ = [
    "KnowledgeService",
    "knowledge_service",
    "VehicleKnowledgeEngine",
    "vehicle_knowledge_engine",
]


def __getattr__(name: str) -> Any:
    if name in {"KnowledgeService", "knowledge_service"}:
        from applications.auto_marketplace.knowledge.service import KnowledgeService, knowledge_service

        return KnowledgeService if name == "KnowledgeService" else knowledge_service
    if name in {"VehicleKnowledgeEngine", "vehicle_knowledge_engine"}:
        from applications.auto_marketplace.knowledge.vehicle import (
            VehicleKnowledgeEngine,
            vehicle_knowledge_engine,
        )

        return VehicleKnowledgeEngine if name == "VehicleKnowledgeEngine" else vehicle_knowledge_engine
    raise AttributeError(name)
