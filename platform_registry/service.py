# Platform Registry Service — Sprint 34.2B facade.

from __future__ import annotations

from typing import Any

from platform_registry.agents import all_agents
from platform_registry.features import all_features
from platform_registry.menus import MENU_CATALOG, all_menu_items
from platform_registry.modules import all_modules
from platform_registry.navigation import filter_menu, group_menu
from platform_registry.permissions import PLATFORM_PERMISSIONS, all_permissions, permissions_for_roles
from platform_registry.roles import all_platform_roles
from platform_registry.routing import all_routes
from platform_registry.verticals import all_verticals
from platform_registry.workspaces import all_workspace_modules


class PlatformRegistryService:
    """Single entry for catalogs — Web/Telegram/Mobile/Desktop/API/AI."""

    sprint = "34.2B"
    version = "1.0.0"

    def snapshot(self) -> dict[str, Any]:
        return {
            "sprint": self.sprint,
            "version": self.version,
            "identity_core": "34.2A",
            "roles": [
                {
                    "code": r.code,
                    "title": r.title,
                    "description": r.description,
                    "aliases": list(r.aliases),
                }
                for r in all_platform_roles()
            ],
            "permissions": [
                {"code": p.code, "description": p.description, "aliases": list(p.aliases)}
                for p in all_permissions()
            ],
            "workspaces": [
                {
                    "id": w.id,
                    "title": w.title,
                    "icon": w.icon,
                    "description": w.description,
                    "route": w.route,
                    "telegram_command": w.telegram_command,
                    "required_permissions": list(w.required_permissions),
                }
                for w in all_workspace_modules()
            ],
            "verticals": [
                {
                    "id": v.id,
                    "title": v.title,
                    "icon": v.icon,
                    "description": v.description,
                    "workspace": v.workspace,
                    "default_roles": list(v.default_roles),
                    "enabled_modules": list(v.enabled_modules),
                    "enabled_agents": list(v.enabled_agents),
                    "enabled_features": list(v.enabled_features),
                    "web_path": v.web_path,
                    "telegram_entry": v.telegram_entry,
                }
                for v in all_verticals()
            ],
            "menus": [m.to_dict() for m in all_menu_items()],
            "modules": [
                {
                    "id": m.id,
                    "title": m.title,
                    "route": m.route,
                    "icon": m.icon,
                    "permissions": list(m.permissions),
                }
                for m in all_modules()
            ],
            "agents": [
                {
                    "id": a.id,
                    "title": a.title,
                    "vertical": a.vertical,
                    "role": a.role,
                    "permissions": list(a.permissions),
                    "entry_points": list(a.entry_points),
                    "available_clients": list(a.available_clients),
                    "model": a.model,
                    "tools": list(a.tools),
                    "memory": a.memory,
                    "knowledge_base": a.knowledge_base,
                }
                for a in all_agents()
            ],
            "features": [
                {
                    "id": f.id,
                    "title": f.title,
                    "enabled_by_default": f.enabled_by_default,
                }
                for f in all_features()
            ],
            "routes": all_routes(),
            "permission_count": len(PLATFORM_PERMISSIONS),
            "menu_count": len(MENU_CATALOG),
        }

    def navigation_for(
        self,
        *,
        client: str,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
        include_owner: bool = False,
        simple: bool = False,
    ) -> dict[str, Any]:
        items = filter_menu(
            client=client,
            roles=roles,
            permissions=permissions,
            include_owner=include_owner,
            simple=simple,
        )
        return {
            "sprint": self.sprint,
            "client": client,
            "roles": roles or [],
            "items": [i.to_dict() for i in items],
            "groups": group_menu(items),
        }

    def permissions_for_roles(self, roles: list[str]) -> list[str]:
        return permissions_for_roles(roles)


platform_registry = PlatformRegistryService()
