"""Developer Platform Suite facade — Sprint 20.6."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.developer_platform.api_gateway import DeveloperApiGateway
from applications.enterprise_hub.developer_platform.dependency_manager import DependencyManager
from applications.enterprise_hub.developer_platform.extension_manager import ExtensionManager
from applications.enterprise_hub.developer_platform.marketplace.installer import MarketplaceInstaller
from applications.enterprise_hub.developer_platform.marketplace.publisher import MarketplacePublisher
from applications.enterprise_hub.developer_platform.marketplace.repository import MarketplaceRepository
from applications.enterprise_hub.developer_platform.marketplace.signatures import MarketplaceSignatures
from applications.enterprise_hub.developer_platform.marketplace.updater import MarketplaceUpdater
from applications.enterprise_hub.developer_platform.package_manager import PackageManager
from applications.enterprise_hub.developer_platform.plugin_lifecycle import PluginLifecycle
from applications.enterprise_hub.developer_platform.plugin_loader import PluginLoader
from applications.enterprise_hub.developer_platform.plugin_manager import PluginManager
from applications.enterprise_hub.developer_platform.plugin_registry import PluginRegistry
from applications.enterprise_hub.developer_platform.sandbox import PluginSandbox
from applications.enterprise_hub.developer_platform.sdk.enterprise_sdk import EnterpriseSdk
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class DeveloperPlatformSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.plugins = PluginManager(self.store)
        self.registry = PluginRegistry(self.store)
        self.loader = PluginLoader(self.store)
        self.lifecycle = PluginLifecycle(self.store)
        self.extensions = ExtensionManager(self.store)
        self.sdk = EnterpriseSdk(self.store)
        self.gateway = DeveloperApiGateway(self.store)
        self.packages = PackageManager(self.store)
        self.dependencies = DependencyManager(self.store)
        self.sandbox = PluginSandbox(self.store)
        self.marketplace = MarketplaceRepository(self.store)
        self.publisher = MarketplacePublisher(self.store)
        self.installer = MarketplaceInstaller(self.store)
        self.updater = MarketplaceUpdater(self.store)
        self.signatures = MarketplaceSignatures(self.store)

    def console(self) -> dict[str, Any]:
        plugins = self.registry.list_all()
        updates = self.updater.check_updates()
        audits = self.store.sdp_audit.list_all()
        errors = [a for a in audits if a.get("action") == "error"]
        return {
            "installed_modules": plugins,
            "plugin_count": len(plugins),
            "dependencies": self.dependencies.status(),
            "by_status": self.registry.status().get("by_status"),
            "resource_usage": {
                "sandboxes": self.sandbox.status()["sandboxes"],
                "sdk_calls": self.sdk.status()["calls"],
                "gateway_routes": self.gateway.status()["routes"],
            },
            "error_log": errors[-20:],
            "audit_log": audits[-20:],
            "available_updates": updates,
            "marketplace": self.marketplace.status(),
            "packages": self.packages.status(),
            "extensions": self.extensions.status(),
            "sdk_docs": self.sdk.describe(),
        }

    def analytics(self) -> dict[str, Any]:
        plugins = self.registry.list_all()
        loads = self.store.sdp_loads.list_all()
        reloads = self.store.sdp_reloads.list_all()
        return {
            "analytics_id": f"sdp_an_{len(plugins)}_{len(loads)}",
            "plugins": len(plugins),
            "loads": len(loads),
            "hot_reloads": len(reloads),
            "sdk_calls": self.sdk.status()["calls"],
            "extensions": self.extensions.status()["extensions"],
            "marketplace_listings": self.marketplace.status()["listings"],
            "signatures": self.signatures.status()["signatures"],
        }

    def generate_sdk_docs(self) -> dict[str, Any]:
        desc = self.sdk.describe()
        lines = ["# Enterprise SDK", "", f"Version: {desc['version']}", ""]
        for surface in desc["surfaces"]:
            caps = desc.get(surface) if isinstance(desc.get(surface), list) else None
            if caps is None and surface == "erp":
                caps = desc.get("crm")
            if caps is None and surface == "knowledge":
                caps = desc.get("ai")
            lines.append(f"## {surface}")
            for c in caps or []:
                lines.append(f"- `{c}`")
            lines.append("")
        doc = "\n".join(lines)
        return {"title": "Enterprise SDK", "markdown": doc, "surfaces": desc["surfaces"], "version": desc["version"]}

    def bootstrap(self) -> dict[str, Any]:
        # sample plugins via manager
        p1 = self.plugins.install_from_manifest(
            plugin_id="crm-industry-pack",
            name="CRM Industry Pack",
            version="1.0.0",
            kind="module",
            permissions=["crm.read", "crm.write", "ui.extend"],
            dependencies=[],
        )
        p2 = self.plugins.install_from_manifest(
            plugin_id="ai-lead-agent",
            name="AI Lead Agent",
            version="1.1.0",
            kind="ai_agent",
            permissions=["ai.invoke", "crm.read", "events.publish"],
            dependencies=["crm-industry-pack@>=1.0.0"],
        )
        dep = self.dependencies.resolve(
            plugin_id="ai-lead-agent",
            dependencies=["crm-industry-pack@>=1.0.0"],
        )
        sbx = self.sandbox.create(plugin_id="ai-lead-agent", allow_network=False, memory_mb=64, cpu_ms=500)
        sbx_check = self.sandbox.check(sandbox_id=sbx["sandbox_id"], needs_network=True)

        ext1 = self.extensions.extend(
            plugin_id="crm-industry-pack", point="menu", label="Industry CRM", handler="menu.open"
        )
        ext2 = self.extensions.extend(
            plugin_id="ai-lead-agent", point="ai_agents", label="Lead Agent", handler="agent.run"
        )
        ext3 = self.extensions.extend(
            plugin_id="crm-industry-pack", point="dashboard", label="Industry KPIs", handler="dash.render"
        )

        sdk_call = self.sdk.call(surface="crm", method="create_lead", plugin_id="crm-industry-pack", payload={"name": "Acme"})
        gw = self.gateway.route(path="/plugins/crm-industry-pack/health", method="GET", plugin_id="crm-industry-pack")

        pub = self.publisher.publish(
            package_id="crm-industry-pack",
            name="CRM Industry Pack",
            version="1.2.0",
            tags=["crm", "industry"],
            description="Industry CRM module",
        )
        # install older package then show update available vs marketplace listing
        self.packages.install(package_id="crm-industry-pack", name="CRM Industry Pack", version="1.0.0")
        listing_id = self.store.sdp_listings.list_all()[0]["listing_id"]
        self.marketplace.add_review(listing_id=listing_id, author="ops", rating=4.5, comment="solid")
        updates = self.updater.check_updates()
        inst = self.installer.install_listing(listing_id=listing_id)
        hot = self.lifecycle.hot_reload(plugin_id="ai-lead-agent")
        rb = self.lifecycle.rollback(plugin_id="ai-lead-agent", to_version="1.0.0")
        # re-activate after rollback demo
        self.lifecycle.activate(plugin_id="ai-lead-agent")

        console = self.console()
        analytics = self.analytics()
        docs = self.generate_sdk_docs()

        return {
            "bootstrap": True,
            "plugin_ids": [p1["plugin_id"], p2["plugin_id"]],
            "dependency_compatible": dep["compatible"],
            "sandbox_id": sbx["sandbox_id"],
            "sandbox_network_denied": not sbx_check["allowed"],
            "extension_ids": [ext1["extension_id"], ext2["extension_id"], ext3["extension_id"]],
            "sdk_call_id": sdk_call["call_id"],
            "gateway_route_id": gw["route_id"],
            "publish_id": pub["publish_id"],
            "install_id": inst["install_id"],
            "updates_available": len(updates) >= 1,
            "hot_reload_id": hot["reload_id"],
            "rollback_id": rb["rollback_id"],
            "console_plugins": console["plugin_count"],
            "analytics_id": analytics["analytics_id"],
            "sdk_docs_surfaces": len(docs["surfaces"]),
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "plugins": self.plugins.status(),
            "sdk": self.sdk.status(),
            "packages": self.packages.status(),
            "marketplace": self.marketplace.status(),
            "sandbox": self.sandbox.status(),
            "extensions": self.extensions.status(),
        }


developer_platform = DeveloperPlatformSuite()
