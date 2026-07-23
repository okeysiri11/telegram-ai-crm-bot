"""AI Tools & Skills models — Sprint 20.2."""

from __future__ import annotations

TOOL_DOMAINS = (
    "crm",
    "erp",
    "finance",
    "legal",
    "analytics",
    "files",
    "communication",
    "integrations",
    "browser",
    "terminal",
    "custom",
)

TOOL_STATUSES = ("active", "disabled", "deprecated", "pending")
SKILL_STATUSES = ("active", "disabled", "draft")
EXECUTION_STATUSES = ("pending", "running", "completed", "failed", "canceled", "denied")
SANDBOX_LIMITS = ("cpu", "memory", "network", "files", "timeout")
PERMISSIONS = ("read", "write", "execute", "network", "admin")
