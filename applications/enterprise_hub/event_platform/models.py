"""Event Platform models — Sprint 20.5."""

from __future__ import annotations

EVENT_TYPES = (
    "UserCreated",
    "LeadCreated",
    "ContractSigned",
    "PaymentReceived",
    "InvoiceApproved",
    "TaskCompleted",
    "ShipmentCreated",
    "AIJobFinished",
    "DocumentUpdated",
    "SecurityAlert",
)

SEVERITIES = ("low", "normal", "high", "critical")
EVENT_STATUSES = ("published", "delivered", "processed", "failed", "replayed", "dead")
SUBSCRIBER_KINDS = ("notifications", "analytics", "audit", "integrations", "ai_agents")
PUBLISHER_KINDS = ("crm", "erp", "ai", "workflow", "finance", "custom")
