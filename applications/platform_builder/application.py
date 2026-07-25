"""Platform Builder application facade — Sprint 28.1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from applications.platform_builder.academy import BuilderAcademy
from applications.platform_builder.builder_engine import BuilderEngine
from applications.platform_builder.catalog import BUILDERS, menu_for_role
from applications.platform_builder.config import DEFAULT_CONFIG, PlatformBuilderConfig
from applications.platform_builder.god_mode import PLATFORM_OWNER_ROLE, GodMode, is_platform_owner
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store

ROOT = Path(__file__).resolve().parents[2]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PlatformBuilderApplication:
    def __init__(
        self,
        *,
        config: PlatformBuilderConfig | None = None,
        store: PlatformBuilderStore | None = None,
        engine: BuilderEngine | None = None,
        academy: BuilderAcademy | None = None,
        god_mode: GodMode | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or platform_builder_store
        self.engine = engine or BuilderEngine(self.store)
        self.academy = academy or BuilderAcademy(self.store)
        self.god_mode = god_mode or GodMode(self.store)

    def reset(self) -> None:
        self.store.reset()
        self.academy = BuilderAcademy(self.store)
        self.god_mode = GodMode(self.store)
        self.engine = BuilderEngine(self.store)

    def bootstrap(self) -> dict[str, Any]:
        web = ROOT / "src" / "web" / "platform-builder"
        bid = _id("pb_boot")
        record = {
            "bootstrap_id": bid,
            "bootstrap": True,
            "version": self.config.application_version,
            "sprint": self.config.sprint,
            "application": self.config.application,
            "api_prefix": self.config.api_prefix,
            "builder_engine_ready": True,
            "builder_academy_ready": True,
            "god_mode_ready": True,
            "help_system_ready": True,
            "navigation_ready": True,
            "dark_theme_ready": True,
            "platform_owner_role": PLATFORM_OWNER_ROLE,
            "builders_count": len(BUILDERS),
            "web_path_exists": web.exists(),
            "dashboard_page_exists": (web / "pages" / "PlatformBuilderDashboard.tsx").exists(),
            "framework_exists": (web / "framework" / "BuilderFramework.tsx").exists(),
            "bootstrapped_at": _now(),
        }
        self.store.bootstraps.save(bid, record)
        return record

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "application": self.config.application,
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "sprint": self.config.sprint,
            "release_status": self.config.release_status,
            "api_prefix": self.config.api_prefix,
            "platform_builder_ready": True,
            "builder_framework_ready": True,
            "builder_academy_ready": True,
            "god_mode_ready": True,
            "builder_navigation_ready": True,
            "help_system_ready": True,
            "dark_theme_ready": True,
            "engines": {
                "builder_engine": self.config.builder_engine,
                "builder_academy": self.config.builder_academy,
                "god_mode": self.config.god_mode,
                "help_system": self.config.help_system,
            },
        }

    def inventory(self) -> dict[str, Any]:
        return {
            "application": self.config.application,
            "version": self.config.application_version,
            "sprint": self.config.sprint,
            "framework_phases": list(self.config.framework_phases),
            "academy_modes": list(self.config.academy_modes),
            "builders": self.engine.list_builders(),
            "platform_owner_role": PLATFORM_OWNER_ROLE,
        }

    def dashboard(self) -> dict[str, Any]:
        return {
            "title": "Platform Builder Dashboard",
            "version": self.config.application_version,
            "sprint": self.config.sprint,
            "builders": [
                {
                    "id": b["id"],
                    "name": b["name"],
                    "status": b["status"],
                    "route": b["route"],
                    "kind": b["kind"],
                }
                for b in BUILDERS
                if b["id"] != "god_mode"
            ],
            "academy": self.academy.status(),
            "framework": {"phases": list(self.config.framework_phases), "ready": True},
            "stats": {
                "builders": len([b for b in BUILDERS if b["kind"] == "builder"]),
                "frame_only": len([b for b in BUILDERS if b.get("frame_only")]),
                "operational": len([b for b in BUILDERS if b["status"] == "operational"]),
            },
        }

    def menu(self, role: str | None = None) -> dict[str, Any]:
        return {
            "section": "Platform Builder",
            "items": menu_for_role(role),
            "god_mode_visible": is_platform_owner(role),
        }

    def roles(self) -> dict[str, Any]:
        return {
            "roles": [
                {
                    "id": PLATFORM_OWNER_ROLE,
                    "name": "Platform Owner",
                    "scope": "platform",
                    "god_mode": True,
                    "description": "Full platform stewardship including God Mode.",
                },
                {
                    "id": "builder",
                    "name": "Builder",
                    "scope": "organization",
                    "god_mode": False,
                    "description": "Create objects through Platform Builder.",
                },
            ]
        }


platform_builder = PlatformBuilderApplication()
