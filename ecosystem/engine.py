# Ecosystem engine — unified facade for identity, workspace, and navigation.

from __future__ import annotations

from typing import Any

from ecosystem.ai.assistant import UnifiedAssistant, unified_assistant
from ecosystem.config import DEFAULT_CONFIG
from ecosystem.identity.service import IdentityService, identity_service
from ecosystem.navigation.service import NavigationService, navigation_service
from ecosystem.organizations.service import OrganizationService, organization_service
from ecosystem.permissions.service import PermissionService, permission_service
from ecosystem.profiles.service import ProfileService, profile_service
from ecosystem.services.shared_services import CrossApplicationServices, cross_app_services
from ecosystem.tenants.service import TenantService, tenant_service
from ecosystem.workspace.service import WorkspaceService, workspace_service


class EcosystemEngine:
    """Unified ecosystem entry point — identity, workspace, organizations, AI."""

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
        assistant: UnifiedAssistant | None = None,
    ) -> None:
        self.identity = identity or identity_service
        self.organizations = organizations or organization_service
        self.permissions = permissions or permission_service
        self.profiles = profiles or profile_service
        self.tenants = tenants or tenant_service
        self.workspace = workspace or workspace_service
        self.navigation = navigation or navigation_service
        self.shared = shared or cross_app_services
        self.assistant = assistant or unified_assistant

    def metrics(self) -> dict[str, Any]:
        from ecosystem.shared.store import ecosystem_store

        return {
            "ecosystem_version": DEFAULT_CONFIG.ecosystem_version,
            "platform_dependency": DEFAULT_CONFIG.platform_dependency,
            "users": ecosystem_store.users.count(),
            "organizations": ecosystem_store.organizations.count(),
            "workspaces": ecosystem_store.workspaces.count(),
            "sessions": ecosystem_store.sessions.count(),
            "registered_applications": DEFAULT_CONFIG.registered_applications,
        }


ecosystem_engine = EcosystemEngine()
