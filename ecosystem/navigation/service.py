# Navigation service — cross-application navigation layer.

from __future__ import annotations

from typing import Any

from ecosystem.config import DEFAULT_CONFIG
from events.publisher import publish

from ecosystem.events import ApplicationOpenedEvent


class NavigationService:
    APPLICATION_NAV = {
        "auto_marketplace": {
            "label": "Auto Marketplace",
            "icon": "car",
            "routes": [
                {"path": "/api/auto/v1/portal/customer/search", "label": "Search Vehicles"},
                {"path": "/api/auto/v1/crm", "label": "CRM"},
                {"path": "/api/auto/v1/finance", "label": "Finance"},
                {"path": "/api/auto/v1/bi", "label": "Business Intelligence"},
                {"path": "/api/auto/v1/portal", "label": "Portal"},
            ],
        },
    }

    def registered_applications(self) -> list[str]:
        return list(DEFAULT_CONFIG.registered_applications)

    def navigation_tree(self, *, user_id: str = "", organization_id: str = "") -> dict[str, Any]:
        apps = []
        for app_id in DEFAULT_CONFIG.registered_applications:
            nav = self.APPLICATION_NAV.get(app_id, {"label": app_id, "icon": "app", "routes": []})
            apps.append({"application_id": app_id, **nav})
        return {
            "user_id": user_id,
            "organization_id": organization_id,
            "applications": apps,
            "ecosystem_routes": [
                {"path": "/api/ecosystem/v1/workspace/dashboard", "label": "Dashboard"},
                {"path": "/api/ecosystem/v1/workspace/search", "label": "Global Search"},
                {"path": "/api/ecosystem/v1/identity/profile", "label": "Profile"},
                {"path": "/api/ecosystem/v1/assistant", "label": "AI Assistant"},
            ],
        }

    async def open_application(
        self,
        user_id: str,
        application_id: str,
        *,
        workspace_id: str = "",
    ) -> dict[str, Any]:
        nav = self.APPLICATION_NAV.get(application_id)
        if nav is None and application_id not in DEFAULT_CONFIG.registered_applications:
            return {"opened": False, "application_id": application_id, "error": "Application not registered"}
        await publish(ApplicationOpenedEvent(user_id=user_id, application_id=application_id, workspace_id=workspace_id))
        return {
            "opened": True,
            "application_id": application_id,
            "workspace_id": workspace_id,
            "navigation": nav or {"label": application_id, "routes": []},
        }


navigation_service = NavigationService()
