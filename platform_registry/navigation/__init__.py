"""Navigation helpers — filter Menu Catalog for a principal / client."""

from __future__ import annotations

from typing import Any

from platform_identity.registries.role_registry import normalize_roles
from platform_registry.features import is_feature_enabled
from platform_registry.menus import MENU_CATALOG, MENU_GROUPS, MenuItem
from platform_registry.permissions import normalize_platform_permission, permissions_for_roles
from platform_registry.visibility import visible_on


def _perm_ok(item: MenuItem, granted: set[str]) -> bool:
    if not item.required_permissions:
        return True
    for p in item.required_permissions:
        canon = normalize_platform_permission(p) or p
        if canon in granted or p in granted:
            return True
        # owner.full_access implies all
        if "owner.full_access" in granted or "owner.full" in granted:
            return True
    return False


def _role_ok(item: MenuItem, roles: set[str]) -> bool:
    if not item.required_roles:
        return True
    if "owner" in roles or "ceo" in roles:
        return True
    return bool(roles.intersection(item.required_roles))


def filter_menu(
    *,
    client: str,
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
    feature_overrides: dict[str, bool] | None = None,
    include_owner: bool = False,
    simple: bool = False,
) -> list[MenuItem]:
    """Return menu items visible for this client + authorization context."""
    role_list = normalize_roles(roles or [])
    role_set = set(role_list)
    if include_owner:
        role_set.add("owner")
    granted = set(permissions or [])
    if not granted:
        granted = set(permissions_for_roles(list(role_set) or ["guest"]))

    out: list[MenuItem] = []
    for item in MENU_CATALOG:
        if not visible_on(item.client_visibility, client):
            continue
        if item.owner_only and "owner" not in role_set and "ceo" not in role_set and not include_owner:
            continue
        if simple and not item.simple and not item.owner_only:
            # In simple mode keep simple items; verticals still show for managers+
            if item.group == "verticals" and role_set.intersection(
                {"owner", "ceo", "administrator", "manager", "dealer", "partner"}
            ):
                pass
            elif not item.simple:
                continue
        if not _role_ok(item, role_set):
            continue
        if not _perm_ok(item, granted):
            continue
        if any(not is_feature_enabled(flag, feature_overrides) for flag in item.feature_flags):
            continue
        out.append(item)
    return out


def group_menu(items: list[MenuItem]) -> list[dict[str, Any]]:
    """Group filtered items for Web accordion / similar UIs."""
    buckets: dict[str, list[MenuItem]] = {}
    for item in items:
        g = item.group or "workspace"
        buckets.setdefault(g, []).append(item)

    groups: list[dict[str, Any]] = []
    for gid, meta in MENU_GROUPS.items():
        children = buckets.get(gid)
        if not children:
            continue
        groups.append(
            {
                "id": gid,
                "label": meta["label"],
                "label_en": meta["label_en"],
                "icon": meta["icon"],
                "owner_only": gid == "owner",
                "simple": gid in {"workspace", "business", "ai"},
                "items": [c.to_dict() for c in children],
            }
        )
    return groups
