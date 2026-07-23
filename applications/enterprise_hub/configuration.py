"""Enterprise configuration — global config, feature flags, settings, profiles."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterpriseConfiguration:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def set_global(self, *, key: str, value: Any) -> dict[str, Any]:
        if not key:
            raise ValidationError("key required")
        cid = _id("hub_cfg")
        return self.store.global_config.save(
            cid,
            {"config_id": cid, "key": key, "value": value, "at": _now()},
        )

    def set_feature_flag(self, *, name: str, enabled: bool = False, scope: str = "global") -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        fid = _id("hub_ff")
        return self.store.feature_flags.save(
            fid,
            {
                "flag_id": fid,
                "name": name,
                "enabled": bool(enabled),
                "scope": scope,
                "at": _now(),
            },
        )

    def set_platform_setting(
        self, *, platform: str, key: str, value: Any
    ) -> dict[str, Any]:
        if not platform or not key:
            raise ValidationError("platform and key required")
        sid = _id("hub_pset")
        return self.store.platform_settings.save(
            sid,
            {
                "setting_id": sid,
                "platform": platform.lower(),
                "key": key,
                "value": value,
                "at": _now(),
            },
        )

    def register_profile(
        self, *, name: str, env_type: str = "production", settings: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        pid = _id("hub_prof")
        return self.store.env_profiles.save(
            pid,
            {
                "profile_id": pid,
                "name": name,
                "env_type": env_type,
                "settings": settings or {},
                "at": _now(),
            },
        )

    def register_config(
        self, *, name: str, category: str = "general", payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        rid = _id("hub_creg")
        return self.store.config_registry.save(
            rid,
            {
                "registry_id": rid,
                "name": name,
                "category": category,
                "payload": payload or {},
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "global_config": self.store.global_config.count(),
            "feature_flags": self.store.feature_flags.count(),
            "platform_settings": self.store.platform_settings.count(),
            "env_profiles": self.store.env_profiles.count(),
            "config_registry": self.store.config_registry.count(),
        }
