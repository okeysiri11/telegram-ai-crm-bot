"""Ecosystem Manager + Application Registry (Sprint 12.0) — integrates existing apps without rewriting them."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from applications.ecosystem.shared.exceptions import NotFoundError, ValidationError
from applications.ecosystem.shared.store import UnifiedEcosystemStore, unified_ecosystem_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Soft probes — import lazily so missing apps degrade gracefully.
APP_PROBES: dict[str, Callable[[], dict[str, Any]]] = {}


def _probe_auto() -> dict[str, Any]:
    from applications.auto_marketplace import auto_marketplace

    h = auto_marketplace.health() if hasattr(auto_marketplace, "health") else {}
    return {"status": "online", "version": h.get("application_version") or h.get("version", "unknown"), "health": h}


def _probe_agro() -> dict[str, Any]:
    from applications.agro_marketplace import agro_marketplace

    h = agro_marketplace.health()
    return {"status": "online", "version": h.get("application_version", "unknown"), "health": h}


def _probe_port() -> dict[str, Any]:
    from applications.port_erp import port_erp

    h = port_erp.health()
    return {"status": "online", "version": h.get("application_version", "unknown"), "health": h}


def _probe_drone() -> dict[str, Any]:
    from applications.drone_platform import drone_platform

    h = drone_platform.health()
    return {"status": "online", "version": h.get("application_version", "unknown"), "health": h}


def _probe_crm() -> dict[str, Any]:
    # CRM is cross-cutting (api/crm_api + per-app CRM) — register as available surface.
    return {"status": "online", "version": "legacy+app", "surface": "api/crm_api + app CRM modules"}


def _probe_platform_core() -> dict[str, Any]:
    try:
        import platform_core  # type: ignore

        return {"status": "online", "version": getattr(platform_core, "__version__", "v3"), "note": "referenced only"}
    except Exception:
        return {"status": "available", "version": "v3", "note": "dependency — not modified"}


def _probe_knowledge() -> dict[str, Any]:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "knowledge"
    return {"status": "online", "version": "2.0.0", "path": str(root), "exists": root.exists()}


APP_PROBES.update(
    {
        "auto_marketplace": _probe_auto,
        "agro_marketplace": _probe_agro,
        "port_erp": _probe_port,
        "drone_platform": _probe_drone,
        "crm": _probe_crm,
        "platform_core": _probe_platform_core,
        "knowledge_system": _probe_knowledge,
    }
)


class EcosystemManager:
    def __init__(self, store: UnifiedEcosystemStore | None = None) -> None:
        self.store = store or unified_ecosystem_store

    def register_application(
        self,
        *,
        app_id: str,
        name: str = "",
        category: str = "application",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not app_id:
            raise ValidationError("app_id required")
        probe: dict[str, Any] = {}
        if app_id in APP_PROBES:
            try:
                probe = APP_PROBES[app_id]()
            except Exception as exc:
                probe = {"status": "degraded", "error": str(exc)}
        item = {
            "app_id": app_id,
            "name": name or app_id.replace("_", " ").title(),
            "category": category,
            "status": probe.get("status", "registered"),
            "version": probe.get("version", "unknown"),
            "probe": probe,
            "metadata": dict(metadata or {}),
            "registered_at": _now(),
        }
        self.store.applications.save(app_id, item)
        return item

    def discover(self) -> dict[str, Any]:
        registered = []
        for app_id in APP_PROBES:
            registered.append(self.register_application(app_id=app_id))
        return {"applications": registered, "count": len(registered), "at": _now()}

    def get_application(self, app_id: str) -> dict[str, Any]:
        item = self.store.applications.get(app_id)
        if item is None:
            raise NotFoundError("application", app_id)
        return item

    def list_applications(self) -> list[dict[str, Any]]:
        apps = self.store.applications.list_all()
        if not apps:
            return self.discover()["applications"]
        return apps

    def application_registry(self) -> dict[str, Any]:
        apps = self.list_applications()
        return {
            "registry": "unified_application_registry",
            "applications": apps,
            "online": sum(1 for a in apps if a.get("status") == "online"),
            "count": len(apps),
        }

    def status(self) -> dict[str, Any]:
        return {"ecosystem_manager": "1.0", "applications": len(self.list_applications()), "ready": True}


ecosystem_manager = EcosystemManager()
