# UnifiedAIEcosystemApplication — Sprint 12.0 integration facade (does not rewrite apps).

from __future__ import annotations

from typing import Any

from applications.ecosystem.ai_registry import UnifiedAIRegistry, unified_ai_registry
from applications.ecosystem.communication import CrossAppCommunication, cross_app_communication
from applications.ecosystem.config import DEFAULT_CONFIG, UnifiedEcosystemConfig
from applications.ecosystem.identity import UnifiedIdentity, unified_identity
from applications.ecosystem.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.ecosystem.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.ecosystem.knowledge import EcosystemAnalytics, GlobalKnowledge, ecosystem_analytics, global_knowledge
from applications.ecosystem.manager import EcosystemManager, ecosystem_manager
from applications.ecosystem.memory import SharedMemoryHub, shared_memory_hub
from applications.ecosystem.shared.store import UnifiedEcosystemStore, unified_ecosystem_store
from applications.ecosystem.workspace import (
    UnifiedAPIGateway,
    UnifiedDashboard,
    UnifiedEventCenter,
    UnifiedNotifications,
    UnifiedSearch,
    UnifiedSettings,
    unified_api_gateway,
    unified_dashboard,
    unified_event_center,
    unified_notifications,
    unified_search,
    unified_settings,
)


class UnifiedAIEcosystemApplication:
    """Integrates CRM, Auto, Agro, Port, Drone, Platform Core, and Knowledge into one AI ecosystem."""

    def __init__(
        self,
        *,
        config: UnifiedEcosystemConfig | None = None,
        store: UnifiedEcosystemStore | None = None,
        manager: EcosystemManager | None = None,
        ai: UnifiedAIRegistry | None = None,
        memory: SharedMemoryHub | None = None,
        communication: CrossAppCommunication | None = None,
        identity: UnifiedIdentity | None = None,
        dashboard: UnifiedDashboard | None = None,
        search: UnifiedSearch | None = None,
        settings: UnifiedSettings | None = None,
        notifications: UnifiedNotifications | None = None,
        events: UnifiedEventCenter | None = None,
        gateway: UnifiedAPIGateway | None = None,
        knowledge: GlobalKnowledge | None = None,
        analytics: EcosystemAnalytics | None = None,
        platform: PlatformBridge | None = None,
        ecosystem: EcosystemBridge | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or unified_ecosystem_store
        self.manager = manager or ecosystem_manager
        self.ai = ai or unified_ai_registry
        self.memory = memory or shared_memory_hub
        self.communication = communication or cross_app_communication
        self.identity = identity or unified_identity
        self.dashboard = dashboard or unified_dashboard
        self.search = search or unified_search
        self.settings = settings or unified_settings
        self.notifications = notifications or unified_notifications
        self.events = events or unified_event_center
        self.gateway = gateway or unified_api_gateway
        self.knowledge = knowledge or global_knowledge
        self.analytics = analytics or ecosystem_analytics
        self.platform = platform or platform_bridge
        self.ecosystem = ecosystem or ecosystem_bridge

    def reset(self) -> None:
        self.store.reset()

    def bootstrap(self) -> dict[str, Any]:
        discovery = self.manager.discover()
        memory = self.memory.connect_all([a["app_id"] for a in discovery["applications"]])
        graph = self.knowledge.build_graph()
        self.events.publish(topic="ai_ecosystem.bootstrap", source="ai_ecosystem", payload={"apps": discovery["count"]})
        return {
            "bootstrap": True,
            "applications": discovery,
            "memory": memory,
            "knowledge_graph": {"nodes": len(graph["nodes"]), "edges": len(graph["edges"]), "sources": graph["source_count"]},
            "version": self.config.application_version,
        }

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "application": self.config.application,
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "release_status": self.config.release_status,
            "api_prefix": self.config.api_prefix,
            "platform_dependency": self.config.platform_dependency,
            "ecosystem_dependency": self.config.ecosystem_dependency,
            "unified_ai_ecosystem_ready": True,
            "cross_platform_integration_ready": True,
            "global_knowledge_graph_ready": True,
            "chief_ai_ready": True,
            "executive_dashboard_ready": True,
            "engines": {
                "ecosystem_manager": self.config.ecosystem_manager,
                "application_registry": self.config.application_registry,
                "unified_ai": self.config.unified_ai,
                "shared_memory": self.config.shared_memory,
                "cross_app_communication": self.config.cross_app_communication,
                "unified_auth": self.config.unified_auth,
                "unified_dashboard": self.config.unified_dashboard,
                "unified_search": self.config.unified_search,
                "global_knowledge": self.config.global_knowledge,
                "analytics": self.config.analytics,
            },
            "manager": self.manager.status(),
            "ai": self.ai.status(),
            "memory": self.memory.status(),
            "communication": self.communication.status(),
            "identity": self.identity.status(),
            "dashboard": self.dashboard.status(),
            "search": self.search.status(),
            "knowledge": self.knowledge.status(),
            "analytics": self.analytics.status(),
            "bridges": {
                "platform": self.platform.health(),
                "ecosystem": self.ecosystem.health(),
            },
        }


ai_ecosystem = UnifiedAIEcosystemApplication()
