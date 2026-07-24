"""Digital Twin models — Sprint 20.8."""

from __future__ import annotations

TWIN_TYPES = (
    "organization",
    "department",
    "employee",
    "customer",
    "supplier",
    "project",
    "warehouse",
    "equipment",
    "vehicle",
    "vessel",
    "production",
    "asset",
    "ai_agent",
    "custom",
    "document",
    "order",
    "container",
)

TWIN_STATUSES = ("active", "inactive", "archived", "deleted", "restored", "syncing")
ACCESS_LEVELS = ("public", "internal", "restricted", "confidential")
RELATION_KINDS = (
    "contains",
    "owns",
    "employs",
    "serves",
    "supplies",
    "depends_on",
    "controls",
    "documents",
    "operates",
)
SYNC_SOURCES = ("crm", "erp", "workflow", "ai", "documents", "resources", "event_bus", "data_fabric", "knowledge")
SNAPSHOT_KINDS = ("manual", "automatic")
