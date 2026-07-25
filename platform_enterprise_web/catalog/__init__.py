"""Web catalogs — layouts, nav, UI, i18n, dashboard — Sprint 26.1."""

from __future__ import annotations

from typing import Any

from platform_enterprise_web.models import (
    DASHBOARD_WIDGETS,
    LAYOUTS,
    LOCALES,
    NAVIGATION,
    UI_COMPONENTS,
)


class WebCatalog:
    def inventory(self) -> dict[str, Any]:
        return {
            "layouts": list(LAYOUTS),
            "navigation": list(NAVIGATION),
            "ui_components": list(UI_COMPONENTS),
            "locales": list(LOCALES),
            "dashboard_widgets": list(DASHBOARD_WIDGETS),
            "theme_modes": ["light", "dark", "system"],
            "ui_count": len(UI_COMPONENTS),
            "passed": True,
        }
