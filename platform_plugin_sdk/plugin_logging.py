# Namespaced plugin logging.

from __future__ import annotations

import logging
from typing import Any


class PluginLogger:
    """Structured logger scoped to a plugin — never logs other plugins' data."""

    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id
        self._logger = logging.getLogger(f"plugin.{plugin_id}")

    def info(self, message: str, **extra: Any) -> None:
        self._logger.info(message, extra={"plugin_id": self.plugin_id, **extra})

    def warning(self, message: str, **extra: Any) -> None:
        self._logger.warning(message, extra={"plugin_id": self.plugin_id, **extra})

    def error(self, message: str, **extra: Any) -> None:
        self._logger.error(message, extra={"plugin_id": self.plugin_id, **extra})

    def debug(self, message: str, **extra: Any) -> None:
        self._logger.debug(message, extra={"plugin_id": self.plugin_id, **extra})
