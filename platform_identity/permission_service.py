# IAM permission catalog — hierarchical, independently assignable.

from __future__ import annotations

from platform_identity.models import PlatformRole

# Permission tree: module.action
IAM_PERMISSIONS: dict[str, str] = {
    # System
    "system.read": "Read system information",
    "system.admin": "Administer system settings",
    # Configuration
    "configuration.read": "Read platform configuration",
    "configuration.write": "Modify platform configuration",
    # Dashboard
    "dashboard.read": "View operations dashboard",
    "dashboard.admin": "Administer dashboard settings",
    # Requests
    "requests.read": "View requests",
    "requests.write": "Create and update requests",
    "requests.assign": "Assign requests to managers",
    # Managers
    "managers.read": "View manager pool",
    "managers.write": "Manage manager pool",
    # Audit
    "audit.read": "View audit trail",
    "audit.export": "Export audit data",
    # Workflow
    "workflow.read": "View workflows",
    "workflow.write": "Manage workflows",
    # SDK
    "sdk.read": "Read SDK resources",
    "sdk.write": "Modify SDK resources",
    # Plugins
    "plugins.read": "View plugins",
    "plugins.write": "Manage plugins",
    # AI
    "ai.read": "View AI modules",
    "ai.use": "Use AI features",
    "ai.admin": "Administer AI modules",
    # Realtime channels
    "realtime.channel.system": "Subscribe to system channel",
    "realtime.channel.dashboard": "Subscribe to dashboard channel",
    "realtime.channel.requests": "Subscribe to requests channel",
    "realtime.channel.workflows": "Subscribe to workflows channel",
    "realtime.channel.managers": "Subscribe to managers channel",
    "realtime.channel.audit": "Subscribe to audit channel",
    "realtime.channel.configuration": "Subscribe to configuration channel",
    "realtime.channel.notifications": "Subscribe to notifications channel",
    "realtime.channel.plugins": "Subscribe to plugins channel",
    "realtime.channel.ai": "Subscribe to AI channel",
    "realtime.channel.health": "Subscribe to health channel",
    # Management API
    "management.read": "Read management API",
    "management.write": "Write via management API",
    "management.admin": "Full management API access",
    "management.identity.read": "Read IAM resources",
    "management.identity.write": "Manage IAM resources",
    # Integrations
    "integrations.read": "View integration hub",
    "integrations.write": "Manage connectors and webhooks",
    "integrations.admin": "Full integration hub access",
    # Jobs
    "jobs.read": "View job engine status",
    "jobs.write": "Enqueue and manage jobs",
    "jobs.admin": "Full job engine access",
    # Observability
    "observability.read": "View observability data",
    "observability.write": "Manage alerts and retention",
    "observability.admin": "Full observability access",
}

PERMISSION_TREE: dict[str, list[str]] = {
    "system": ["system.read", "system.admin"],
    "configuration": ["configuration.read", "configuration.write"],
    "dashboard": ["dashboard.read", "dashboard.admin"],
    "requests": ["requests.read", "requests.write", "requests.assign"],
    "managers": ["managers.read", "managers.write"],
    "audit": ["audit.read", "audit.export"],
    "workflow": ["workflow.read", "workflow.write"],
    "sdk": ["sdk.read", "sdk.write"],
    "plugins": ["plugins.read", "plugins.write"],
    "ai": ["ai.read", "ai.use", "ai.admin"],
    "realtime": [k for k in IAM_PERMISSIONS if k.startswith("realtime.")],
    "management": [
        "management.read",
        "management.write",
        "management.admin",
        "management.identity.read",
        "management.identity.write",
    ],
    "integrations": [
        "integrations.read",
        "integrations.write",
        "integrations.admin",
    ],
    "jobs": [
        "jobs.read",
        "jobs.write",
        "jobs.admin",
    ],
    "observability": [
        "observability.read",
        "observability.write",
        "observability.admin",
    ],
}

# Map IAM permissions → legacy permission engine codes (backward compat).
LEGACY_PERMISSION_MAP: dict[str, str] = {
    "configuration.read": "platform.config.read",
    "configuration.write": "platform.config.write",
    "dashboard.read": "analytics.view",
    "management.read": "api.access",
    "management.admin": "admin.access",
    "ai.use": "ai.use",
    "requests.read": "leads.view",
    "requests.write": "leads.create",
    "requests.assign": "leads.assign",
    "managers.read": "leads.view",
    "audit.read": "admin.access",
}

REALTIME_CHANNEL_PERMISSIONS: dict[str, str] = {
    "system": "realtime.channel.system",
    "dashboard": "realtime.channel.dashboard",
    "requests": "realtime.channel.requests",
    "workflows": "realtime.channel.workflows",
    "managers": "realtime.channel.managers",
    "audit": "realtime.channel.audit",
    "configuration": "realtime.channel.configuration",
    "notifications": "realtime.channel.notifications",
    "plugins": "realtime.channel.plugins",
    "ai": "realtime.channel.ai",
    "health": "realtime.channel.health",
}


class PermissionService:
    @staticmethod
    def list_permissions() -> dict[str, str]:
        return dict(IAM_PERMISSIONS)

    @staticmethod
    def permission_tree() -> dict[str, list[str]]:
        return dict(PERMISSION_TREE)

    @staticmethod
    def channel_permission(channel: str) -> str:
        perm = REALTIME_CHANNEL_PERMISSIONS.get(channel)
        if perm is None:
            raise KeyError(f"Unknown realtime channel: {channel}")
        return perm

    @staticmethod
    def legacy_code(iam_permission: str) -> str | None:
        return LEGACY_PERMISSION_MAP.get(iam_permission)

    @staticmethod
    async def resolve_user_permissions(
        telegram_id: int,
        roles: list[str],
    ) -> set[str]:
        """Merge role defaults with DB-assigned permissions."""
        from platform_identity.role_service import role_service

        perms: set[str] = set()
        for role in roles:
            perms.update(role_service.permissions_for_role(role))

        if telegram_id is not None:
            try:
                from platform_legacy import legacy

                for iam_code, legacy_code in LEGACY_PERMISSION_MAP.items():
                    if await legacy.permissions.user_has_permission(telegram_id, legacy_code):
                        perms.add(iam_code)
            except Exception:
                pass

        return perms


permission_service = PermissionService()
