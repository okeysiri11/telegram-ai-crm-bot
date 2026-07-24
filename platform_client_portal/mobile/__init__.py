"""Mobile-first targets — Sprint 22.8."""

from __future__ import annotations

from typing import Any

from platform_client_portal.models import MOBILE_PLATFORMS


class MobileExperience:
    def manifest(self) -> dict[str, Any]:
        return {
            "mobile_first": True,
            "platforms": list(MOBILE_PLATFORMS),
            "android": True,
            "ios": True,
            "pwa": True,
            "responsive": True,
        }
