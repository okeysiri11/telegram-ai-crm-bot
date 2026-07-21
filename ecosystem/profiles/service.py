# Unified profile service — cross-application user profile.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ecosystem.shared.exceptions import NotFoundError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


@dataclass
class UnifiedProfile:
    profile_id: str = field(default_factory=_id)
    user_id: str = ""
    first_name: str = ""
    last_name: str = ""
    avatar_url: str = ""
    locale: str = "en"
    timezone: str = "UTC"
    phone: str = ""
    preferences: dict[str, Any] = field(default_factory=dict)
    application_links: dict[str, str] = field(default_factory=dict)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "avatar_url": self.avatar_url,
            "locale": self.locale,
            "timezone": self.timezone,
            "phone": self.phone,
            "preferences": dict(self.preferences),
            "application_links": dict(self.application_links),
            "updated_at": self.updated_at,
        }


class ProfileService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def get_or_create(self, user_id: str) -> UnifiedProfile:
        for profile in self._store.profiles.list_all():
            if profile.user_id == user_id:
                return profile
        profile = UnifiedProfile(user_id=user_id)
        self._store.profiles.save(profile.profile_id, profile)
        return profile

    def update(self, user_id: str, **fields: Any) -> UnifiedProfile:
        profile = self.get_or_create(user_id)
        for key, value in fields.items():
            if hasattr(profile, key) and key not in ("profile_id", "user_id"):
                setattr(profile, key, value)
        profile.updated_at = _ts()
        self._store.profiles.save(profile.profile_id, profile)
        return profile

    def link_application(self, user_id: str, application_id: str, external_id: str) -> UnifiedProfile:
        profile = self.get_or_create(user_id)
        profile.application_links[application_id] = external_id
        profile.updated_at = _ts()
        self._store.profiles.save(profile.profile_id, profile)
        return profile

    def get(self, user_id: str) -> UnifiedProfile:
        profile = next((p for p in self._store.profiles.list_all() if p.user_id == user_id), None)
        if profile is None:
            raise NotFoundError("Profile", user_id)
        return profile


profile_service = ProfileService()
