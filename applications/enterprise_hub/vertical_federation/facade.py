"""Vertical Federation Suite — Sprint 27.3."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platform_vertical_federation.facade import VerticalFederationLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store

ROOT = Path(__file__).resolve().parents[3]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class VerticalFederationSuite:
    """Sprint 27.3 — Enterprise Vertical Federation hub facade."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = VerticalFederationLibrary()

    def bootstrap(self) -> dict[str, Any]:
        self.library = VerticalFederationLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        web = ROOT / "src" / "web" / "vertical-federation"
        result["vertical_federation_path_exists"] = web.exists()
        result["dashboard_page_exists"] = (web / "pages" / "VerticalFederationPage.tsx").exists()
        result["platform_package_exists"] = (
            ROOT / "platform_vertical_federation" / "facade.py"
        ).exists()
        result["hub_suite_exists"] = (
            ROOT / "applications" / "enterprise_hub" / "vertical_federation" / "facade.py"
        ).exists()
        bid = _id("vf_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "hub_version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.vf_bootstraps.save(bid, record)
        for key, attr, prefix in (
            ("inventory", "vf_inventory", "vf_inv"),
            ("dashboard", "vf_dashboards", "vf_dash"),
            ("registry", "vf_registry", "vf_reg"),
            ("directors", "vf_directors", "vf_dir"),
            ("links", "vf_links", "vf_lnk"),
            ("marketplace", "vf_marketplace", "vf_mkt"),
            ("knowledge", "vf_knowledge", "vf_kg"),
            ("integrations", "vf_integrations", "vf_int"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        return record

    def inventory(self) -> dict[str, Any]:
        inv = self.library.inventory()
        rid = _id("vf_inv")
        record = {"inventory_id": rid, **inv, "created_at": _now()}
        self.store.vf_inventory.save(rid, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        dash = self.library.dashboard()
        rid = _id("vf_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.vf_dashboards.save(rid, record)
        return record

    def registry(self) -> dict[str, Any]:
        return self.library.registry()

    def register_custom(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.register_custom(**kwargs)
        rid = result["id"]
        self.store.vf_registry.save(rid, {**result, "stored_at": _now()})
        return result

    def directors(self, vertical: str | None = None) -> dict[str, Any]:
        return self.library.directors(vertical)

    def director_act(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.director_act(**kwargs)
        rid = result["action_id"]
        self.store.vf_director_actions.save(rid, {**result, "stored_at": _now()})
        return result

    def links(self) -> dict[str, Any]:
        return self.library.links()

    def communicate(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.communicate(**kwargs)
        rid = result["message_id"]
        self.store.vf_messages.save(rid, {**result, "stored_at": _now()})
        return result

    def messages(self) -> dict[str, Any]:
        return self.library.messages()

    def marketplace_publish(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.marketplace_publish(**kwargs)
        rid = result["id"]
        self.store.vf_marketplace.save(rid, {**result, "stored_at": _now()})
        return result

    def marketplace(self, vertical: str | None = None) -> dict[str, Any]:
        return self.library.marketplace_list(vertical)

    def knowledge_write(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.knowledge_write(**kwargs)
        rid = result["id"]
        self.store.vf_knowledge.save(rid, {**result, "stored_at": _now()})
        return result

    def knowledge(self, scope: str | None = None) -> dict[str, Any]:
        return self.library.knowledge_list(scope)

    def semantic_search(self, query: str) -> dict[str, Any]:
        return self.library.semantic_search(query)

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.vf_bootstraps.list_all()),
            "path": "src/web/vertical-federation",
            "api_prefix": "/api/verticals/v1",
        }


vertical_federation = VerticalFederationSuite()
