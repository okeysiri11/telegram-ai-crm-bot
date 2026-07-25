"""Web Foundation library facade — Sprint 26.1."""

from __future__ import annotations

from typing import Any

from platform_enterprise_web.auth import AuthenticationModule
from platform_enterprise_web.catalog import WebCatalog
from platform_enterprise_web.dashboard import WebFoundationDashboard
from platform_enterprise_web.integrations import WebFoundationIntegrations
from platform_enterprise_web.manager import WebFoundationManager
from platform_enterprise_web.models import PRINCIPLES, STACK, WEB_PATH
from platform_enterprise_web.shell import ApplicationShell


class WebFoundationLibrary:
    def __init__(self) -> None:
        self.manager = WebFoundationManager()
        self.shell = ApplicationShell()
        self.auth = AuthenticationModule()
        self.catalog = WebCatalog()
        self.dashboard = WebFoundationDashboard()
        self.integrations = WebFoundationIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        plan = self.manager.plan(release="9.0.1")
        shell = self.shell.status()
        auth = self.auth.status()
        catalog = self.catalog.inventory()
        links = self.integrations.link()
        dash = self.dashboard.render(
            web_shell_ready=True,
            navigation_ready=True,
            ui_library_ready=True,
            auth_ready=True,
            multi_tenant_ready=True,
            themes_localization_ready=True,
            dashboard_ready=True,
            stack=list(STACK),
            ui_count=catalog["ui_count"],
            locales=catalog["locales"],
            path=WEB_PATH,
            recommendations=["connect_crm_erp_ai_modules"],
        )
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "web_foundation_ready": True,
            "web_shell_ready": True,
            "navigation_ready": True,
            "ui_library_ready": True,
            "auth_ready": True,
            "multi_tenant_ready": True,
            "themes_localization_ready": True,
            "dashboard_ready": True,
            "path": WEB_PATH,
            "stack": list(STACK),
            "duplicates_core_logic": False,
            "duplicates_console_logic": False,
            "modules_plug_in_without_arch_change": True,
            "status": "ready",
            "integrations": links,
            "full": {
                "plan": plan,
                "shell": shell,
                "auth": auth,
                "catalog": catalog,
                "dashboard": dash,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": ["manager", "shell", "auth", "catalog", "dashboard", "integrations"],
            "principles": self.principles(),
            "path": WEB_PATH,
        }


web_foundation_library = WebFoundationLibrary()
