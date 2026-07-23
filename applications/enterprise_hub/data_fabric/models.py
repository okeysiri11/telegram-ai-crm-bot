"""Data Fabric models — Sprint 20.7."""

from __future__ import annotations

ASSET_KINDS = (
    "table",
    "document",
    "event",
    "vector_index",
    "file_store",
    "external",
    "ai_model",
)
SOURCE_TYPES = (
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "elasticsearch",
    "vector_db",
    "object_storage",
    "data_warehouse",
    "custom",
    "crm",
    "erp",
    "knowledge",
    "analytics",
    "event_stream",
)
VIRTUALIZATION_MODES = ("sql", "nosql", "graph", "vector", "object", "event_stream")
SENSITIVITY = ("public", "internal", "confidential", "restricted")
QUALITY_CHECKS = ("completeness", "freshness", "correctness", "duplicates", "anomalies", "consistency")
