"""Web Foundation Suite — Sprint 26.1 / v9.0.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platform_enterprise_web.facade import WebFoundationLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store

ROOT = Path(__file__).resolve().parents[3]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class WebFoundationSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = WebFoundationLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = WebFoundationLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        web_root = ROOT / "src" / "web"
        result["web_path_exists"] = web_root.exists()
        result["package_json_exists"] = (web_root / "package.json").exists()
        bid = _id("ewf_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.ewf_bootstraps.save(bid, record)
        for key, attr, prefix in (
            ("shell", "ewf_shell", "ewf_shell"),
            ("auth", "ewf_auth", "ewf_auth"),
            ("catalog", "ewf_catalog", "ewf_cat"),
            ("dashboard", "ewf_dashboards", "ewf_dash"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        self.store.ewf_bootstraps.save(bid, record)
        return record

    def inventory(self) -> dict[str, Any]:
        catalog = self.library.catalog.inventory()
        shell = self.library.shell.status()
        auth = self.library.auth.status()
        rid = _id("ewf_inv")
        record = {
            "inventory_id": rid,
            "shell": shell,
            "auth": auth,
            "catalog": catalog,
            "path": "src/web",
            "created_at": _now(),
        }
        self.store.ewf_catalog.save(rid, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        boot = self.library.bootstrap()
        dash = boot["full"]["dashboard"]
        rid = _id("ewf_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.ewf_dashboards.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.ewf_bootstraps.list_all()),
            "path": "src/web",
        }


web_foundation = WebFoundationSuite()
