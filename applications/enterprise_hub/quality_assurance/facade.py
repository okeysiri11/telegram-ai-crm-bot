"""Quality Assurance Suite facade — Sprint 21.5 / v6.0.0-rc5."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_quality.facade import QualityLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class QualityAssuranceSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = QualityLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations()

    def bootstrap(self) -> dict[str, Any]:
        self.library = QualityLibrary()
        result = self.library.bootstrap()
        bid = _id("eqa_boot")
        # persist suite summaries without huge nested payload duplication in list endpoints
        full = result.pop("full")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.eqa_bootstraps.save(bid, record)
        for kind, suite in full["suites"].items():
            sid = _id("eqa_suite")
            self.store.eqa_suites.save(sid, {"suite_id": sid, "kind": kind, **suite, "run_at": _now()})
        cov_id = _id("eqa_cov")
        self.store.eqa_coverage.save(cov_id, {"coverage_id": cov_id, **full["coverage"], "measured_at": _now()})
        met_id = _id("eqa_met")
        self.store.eqa_metrics.save(met_id, {"metrics_id": met_id, **full["metrics"], "computed_at": _now()})
        dash_id = _id("eqa_dash")
        self.store.eqa_dashboards.save(dash_id, {"dashboard_id": dash_id, **full["dashboard"], "rendered_at": _now()})
        fix = full["fixtures"]
        self.store.eqa_fixtures.save(fix["fixture_id"], fix)
        record["dashboard_id"] = dash_id
        record["coverage_id"] = cov_id
        record["metrics_id"] = met_id
        self.store.eqa_bootstraps.save(bid, record)
        return record

    def run_suite(self, kind: str) -> dict[str, Any]:
        mapping = {
            "unit": self.library.unit.run,
            "integration": self.library.integration.run,
            "e2e": self.library.e2e.run,
            "contract": self.library.contract.run,
            "ai": self.library.ai.run,
            "workflow": self.library.workflow.run,
            "regression": self.library.regression.run,
            "security": self.library.security.run,
            "performance": self.library.performance.run,
        }
        if kind not in mapping:
            raise ValidationError(f"unknown suite kind: {kind}")
        result = mapping[kind]()
        sid = _id("eqa_suite")
        record = {"suite_id": sid, **result, "run_at": _now()}
        self.store.eqa_suites.save(sid, record)
        return record

    def coverage(self) -> dict[str, Any]:
        result = self.library.coverage.measure()
        cid = _id("eqa_cov")
        record = {"coverage_id": cid, **result, "measured_at": _now()}
        self.store.eqa_coverage.save(cid, record)
        return record

    def fixtures(self, *, kind: str = "organization", count: int = 3) -> dict[str, Any]:
        result = self.library.fixtures.generate(kind=kind, count=count)
        self.store.eqa_fixtures.save(result["fixture_id"], result)
        return result

    def dashboard(self) -> dict[str, Any]:
        items = self.store.eqa_dashboards.list_all()
        if not items:
            raise NotFoundError("quality dashboard not found; bootstrap first")
        return items[-1]

    def certify(self) -> dict[str, Any]:
        boot = self.bootstrap()
        cid = _id("eqa_cert")
        record = {
            "certification_id": cid,
            "certified": boot["certified"],
            "release_quality": boot["release_quality"],
            "coverage": boot["coverage"],
            "pass_rate": boot["pass_rate"],
            "bootstrap_id": boot["bootstrap_id"],
            "certified_at": _now(),
        }
        self.store.eqa_certifications.save(cid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.eqa_bootstraps.list_all()),
            "suites": len(self.store.eqa_suites.list_all()),
            "dashboards": len(self.store.eqa_dashboards.list_all()),
            "certifications": len(self.store.eqa_certifications.list_all()),
        }


quality_assurance = QualityAssuranceSuite()
