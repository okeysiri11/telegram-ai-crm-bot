"""Organization Brain Suite — Sprint 27.2."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platform_organization_brain.facade import OrganizationBrainLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store

ROOT = Path(__file__).resolve().parents[3]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class OrganizationBrainSuite:
    """Sprint 27.2 — Enterprise Organization Brain hub facade."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = OrganizationBrainLibrary()

    def bootstrap(self) -> dict[str, Any]:
        self.library = OrganizationBrainLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        web = ROOT / "src" / "web" / "organization-brain"
        result["organization_brain_path_exists"] = web.exists()
        result["dashboard_page_exists"] = (web / "pages" / "OrganizationBrainPage.tsx").exists()
        result["platform_package_exists"] = (ROOT / "platform_organization_brain" / "facade.py").exists()
        result["hub_suite_exists"] = (
            ROOT / "applications" / "enterprise_hub" / "organization_brain" / "facade.py"
        ).exists()
        bid = _id("obr_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "hub_version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.obr_bootstraps.save(bid, record)
        for key, attr, prefix in (
            ("inventory", "obr_inventory", "obr_inv"),
            ("dashboard", "obr_dashboards", "obr_dash"),
            ("organization", "obr_organization", "obr_org"),
            ("board", "obr_board", "obr_board"),
            ("departments", "obr_departments", "obr_dept"),
            ("knowledge", "obr_knowledge", "obr_kg"),
            ("links", "obr_integrations", "obr_int"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        return record

    def inventory(self) -> dict[str, Any]:
        inv = self.library.inventory()
        rid = _id("obr_inv")
        record = {"inventory_id": rid, **inv, "created_at": _now()}
        self.store.obr_inventory.save(rid, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        dash = self.library.dashboard()
        rid = _id("obr_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.obr_dashboards.save(rid, record)
        return record

    def organization(self) -> dict[str, Any]:
        return self.library.organization_model()

    def board(self) -> dict[str, Any]:
        return self.library.executive_board()

    def departments(self) -> dict[str, Any]:
        return self.library.departments()

    def orchestrate_department(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.orchestrate_department(**kwargs)
        rid = _id("obr_orch")
        self.store.obr_orchestrations.save(rid, {"record_id": rid, **result, "created_at": _now()})
        return result

    def decide(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.decide(**kwargs)
        rid = _id("obr_dec")
        self.store.obr_decisions.save(rid, {"record_id": rid, **result, "created_at": _now()})
        return result

    def meeting(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.run_meeting(**kwargs)
        rid = _id("obr_mtg")
        self.store.obr_meetings.save(rid, {"record_id": rid, **result, "created_at": _now()})
        return result

    def meetings(self) -> dict[str, Any]:
        return self.library.meetings()

    def knowledge_write(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.knowledge_write(**kwargs)
        rid = result["id"]
        self.store.obr_knowledge.save(rid, {**result, "stored_at": _now()})
        return result

    def knowledge(self, kind: str | None = None) -> dict[str, Any]:
        return self.library.knowledge_list(kind)

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.obr_bootstraps.list_all()),
            "path": "src/web/organization-brain",
            "api_prefix": "/api/organization-brain/v1",
        }


organization_brain = OrganizationBrainSuite()
