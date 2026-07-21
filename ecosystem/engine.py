# Ecosystem engine — unified facade including AI workforce.

from __future__ import annotations

from typing import Any

from ecosystem.assistant.engine import AssistantEngine, assistant_engine
from ecosystem.communication.engine import CommunicationEngine, communication_engine
from ecosystem.config import DEFAULT_CONFIG
from ecosystem.identity.service import IdentityService, identity_service
from ecosystem.navigation.service import NavigationService, navigation_service
from ecosystem.organizations.service import OrganizationService, organization_service
from ecosystem.permissions.service import PermissionService, permission_service
from ecosystem.profiles.service import ProfileService, profile_service
from ecosystem.services.shared_services import CrossApplicationServices, cross_app_services
from ecosystem.tenants.service import TenantService, tenant_service
from ecosystem.workforce.engine import WorkforceEngine, workforce_engine
from ecosystem.workspace.service import WorkspaceService, workspace_service


class EcosystemEngine:
    """Unified ecosystem entry point — identity, workspace, communication, assistant, workforce."""

    def __init__(
        self,
        identity: IdentityService | None = None,
        organizations: OrganizationService | None = None,
        permissions: PermissionService | None = None,
        profiles: ProfileService | None = None,
        tenants: TenantService | None = None,
        workspace: WorkspaceService | None = None,
        navigation: NavigationService | None = None,
        shared: CrossApplicationServices | None = None,
        assistant: AssistantEngine | None = None,
        communication: CommunicationEngine | None = None,
        workforce: WorkforceEngine | None = None,
    ) -> None:
        self.identity = identity or identity_service
        self.organizations = organizations or organization_service
        self.permissions = permissions or permission_service
        self.profiles = profiles or profile_service
        self.tenants = tenants or tenant_service
        self.workspace = workspace or workspace_service
        self.navigation = navigation or navigation_service
        self.shared = shared or cross_app_services
        self.assistant = assistant or assistant_engine
        self.communication = communication or communication_engine
        self.workforce = workforce or workforce_engine

    def metrics(self) -> dict[str, Any]:
        from ecosystem.shared.store import ecosystem_store

        return {
            "ecosystem_version": DEFAULT_CONFIG.ecosystem_version,
            "platform_dependency": DEFAULT_CONFIG.platform_dependency,
            "communication_layer": DEFAULT_CONFIG.communication_layer,
            "event_bus": DEFAULT_CONFIG.event_bus,
            "assistant_layer": DEFAULT_CONFIG.assistant_layer,
            "global_knowledge": DEFAULT_CONFIG.global_knowledge,
            "workforce_layer": DEFAULT_CONFIG.workforce_layer,
            "executive_ai": DEFAULT_CONFIG.executive_ai,
            "users": ecosystem_store.users.count(),
            "organizations": ecosystem_store.organizations.count(),
            "workspaces": ecosystem_store.workspaces.count(),
            "sessions": ecosystem_store.sessions.count(),
            "registered_applications": DEFAULT_CONFIG.registered_applications,
            "communication": self.communication.metrics(),
            "assistant": self.assistant.metrics(),
            "workforce": self.workforce.metrics(),
        }


ecosystem_engine = EcosystemEngine()
