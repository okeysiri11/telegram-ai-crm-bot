"""Release Candidate Suite — Sprint 26.8 / RC1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platform_enterprise_release_candidate.facade import ReleaseCandidateLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store

ROOT = Path(__file__).resolve().parents[3]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ReleaseCandidateSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = ReleaseCandidateLibrary()

    def bootstrap(self) -> dict[str, Any]:
        self.library = ReleaseCandidateLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        web = ROOT / "src" / "web" / "release"
        result["release_path_exists"] = web.exists()
        result["dashboard_page_exists"] = (web / "pages" / "ReleaseCandidatePage.tsx").exists()
        result["platform_package_exists"] = (ROOT / "platform_enterprise_release_candidate" / "facade.py").exists()
        result["docs_rc_exists"] = (ROOT / "docs" / "RELEASE_CANDIDATE.md").exists()
        result["docs_health_exists"] = (ROOT / "docs" / "PLATFORM_HEALTH_REPORT.md").exists()
        bid = _id("rc_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "hub_version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.rc_bootstraps.save(bid, record)
        for key, attr, prefix in (
            ("inventory", "rc_inventory", "rc_inv"),
            ("dashboard", "rc_dashboards", "rc_dash"),
            ("links", "rc_integrations", "rc_int"),
            ("health_report", "rc_health_reports", "rc_health"),
            ("integration", "rc_integration", "rc_integ"),
            ("registry", "rc_registry", "rc_reg"),
            ("routes", "rc_routes", "rc_routes"),
            ("security", "rc_security", "rc_sec"),
            ("performance", "rc_performance", "rc_perf"),
            ("documentation", "rc_documentation", "rc_docs"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        return record

    def inventory(self) -> dict[str, Any]:
        inv = self.library.inventory()
        rid = _id("rc_inv")
        record = {"inventory_id": rid, **inv, "created_at": _now()}
        self.store.rc_inventory.save(rid, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        dash = self.library.dashboard()
        rid = _id("rc_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.rc_dashboards.save(rid, record)
        return record

    def health_report(self) -> dict[str, Any]:
        report = self.library.health_report()
        rid = _id("rc_health")
        record = {"report_id": rid, **report, "created_at": _now()}
        self.store.rc_health_reports.save(rid, record)
        return record

    def integration(self) -> dict[str, Any]:
        return self.library.platform_integration()

    def registry(self) -> dict[str, Any]:
        return self.library.application_registry_scan()

    def routes(self) -> dict[str, Any]:
        return self.library.routes_audit()

    def security(self) -> dict[str, Any]:
        return self.library.security_review()

    def performance(self) -> dict[str, Any]:
        return self.library.performance_review()

    def documentation(self) -> dict[str, Any]:
        return self.library.documentation_review()

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.rc_bootstraps.list_all()),
            "path": "src/web/release",
            "api_prefix": "/api/release/v1",
        }


release_candidate = ReleaseCandidateSuite()
