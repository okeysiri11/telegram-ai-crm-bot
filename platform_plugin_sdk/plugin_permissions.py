# Plugin permissions — declare and validate permissions from manifest.

from __future__ import annotations

from platform_plugin_sdk.exceptions import PluginPermissionError


class PluginPermissions:
    """Permission declarations and checks for a plugin."""

    def __init__(self, plugin_id: str, declared: list[str] | None = None) -> None:
        self.plugin_id = plugin_id
        self.declared = list(declared or [])

    def register(self, permission: str) -> None:
        full = self._normalize(permission)
        if full not in self.declared:
            self.declared.append(full)

    def validate_declared(self, required: list[str]) -> None:
        missing = [p for p in required if p not in self.declared]
        if missing:
            raise PluginPermissionError(
                f"Plugin {self.plugin_id} missing declared permissions: {', '.join(missing)}"
            )

    async def check(self, ctx: Any, permission: str) -> bool:
        from platform_plugin_sdk.plugin_api import IamApi

        iam = IamApi()
        principal = ctx.metadata.get("principal") if hasattr(ctx, "metadata") else None
        if principal is None:
            return False
        return await iam.authorize(principal, self._normalize(permission))

    def _normalize(self, permission: str) -> str:
        if "." in permission:
            return permission
        return f"{self.plugin_id}.{permission}"

    def to_manifest(self) -> list[str]:
        return list(self.declared)
