"""Installation packages — Sprint 21.8."""

from __future__ import annotations

from typing import Any


class Installers:
    def package(self) -> dict[str, Any]:
        return {
            "installers": ["offline", "online", "airgap"],
            "upgrade_path": "5.x -> 6.0.0",
            "passed": True,
        }
