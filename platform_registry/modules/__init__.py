"""Platform modules registry — mirrors enterprise module ids."""

from __future__ import annotations

from dataclasses import dataclass

from platform_registry.workspaces import WORKSPACE_MODULE_REGISTRY


@dataclass(frozen=True)
class ModuleDef:
    id: str
    title: str
    route: str
    icon: str
    permissions: tuple[str, ...] = ()


def all_modules() -> list[ModuleDef]:
    return [
        ModuleDef(
            id=m.id,
            title=m.title,
            route=m.route,
            icon=m.icon,
            permissions=m.required_permissions,
        )
        for m in WORKSPACE_MODULE_REGISTRY.values()
    ]
