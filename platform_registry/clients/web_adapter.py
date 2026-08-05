"""Web client adapter — groups shaped for Sidebar / intelligent nav."""

from __future__ import annotations

from typing import Any

from platform_registry.service import platform_registry
from platform_registry.visibility import ClientId


def web_navigation_groups(
    *,
    roles: list[str] | None = None,
    include_owner: bool = False,
    simple: bool = False,
) -> list[dict[str, Any]]:
    data = platform_registry.navigation_for(
        client=ClientId.WEB.value,
        roles=roles,
        include_owner=include_owner,
        simple=simple,
    )
    return list(data.get("groups") or [])


def web_navigation_payload(
    *,
    roles: list[str] | None = None,
    include_owner: bool = False,
    simple: bool = False,
) -> dict[str, Any]:
    return platform_registry.navigation_for(
        client=ClientId.WEB.value,
        roles=roles,
        include_owner=include_owner,
        simple=simple,
    )
