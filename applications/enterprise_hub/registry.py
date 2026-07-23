"""Enterprise registry — platforms, services, modules, integrations, orgs, environments."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterpriseRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.known_platforms = list(DEFAULT_CONFIG.known_platforms)
        self.environment_types = list(DEFAULT_CONFIG.environment_types)

    def register_platform(
        self, *, name: str, version: str = "1.0", status: str = "connected"
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        pid = _id("hub_plat")
        return self.store.platforms.save(
            pid,
            {
                "platform_id": pid,
                "name": name.lower(),
                "version": version,
                "status": status,
                "at": _now(),
            },
        )

    def register_service(
        self, *, name: str, platform: str, endpoint: str = ""
    ) -> dict[str, Any]:
        if not name or not platform:
            raise ValidationError("name and platform required")
        sid = _id("hub_svc")
        return self.store.services.save(
            sid,
            {
                "service_id": sid,
                "name": name,
                "platform": platform.lower(),
                "endpoint": endpoint,
                "at": _now(),
            },
        )

    def register_module(
        self, *, name: str, platform: str, sprint: str = ""
    ) -> dict[str, Any]:
        if not name or not platform:
            raise ValidationError("name and platform required")
        mid = _id("hub_mod")
        return self.store.modules.save(
            mid,
            {
                "module_id": mid,
                "name": name,
                "platform": platform.lower(),
                "sprint": sprint,
                "at": _now(),
            },
        )

    def register_integration(
        self, *, source: str, target: str, protocol: str = "event_bus"
    ) -> dict[str, Any]:
        if not source or not target:
            raise ValidationError("source and target required")
        iid = _id("hub_int")
        return self.store.integrations.save(
            iid,
            {
                "integration_id": iid,
                "source": source.lower(),
                "target": target.lower(),
                "protocol": protocol,
                "status": "active",
                "at": _now(),
            },
        )

    def register_organization(
        self, *, name: str, org_code: str = "", jurisdiction: str = ""
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        oid = _id("hub_org")
        return self.store.organizations.save(
            oid,
            {
                "organization_id": oid,
                "name": name,
                "org_code": org_code or oid,
                "jurisdiction": jurisdiction,
                "at": _now(),
            },
        )

    def register_environment(
        self, *, name: str, env_type: str = "production", profile: str = ""
    ) -> dict[str, Any]:
        et = env_type.lower().strip()
        if et not in self.environment_types:
            raise ValidationError(f"env_type must be one of {self.environment_types}")
        if not name:
            raise ValidationError("name required")
        eid = _id("hub_env")
        return self.store.environments.save(
            eid,
            {
                "environment_id": eid,
                "name": name,
                "env_type": et,
                "profile": profile or et,
                "status": "active",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "platforms": self.store.platforms.count(),
            "services": self.store.services.count(),
            "modules": self.store.modules.count(),
            "integrations": self.store.integrations.count(),
            "organizations": self.store.organizations.count(),
            "environments": self.store.environments.count(),
            "known_platforms": self.known_platforms,
        }
