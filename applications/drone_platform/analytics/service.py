from __future__ import annotations

from typing import Any

from applications.drone_platform.shared.store import DroneStore, drone_store


class AnalyticsService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def overview(self) -> dict[str, Any]:
        return {
            "uavs": self.store.uavs.count(),
            "components": self.store.components.count(),
            "projects": self.store.projects.count(),
            "firmware_projects": self.store.firmware_projects.count(),
            "missions": self.store.missions.count(),
            "stock_items": self.store.stock_items.count(),
            "documents": self.store.documents.count(),
            "ai_sessions": self.store.ai_sessions.count(),
        }


analytics_service = AnalyticsService()
