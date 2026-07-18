# DeprecationManager — official legacy deprecation warnings and API tracking.

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from platform_legacy.registry import legacy_registry

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DeprecatedApi:
    name: str
    subsystem: str
    replacement: str
    deprecated_since: str = "2026-07"
    removal_target: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "subsystem": self.subsystem,
            "replacement": self.replacement,
            "deprecated_since": self.deprecated_since,
            "removal_target": self.removal_target,
        }


_OFFICIAL_DEPRECATED: dict[str, DeprecatedApi] = {
    "handlers.router": DeprecatedApi(
        "handlers.router",
        "telegram",
        "platform_sdk + platform_workflows",
    ),
    "database_legacy": DeprecatedApi(
        "database_legacy",
        "repositories",
        "repositories.* + database.session",
    ),
    "services.pg_*": DeprecatedApi(
        "services.pg_*",
        "requests",
        "platform_legacy adapters → platform services",
    ),
    "openrouter.ask_openrouter": DeprecatedApi(
        "openrouter.ask_openrouter",
        "ai",
        "platform_ai.llm",
    ),
}


class DeprecationManager:
    def __init__(self) -> None:
        self._warned: set[str] = set()
        self._apis = dict(_OFFICIAL_DEPRECATED)

    def register(self, api: DeprecatedApi) -> None:
        self._apis[api.name] = api

    def list_deprecated(self) -> list[dict[str, Any]]:
        hits = legacy_registry.metrics.deprecated_api_hits
        out: list[dict[str, Any]] = []
        for name, api in sorted(self._apis.items()):
            out.append({**api.to_dict(), "hit_count": hits.get(name, 0)})
        return out

    def warn_legacy_route(self, subsystem: str, *, method: str = "") -> None:
        key = f"{subsystem}:{method}" if method else subsystem
        if key in self._warned:
            return
        self._warned.add(key)
        message = (
            f"Legacy compatibility path for subsystem '{subsystem}'"
            + (f".{method}" if method else "")
            + " is deprecated — migrate to Platform Core."
        )
        logger.warning(message)
        warnings.warn(message, DeprecationWarning, stacklevel=4)
        legacy_registry.record_deprecated(key)

    def mark_api_used(self, api_name: str) -> None:
        legacy_registry.record_deprecated(api_name)
        api = self._apis.get(api_name)
        if api:
            logger.debug("deprecated_api_used name=%s subsystem=%s", api_name, api.subsystem)


deprecation_manager = DeprecationManager()
