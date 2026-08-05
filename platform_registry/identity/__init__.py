"""Re-export Sprint 34.2A identity registries — single source, no copies."""

from platform_identity.registries import (  # noqa: F401
    ROLE_REGISTRY,
    PERMISSION_REGISTRY,
    WORKSPACE_REGISTRY as IDENTITY_VERTICAL_WORKSPACES,
    CanonicalRole,
    all_permission_codes,
    all_role_codes,
    defaults_for_roles,
    expand_permissions,
    normalize_permission,
    normalize_role,
    normalize_roles,
    normalize_workspace_codes,
    role_definition,
)

__all__ = [
    "ROLE_REGISTRY",
    "PERMISSION_REGISTRY",
    "IDENTITY_VERTICAL_WORKSPACES",
    "CanonicalRole",
    "all_permission_codes",
    "all_role_codes",
    "defaults_for_roles",
    "expand_permissions",
    "normalize_permission",
    "normalize_role",
    "normalize_roles",
    "normalize_workspace_codes",
    "role_definition",
]
