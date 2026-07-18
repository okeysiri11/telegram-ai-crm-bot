# PluginContext — SDK surface exposed to plugins (core-agnostic).

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from aiohttp import web

logger = logging.getLogger(__name__)

PLATFORM_VERSION = "1.0.0"


@dataclass
class PluginContext:
    """Sandboxed platform API for a single plugin instance."""

    plugin_id: str
    plugin_version: str
    config: dict[str, Any] = field(default_factory=dict)
    _app: web.Application | None = field(default=None, repr=False)

    def bind_app(self, app: web.Application) -> None:
        self._app = app

    # ---- SDK ----

    @property
    def sdk(self) -> Any:
        from platform_sdk.vertical_builder import vertical_builder

        return vertical_builder.create_context(plugin_id=self.plugin_id)

    # ---- Configuration ----

    @property
    def configuration(self) -> Any:
        from platform_configuration.config_provider import config_provider

        return config_provider

    def get_config(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    # ---- EventBus ----

    @property
    def events(self) -> Any:
        from events.event_bus import PlatformEventBus

        return PlatformEventBus

    async def publish(self, event: Any) -> None:
        await self.events.publish(event)

    # ---- Jobs ----

    @property
    def jobs(self) -> Any:
        from platform_jobs.job_engine import job_engine

        return job_engine

    # ---- Realtime ----

    @property
    def realtime(self) -> Any:
        from platform_realtime.connection_hub import connection_hub

        return connection_hub

    # ---- IAM ----

    @property
    def iam(self) -> Any:
        from platform_identity.identity_service import identity_service

        return identity_service

    # ---- Integrations ----

    @property
    def integrations(self) -> Any:
        from platform_integrations.integration_service import integration_service

        return integration_service

    # ---- Observability ----

    @property
    def observability(self) -> Any:
        from platform_observability.metrics_service import metrics_service

        return metrics_service

    # ---- Management API metadata ----

    @property
    def management(self) -> dict[str, str]:
        return {
            "prefix": "/management",
            "plugins": "/management/plugins",
            "dashboard": "/management/dashboard",
        }

    def log(self, message: str) -> None:
        logger.info("plugin_%s %s", self.plugin_id, message)
