# Configuration change handler — hot-reload side effects without restart.

from __future__ import annotations

import logging

from events.configuration_events import ConfigurationChangedEvent
from platform_configuration.config_provider import config_provider

logger = logging.getLogger(__name__)


class ConfigurationEventHandler:
    @staticmethod
    async def handle(event: ConfigurationChangedEvent) -> None:
        if event.section == "workflow" or event.config_key.startswith("workflow."):
            await ConfigurationEventHandler._maybe_reload_workflows()
        if event.config_key.startswith("feature_flags.verticals."):
            logger.info(
                "vertical_feature_flag_changed key=%s value=%s",
                event.config_key,
                event.new_value,
            )

    @staticmethod
    async def _maybe_reload_workflows() -> None:
        if not config_provider.is_feature_enabled("workflow.definitions_auto_reload", default=False):
            return
        try:
            from platform_sdk.workflow_loader import sdk_workflow_loader

            count = sdk_workflow_loader.reload()
            logger.info("workflow_definitions_reloaded count=%s", count)
        except Exception:
            logger.warning("workflow_definitions_reload_failed", exc_info=True)
