"""Platform state DTOs — versioning + conflict metadata (Sprint 34.2C)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class EntityMeta:
    """Optimistic versioning for every shared entity."""

    entity_type: str
    entity_id: str
    version: int = 1
    updated_at: str = field(default_factory=lambda: utcnow().isoformat())
    updated_by: str | None = None
    source_client: str | None = None  # web | telegram | desktop | mobile | api | ai

    def bump(self, *, updated_by: str | None = None, source_client: str | None = None) -> EntityMeta:
        self.version += 1
        self.updated_at = utcnow().isoformat()
        if updated_by is not None:
            self.updated_by = updated_by
        if source_client is not None:
            self.source_client = source_client
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StateSlice:
    slice_id: str
    revision: str
    data: dict[str, Any]
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "slice_id": self.slice_id,
            "revision": self.revision,
            "data": self.data,
            "meta": self.meta,
        }


@dataclass
class PlatformStateSnapshot:
    revision: str
    generated_at: str
    slices: dict[str, StateSlice]
    user_id: str | None = None
    telegram_id: int | None = None
    workspace_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sprint": "34.2C",
            "revision": self.revision,
            "generated_at": self.generated_at,
            "user_id": self.user_id,
            "telegram_id": self.telegram_id,
            "workspace_id": self.workspace_id,
            "slices": {k: v.to_dict() for k, v in self.slices.items()},
        }


def compute_revision(*parts: Any) -> str:
    raw = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# Canonical slice ids for PlatformState
SLICE_USERS = "users"
SLICE_SESSIONS = "sessions"
SLICE_CRM = "crm"
SLICE_TASKS = "tasks"
SLICE_CALENDAR = "calendar"
SLICE_NOTIFICATIONS = "notifications"
SLICE_FILES = "files"
SLICE_DOCUMENTS = "documents"
SLICE_CONVERSATIONS = "conversations"
SLICE_MEMORY = "memory"
SLICE_AGENTS = "agents"
SLICE_PROJECTS = "projects"
SLICE_ANALYTICS = "analytics"
SLICE_ACTIVITY = "activity"
SLICE_FAVORITES = "favorites"
SLICE_WORKSPACES = "workspaces"

ALL_SLICES: tuple[str, ...] = (
    SLICE_USERS,
    SLICE_SESSIONS,
    SLICE_CRM,
    SLICE_TASKS,
    SLICE_CALENDAR,
    SLICE_NOTIFICATIONS,
    SLICE_FILES,
    SLICE_DOCUMENTS,
    SLICE_CONVERSATIONS,
    SLICE_MEMORY,
    SLICE_AGENTS,
    SLICE_PROJECTS,
    SLICE_ANALYTICS,
    SLICE_ACTIVITY,
    SLICE_FAVORITES,
    SLICE_WORKSPACES,
)
