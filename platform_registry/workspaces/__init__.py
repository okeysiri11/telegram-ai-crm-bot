"""Module workspace registry — CRM, ERP, Calendar, … (not business verticals)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkspaceModuleDef:
    id: str
    title: str
    icon: str
    description: str
    route: str
    telegram_command: str | None = None
    required_permissions: tuple[str, ...] = ()


WORKSPACE_MODULE_REGISTRY: dict[str, WorkspaceModuleDef] = {
    "crm": WorkspaceModuleDef("crm", "CRM", "crm", "Customer relationship management", "/crm", "crm", ("crm.read",)),
    "erp": WorkspaceModuleDef("erp", "ERP", "erp", "Enterprise resource planning", "/erp", "erp", ("erp.read",)),
    "calendar": WorkspaceModuleDef("calendar", "Calendar", "calendar", "Scheduling", "/calendar", "calendar", ("calendar.read",)),
    "tasks": WorkspaceModuleDef("tasks", "Tasks", "tasks", "Task management", "/tasks", "tasks", ("tasks.read",)),
    "files": WorkspaceModuleDef("files", "Files", "files", "File storage", "/documents", "files", ("files.upload",)),
    "documents": WorkspaceModuleDef("documents", "Documents", "documents", "Document management", "/documents", "documents", ("documents.manage",)),
    "analytics": WorkspaceModuleDef("analytics", "Analytics", "analytics", "Business analytics", "/analytics", "analytics", ("analytics.read",)),
    "ai_studio": WorkspaceModuleDef("ai_studio", "AI Studio", "ai", "AI content studio", "/ai-studio", "ai_studio", ("studio.generate",)),
    "marketplace": WorkspaceModuleDef("marketplace", "Marketplace", "marketplace", "Marketplace", "/marketplace", "marketplace", ("crm.read",)),
    "finance": WorkspaceModuleDef("finance", "Finance", "finance", "Finance & billing", "/analytics", "finance", ("analytics.read",)),
    "settings": WorkspaceModuleDef("settings", "Settings", "settings", "Platform settings", "/settings", "settings", ()),
    "notifications": WorkspaceModuleDef("notifications", "Notifications", "bell", "Notification center", "/notifications", "notifications", ()),
    "search": WorkspaceModuleDef("search", "Search", "search", "Universal search", "/search", "search", ()),
    "knowledge": WorkspaceModuleDef("knowledge", "Knowledge Base", "knowledge", "Enterprise knowledge", "/knowledge", "knowledge", ("knowledge.read",)),
    "production": WorkspaceModuleDef("production", "Production", "production", "AI production center", "/production-studio", "production", ("studio.generate",)),
    "desktop": WorkspaceModuleDef("desktop", "Desktop", "desktop", "Enterprise desktop", "/desktop", "desktop", ()),
    "integrations": WorkspaceModuleDef("integrations", "Integrations", "integrations", "Integration hub", "/platform-builder/integrations", "integrations", ("platform.config.read",)),
}


def all_workspace_modules() -> list[WorkspaceModuleDef]:
    return list(WORKSPACE_MODULE_REGISTRY.values())


def workspace_module(mid: str | None) -> WorkspaceModuleDef | None:
    if not mid:
        return None
    return WORKSPACE_MODULE_REGISTRY.get(str(mid).strip().lower())
