"""Sprint 34.2A — Identity registries package."""

from platform_identity.registries.permission_registry import (
    PERMISSION_REGISTRY,
    ROLE_PERMISSION_DEFAULTS,
    all_permission_codes,
    defaults_for_roles,
    expand_permissions,
    normalize_permission,
)
from platform_identity.registries.role_registry import (
    ROLE_REGISTRY,
    CanonicalRole,
    all_role_codes,
    normalize_role,
    normalize_roles,
    role_definition,
)
from platform_identity.registries.workspace_registry import (
    WORKSPACE_REGISTRY,
    all_workspaces,
    normalize_workspace_codes,
    workspace_by_code,
)

__all__ = [
    "CanonicalRole",
    "PERMISSION_REGISTRY",
    "ROLE_PERMISSION_DEFAULTS",
    "ROLE_REGISTRY",
    "WORKSPACE_REGISTRY",
    "all_permission_codes",
    "all_role_codes",
    "all_workspaces",
    "defaults_for_roles",
    "expand_permissions",
    "normalize_permission",
    "normalize_role",
    "normalize_roles",
    "normalize_workspace_codes",
    "role_definition",
    "workspace_by_code",
]
