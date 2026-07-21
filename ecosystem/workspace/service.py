# Workspace service — unified dashboard and activity.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ecosystem.config import DEFAULT_CONFIG
from ecosystem.shared.store import EcosystemStore, ecosystem_store


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


@dataclass
class ActivityEntry:
    activity_id: str = field(default_factory=_id)
    user_id: str = ""
    workspace_id: str = ""
    application_id: str = ""
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            "user_id": self.user_id,
            "workspace_id": self.workspace_id,
            "application_id": self.application_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class WorkspaceFavorite:
    favorite_id: str = field(default_factory=_id)
    user_id: str = ""
    item_type: str = ""
    item_id: str = ""
    label: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "favorite_id": self.favorite_id,
            "user_id": self.user_id,
            "item_type": self.item_type,
            "item_id": self.item_id,
            "label": self.label,
            "created_at": self.created_at,
        }


@dataclass
class WorkspaceNotification:
    notification_id: str = field(default_factory=_id)
    user_id: str = ""
    title: str = ""
    body: str = ""
    source_application: str = ""
    read: bool = False
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "title": self.title,
            "body": self.body,
            "source_application": self.source_application,
            "read": self.read,
            "created_at": self.created_at,
        }


class WorkspaceService:
    QUICK_ACTIONS = [
        {"id": "search", "label": "Global Search", "route": "/workspace/search"},
        {"id": "assistant", "label": "AI Assistant", "route": "/workspace/assistant"},
        {"id": "auto_marketplace", "label": "Auto Marketplace", "route": "/apps/auto_marketplace"},
        {"id": "notifications", "label": "Notifications", "route": "/workspace/notifications"},
    ]

    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def dashboard(self, user_id: str, *, workspace_id: str = "") -> dict[str, Any]:
        return {
            "user_id": user_id,
            "workspace_id": workspace_id,
            "applications": DEFAULT_CONFIG.registered_applications,
            "recent_activity": self.recent_activity(user_id, workspace_id=workspace_id, limit=10),
            "notifications_unread": len([n for n in self.notifications(user_id) if not n.read]),
            "favorites_count": len(self.favorites(user_id)),
            "quick_actions": list(self.QUICK_ACTIONS),
        }

    def record_activity(
        self,
        user_id: str,
        action: str,
        *,
        workspace_id: str = "",
        application_id: str = "",
        resource_type: str = "",
        resource_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ActivityEntry:
        entry = ActivityEntry(
            user_id=user_id,
            workspace_id=workspace_id,
            application_id=application_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata or {},
        )
        self._store.activities.save(entry.activity_id, entry)
        return entry

    def recent_activity(self, user_id: str, *, workspace_id: str = "", limit: int = 20) -> list[ActivityEntry]:
        entries = [a for a in self._store.activities.list_all() if a.user_id == user_id]
        if workspace_id:
            entries = [a for a in entries if a.workspace_id in ("", workspace_id)]
        return sorted(entries, key=lambda e: e.created_at, reverse=True)[:limit]

    def global_search(self, user_id: str, query: str) -> dict[str, Any]:
        query_lower = query.lower()
        results: list[dict[str, Any]] = []
        for app in DEFAULT_CONFIG.registered_applications:
            results.append({"type": "application", "application_id": app, "title": app.replace("_", " ").title(), "score": 1.0})
        for fav in self.favorites(user_id):
            if query_lower in fav.label.lower():
                results.append({"type": "favorite", **fav.to_dict(), "score": 0.9})
        for activity in self.recent_activity(user_id, limit=50):
            if query_lower in activity.action.lower() or query_lower in activity.application_id.lower():
                results.append({"type": "activity", **activity.to_dict(), "score": 0.7})
        return {"query": query, "results": sorted(results, key=lambda r: r.get("score", 0), reverse=True)}

    def add_favorite(self, user_id: str, item_type: str, item_id: str, *, label: str = "") -> WorkspaceFavorite:
        fav = WorkspaceFavorite(user_id=user_id, item_type=item_type, item_id=item_id, label=label or item_id)
        self._store.favorites.save(fav.favorite_id, fav)
        return fav

    def favorites(self, user_id: str) -> list[WorkspaceFavorite]:
        return [f for f in self._store.favorites.list_all() if f.user_id == user_id]

    def send_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        *,
        source_application: str = "ecosystem",
    ) -> WorkspaceNotification:
        notification = WorkspaceNotification(
            user_id=user_id,
            title=title,
            body=body,
            source_application=source_application,
        )
        self._store.notifications.save(notification.notification_id, notification)
        return notification

    def notifications(self, user_id: str) -> list[WorkspaceNotification]:
        return sorted(
            [n for n in self._store.notifications.list_all() if n.user_id == user_id],
            key=lambda n: n.created_at,
            reverse=True,
        )

    def quick_actions(self) -> list[dict[str, str]]:
        return list(self.QUICK_ACTIONS)


workspace_service = WorkspaceService()
