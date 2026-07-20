# Maintenance mode.

from __future__ import annotations

import time
from typing import Any


class MaintenanceService:
    def __init__(self) -> None:
        self._enabled = False
        self._message = "Auto Marketplace is undergoing scheduled maintenance."
        self._enabled_at: float | None = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self, *, message: str = "") -> dict[str, Any]:
        self._enabled = True
        self._enabled_at = time.time()
        if message:
            self._message = message
        return self.status()

    def disable(self) -> dict[str, Any]:
        self._enabled = False
        self._enabled_at = None
        return self.status()

    def status(self) -> dict[str, Any]:
        return {
            "maintenance_mode": self._enabled,
            "message": self._message if self._enabled else "",
            "enabled_at": self._enabled_at,
        }


maintenance_service = MaintenanceService()
