"""Developer Platform models — Sprint 20.6."""

from __future__ import annotations

PLUGIN_STATUSES = ("registered", "installed", "loaded", "active", "disabled", "failed", "rolled_back")
PLUGIN_KINDS = ("module", "plugin", "ai_agent", "integration", "ui", "workflow", "custom")
EXTENSION_POINTS = (
    "menu",
    "ui",
    "ai_agents",
    "workflow",
    "reports",
    "dashboard",
    "forms",
    "events",
)
PERMISSIONS = (
    "crm.read",
    "crm.write",
    "erp.read",
    "erp.write",
    "workflow.execute",
    "ai.invoke",
    "events.publish",
    "events.subscribe",
    "ui.extend",
    "integrations.call",
    "security.audit",
    "filesystem.limited",
    "network.limited",
)
SANDBOX_LIMITS = ("filesystem", "network", "memory", "cpu", "syscalls")
PACKAGE_ACTIONS = ("install", "uninstall", "update", "rollback", "verify")
