"""Enterprise Service Builder — Sprint 36.0 public exports."""

from __future__ import annotations

from typing import Any

__all__ = [
    "ServiceBuilderService",
    "service_builder",
    "ServiceRegistry",
    "ServiceDefinition",
    "ServiceManifest",
    "ServiceVersion",
    "ServiceState",
    "ServiceLifecycleManager",
    "ServiceDependencyResolver",
    "ServiceLoader",
    "ServiceSandbox",
    "ServiceHealthChecker",
    "ServiceConfiguration",
    "ServicePermissionResolver",
]


def __getattr__(name: str) -> Any:
    if name in {"ServiceBuilderService", "service_builder"}:
        from platform_service_builder.service import ServiceBuilderService, service_builder

        return ServiceBuilderService if name == "ServiceBuilderService" else service_builder
    if name == "ServiceRegistry":
        from platform_service_builder.registry import ServiceRegistry

        return ServiceRegistry
    if name in {
        "ServiceDefinition",
        "ServiceManifest",
        "ServiceVersion",
        "ServiceState",
        "ServiceConfiguration",
    }:
        from platform_service_builder import models as _models

        return getattr(_models, name)
    if name == "ServiceLifecycleManager":
        from platform_service_builder.lifecycle import ServiceLifecycleManager

        return ServiceLifecycleManager
    if name == "ServiceDependencyResolver":
        from platform_service_builder.dependency import ServiceDependencyResolver

        return ServiceDependencyResolver
    if name == "ServiceLoader":
        from platform_service_builder.loader import ServiceLoader

        return ServiceLoader
    if name == "ServiceSandbox":
        from platform_service_builder.sandbox import ServiceSandbox

        return ServiceSandbox
    if name == "ServiceHealthChecker":
        from platform_service_builder.health import ServiceHealthChecker

        return ServiceHealthChecker
    if name == "ServicePermissionResolver":
        from platform_service_builder.permissions import ServicePermissionResolver

        return ServicePermissionResolver
    raise AttributeError(f"module 'platform_service_builder' has no attribute {name!r}")
