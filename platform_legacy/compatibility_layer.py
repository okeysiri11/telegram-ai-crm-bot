# CompatibilityLayer — transparent platform vs legacy routing.

from __future__ import annotations

import inspect
import logging
from typing import Any, Awaitable, Callable, TypeVar

from platform_legacy.coverage import migration_coverage
from platform_legacy.deprecation_manager import deprecation_manager
from platform_legacy.migration_manager import migration_manager

logger = logging.getLogger(__name__)

T = TypeVar("T")
AsyncFn = Callable[..., Awaitable[T]]
SyncFn = Callable[..., T]


class CompatibilityLayer:
    """Delegates to Platform Core or legacy adapters based on migration state + flags."""

    async def dispatch_async(
        self,
        subsystem: str,
        *,
        platform_fn: AsyncFn[T],
        legacy_fn: AsyncFn[T],
        method: str = "",
        **kwargs: Any,
    ) -> T:
        if migration_manager.should_route_to_legacy(subsystem):
            deprecation_manager.warn_legacy_route(subsystem, method=method)
            migration_coverage.record_legacy(subsystem, method=method or "dispatch_async")
            return await legacy_fn(**kwargs)
        migration_coverage.record_platform(subsystem, method=method or "dispatch_async")
        return await platform_fn(**kwargs)

    def dispatch_sync(
        self,
        subsystem: str,
        *,
        platform_fn: SyncFn[T],
        legacy_fn: SyncFn[T],
        method: str = "",
        **kwargs: Any,
    ) -> T:
        if migration_manager.should_route_to_legacy(subsystem):
            deprecation_manager.warn_legacy_route(subsystem, method=method)
            migration_coverage.record_legacy(subsystem, method=method or "dispatch_sync")
            return legacy_fn(**kwargs)
        migration_coverage.record_platform(subsystem, method=method or "dispatch_sync")
        return platform_fn(**kwargs)

    async def dispatch(
        self,
        subsystem: str,
        *,
        platform_fn: Callable[..., Any],
        legacy_fn: Callable[..., Any],
        method: str = "",
        **kwargs: Any,
    ) -> Any:
        if inspect.iscoroutinefunction(platform_fn) or inspect.iscoroutinefunction(legacy_fn):
            return await self.dispatch_async(
                subsystem,
                platform_fn=platform_fn,
                legacy_fn=legacy_fn,
                method=method,
                **kwargs,
            )
        return self.dispatch_sync(
            subsystem,
            platform_fn=platform_fn,
            legacy_fn=legacy_fn,
            method=method,
            **kwargs,
        )


compatibility_layer = CompatibilityLayer()


async def user_has_permission(
    telegram_id: int,
    permission_code: str,
) -> bool:
    """Route permission checks: Platform IAM default, legacy PG on compatibility flag."""

    async def _platform() -> bool:
        from platform_identity.identity_service import identity_service
        from platform_identity.permission_service import LEGACY_PERMISSION_MAP

        principal = await identity_service.authenticate_telegram(telegram_id)
        if principal.is_owner:
            return True
        for iam_code, mapped_legacy in LEGACY_PERMISSION_MAP.items():
            if mapped_legacy == permission_code:
                return await identity_service.authorize(principal, iam_code)
        return False

    async def _legacy() -> bool:
        from platform_legacy.registry import legacy_registry

        return await legacy_registry.get("permissions").user_has_permission(
            telegram_id,
            permission_code,
        )

    return await compatibility_layer.dispatch_async(
        "users",
        platform_fn=_platform,
        legacy_fn=_legacy,
        method="user_has_permission",
    )
