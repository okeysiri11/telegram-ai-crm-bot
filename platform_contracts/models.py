"""Contract constants — Sprint 21.3."""

from __future__ import annotations

DOMAINS = (
    "crm",
    "erp",
    "hr",
    "finance",
    "logistics",
    "warehouse",
    "manufacturing",
    "maritime",
    "healthcare",
    "construction",
    "legal",
    "ai",
    "workflow",
    "security",
    "analytics",
    "integration",
    "common",
)

SERIALIZATION_FORMATS = ("json", "msgpack", "protobuf", "avro")

EVENT_REQUIRED_FIELDS = (
    "event_id",
    "event_type",
    "aggregate_id",
    "aggregate_type",
    "source_service",
    "actor",
    "payload",
    "schema_version",
    "timestamp",
    "trace_id",
)

BASE_DTO_FIELDS = (
    "id",
    "version",
    "tenant_id",
    "organization_id",
    "correlation_id",
    "request_id",
    "created_at",
    "updated_at",
    "metadata",
)

INTEGRATION_TARGETS = (
    "api_standardization",
    "event_bus",
    "workflow",
    "ai_orchestrator",
    "data_fabric",
    "knowledge_platform",
    "integration_hub",
    "sdk",
)
