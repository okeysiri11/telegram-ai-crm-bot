"""Service permission resolver — enforce API / event / storage / AI / integration scopes."""

from __future__ import annotations

from platform_service_builder.models import ServiceDefinition, ServicePermissions


class ServicePermissionDenied(PermissionError):
    def __init__(self, service_id: str, scope: str, resource: str) -> None:
        super().__init__(f"Service {service_id} denied {scope}:{resource}")
        self.service_id = service_id
        self.scope = scope
        self.resource = resource


class ServicePermissionResolver:
    WILDCARD = "*"

    def permissions_for(self, definition: ServiceDefinition) -> ServicePermissions:
        return definition.manifest.permissions

    def _allowed(self, allowed: list[str], resource: str) -> bool:
        if not allowed:
            return False
        if self.WILDCARD in allowed:
            return True
        if resource in allowed:
            return True
        for pattern in allowed:
            if pattern.endswith(".*") and resource.startswith(pattern[:-1]):
                return True
            if pattern.endswith("*") and resource.startswith(pattern[:-1]):
                return True
        return False

    def check_api(self, definition: ServiceDefinition, api: str) -> bool:
        return self._allowed(definition.manifest.permissions.allowed_apis, api)

    def check_event(self, definition: ServiceDefinition, event: str) -> bool:
        return self._allowed(definition.manifest.permissions.allowed_events, event)

    def check_storage(self, definition: ServiceDefinition, storage: str) -> bool:
        return self._allowed(definition.manifest.permissions.allowed_storage, storage)

    def check_ai_tool(self, definition: ServiceDefinition, tool: str) -> bool:
        return self._allowed(definition.manifest.permissions.allowed_ai_tools, tool)

    def check_integration(self, definition: ServiceDefinition, integration: str) -> bool:
        return self._allowed(definition.manifest.permissions.allowed_integrations, integration)

    def require(self, definition: ServiceDefinition, scope: str, resource: str) -> None:
        checkers = {
            "api": self.check_api,
            "event": self.check_event,
            "storage": self.check_storage,
            "ai_tool": self.check_ai_tool,
            "integration": self.check_integration,
        }
        fn = checkers.get(scope)
        if fn is None:
            raise ValueError(f"unknown permission scope: {scope}")
        if not fn(definition, resource):
            raise ServicePermissionDenied(definition.id, scope, resource)

    def evaluate(
        self,
        definition: ServiceDefinition,
        *,
        api: str | None = None,
        event: str | None = None,
        storage: str | None = None,
        ai_tool: str | None = None,
        integration: str | None = None,
    ) -> dict[str, bool]:
        result: dict[str, bool] = {}
        if api is not None:
            result["api"] = self.check_api(definition, api)
        if event is not None:
            result["event"] = self.check_event(definition, event)
        if storage is not None:
            result["storage"] = self.check_storage(definition, storage)
        if ai_tool is not None:
            result["ai_tool"] = self.check_ai_tool(definition, ai_tool)
        if integration is not None:
            result["integration"] = self.check_integration(definition, integration)
        return result


permission_resolver = ServicePermissionResolver()
