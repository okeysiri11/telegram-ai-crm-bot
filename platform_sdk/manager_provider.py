# ManagerProvider — resolve managers via Smart Assignment (extensible strategies).

from __future__ import annotations

import logging
from typing import Any, Protocol

from platform_configuration.config_provider import config_provider

logger = logging.getLogger(__name__)


class ManagerStrategy(str):
    SMART = "SMART"
    ROUND_ROBIN = "ROUND_ROBIN"
    LEAST_LOADED = "LEAST_LOADED"
    PRIORITY = "PRIORITY"
    WEIGHTED = "WEIGHTED"
    MANUAL = "MANUAL"


class ManagerResolver(Protocol):
    async def assign_for_request(self, **kwargs: Any) -> dict[str, Any] | None: ...


class ManagerProvider:
    """Resolve managers for a vertical without hardcoded IDs."""

    def __init__(self, *, default_strategy: str | None = None) -> None:
        self.default_strategy = default_strategy or config_provider.assignment_mode()

    async def resolve_manager(
        self,
        vertical: str,
        request: dict[str, Any] | None = None,
        *,
        strategy: str | None = None,
        exclude_telegram_ids: set[int] | None = None,
    ) -> dict[str, Any] | None:
        chosen = (strategy or self.default_strategy).upper()

        if chosen == ManagerStrategy.MANUAL:
            manual_tid = (request or {}).get("manager_telegram_id")
            if manual_tid is None:
                return None
            from services.manager_service import manager_service

            return await manager_service.resolve_manual_manager(int(manual_tid))

        resolver = self._get_resolver(chosen)
        return await resolver.assign_for_request(
            vertical=vertical,
            request_type=(request or {}).get("request_type"),
            request_id=(request or {}).get("id"),
            request_number=(request or {}).get("request_number"),
            exclude_telegram_ids=exclude_telegram_ids,
        )

    def _get_resolver(self, strategy: str) -> ManagerResolver:
        if strategy in {ManagerStrategy.SMART, ManagerStrategy.ROUND_ROBIN, ManagerStrategy.LEAST_LOADED,
                        ManagerStrategy.PRIORITY, ManagerStrategy.WEIGHTED}:
            from services.smart_assignment_service import smart_assignment_service

            return smart_assignment_service

        from services.manager_service import manager_service

        return _ManagerServiceAdapter(manager_service)


class _ManagerServiceAdapter:
    def __init__(self, service) -> None:
        self._service = service

    async def assign_for_request(self, **kwargs: Any) -> dict[str, Any] | None:
        return await self._service.resolve_manager_for_vertical(
            kwargs.get("vertical") or "",
            request_type=kwargs.get("request_type"),
            request_id=kwargs.get("request_id"),
            request_number=kwargs.get("request_number"),
        )


manager_provider = ManagerProvider()
