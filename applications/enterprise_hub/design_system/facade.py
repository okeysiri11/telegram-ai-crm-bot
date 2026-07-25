"""Design System Suite — Sprint 26.2 / v9.0.1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platform_enterprise_design_system.facade import DesignSystemLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store

ROOT = Path(__file__).resolve().parents[3]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DesignSystemSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = DesignSystemLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = DesignSystemLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        ds_root = ROOT / "src" / "web" / "design-system"
        result["design_system_path_exists"] = ds_root.exists()
        result["tokens_css_exists"] = (ds_root / "styles" / "tokens.css").exists()
        result["catalog_module_exists"] = (ds_root / "catalog" / "index.ts").exists()
        bid = _id("eds_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "hub_version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.eds_bootstraps.save(bid, record)
        for key, attr, prefix in (
            ("tokens", "eds_tokens", "eds_tok"),
            ("catalog", "eds_catalog", "eds_cat"),
            ("themes", "eds_themes", "eds_thm"),
            ("documentation", "eds_docs", "eds_doc"),
            ("dashboard", "eds_dashboards", "eds_dash"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        self.store.eds_bootstraps.save(bid, record)
        return record

    def inventory(self) -> dict[str, Any]:
        tokens = self.library.tokens.inventory()
        catalog = self.library.catalog.inventory()
        themes = self.library.theme.inventory()
        a11y = self.library.accessibility.inventory()
        responsive = self.library.responsive.inventory()
        rid = _id("eds_inv")
        record = {
            "inventory_id": rid,
            "tokens": tokens,
            "catalog": catalog,
            "themes": themes,
            "accessibility": a11y,
            "responsive": responsive,
            "path": "src/web/design-system",
            "created_at": _now(),
        }
        self.store.eds_catalog.save(rid, record)
        return record

    def documentation(self) -> dict[str, Any]:
        boot = self.library.bootstrap()
        docs = boot["full"]["documentation"]
        rid = _id("eds_doc")
        record = {"documentation_id": rid, **docs, "created_at": _now()}
        self.store.eds_docs.save(rid, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        boot = self.library.bootstrap()
        dash = boot["full"]["dashboard"]
        rid = _id("eds_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.eds_dashboards.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.eds_bootstraps.list_all()),
            "path": "src/web/design-system",
        }


design_system = DesignSystemSuite()
