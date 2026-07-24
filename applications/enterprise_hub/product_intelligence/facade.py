"""Product Intelligence Suite facade — Sprint 22.0 / v6.1.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_product_intelligence.facade import ProductIntelligenceLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ProductIntelligenceSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = ProductIntelligenceLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations()

    def bootstrap(self) -> dict[str, Any]:
        self.library = ProductIntelligenceLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("epi_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.epi_bootstraps.save(bid, record)
        for sample in full["samples"]:
            fid = _id("epi_fb")
            self.store.epi_feedback.save(fid, {"feedback_id": fid, **sample, "ingested_at": _now()})
        rid = _id("epi_rep")
        self.store.epi_reports.save(rid, {"report_id": rid, **full["report"], "generated_at": _now()})
        did = _id("epi_dec")
        self.store.epi_decisions.save(
            did, {"decision_id": did, "report_id": rid, **full["owner"], "decided_at": _now()}
        )
        pid = _id("epi_pipe")
        self.store.epi_pipelines.save(
            pid, {"pipeline_id": pid, "decision_id": did, **full["pipeline"], "created_at": _now()}
        )
        vid = _id("epi_val")
        self.store.epi_validations.save(
            vid, {"validation_id": vid, "pipeline_id": pid, **full["validation"], "validated_at": _now()}
        )
        kid = _id("epi_kb")
        self.store.epi_knowledge.save(
            kid,
            {
                "knowledge_id": kid,
                "report_id": rid,
                "decision_id": did,
                **full["knowledge"],
                "recorded_at": _now(),
            },
        )
        record["report_id"] = rid
        record["decision_id"] = did
        record["pipeline_id"] = pid
        record["knowledge_id"] = kid
        self.store.epi_bootstraps.save(bid, record)
        return record

    def ingest(
        self,
        *,
        source: str,
        title: str,
        description: str = "",
        module: str = "enterprise_hub",
        severity: str = "medium",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            item = self.library.feedback.normalize(
                source=source,
                title=title,
                description=description,
                module=module,
                severity=severity,
                metadata=metadata,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        fid = _id("epi_fb")
        record = {"feedback_id": fid, **item, "ingested_at": _now()}
        self.store.epi_feedback.save(fid, record)
        return record

    def analyze(self) -> dict[str, Any]:
        items = self.store.epi_feedback.list_all()
        if not items:
            raise ValidationError("no feedback to analyze; ingest first")
        history = self.store.epi_knowledge.list_all()
        result = self.library.analysis.analyze(items, history=history)
        aid = _id("epi_an")
        record = {"analysis_id": aid, **result, "analyzed_at": _now()}
        self.store.epi_analyses.save(aid, record)
        return record

    def generate_report(self, *, problem: str, proposal: str) -> dict[str, Any]:
        if not problem or not proposal:
            raise ValidationError("problem and proposal are required")
        items = self.store.epi_feedback.list_all()
        history = self.store.epi_knowledge.list_all()
        analysis = self.library.analysis.analyze(items or [{"title": problem, "fingerprint": "adhoc"}], history=history)
        board = self.library.experts.evaluate(problem=problem, proposal=proposal)
        report = self.library.reports.generate(
            problem=problem, proposal=proposal, analysis=analysis, expert_board=board
        )
        rid = _id("epi_rep")
        record = {"report_id": rid, **report, "generated_at": _now()}
        self.store.epi_reports.save(rid, record)
        return record

    def owner_decide(
        self,
        *,
        report_id: str,
        decision: str,
        owner_id: str,
        changes: str = "",
        notes: str = "",
    ) -> dict[str, Any]:
        report = self.store.epi_reports.get(report_id)
        if not report:
            raise NotFoundError(f"report not found: {report_id}")
        try:
            result = self.library.approval.decide(
                decision=decision, owner_id=owner_id, changes=changes, notes=notes
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        did = _id("epi_dec")
        record = {"decision_id": did, "report_id": report_id, **result, "decided_at": _now()}
        self.store.epi_decisions.save(did, record)
        if result["development_allowed"]:
            pipe = self.library.pipeline.create(report=report, approval=result)
            pid = _id("epi_pipe")
            self.store.epi_pipelines.save(
                pid, {"pipeline_id": pid, "decision_id": did, **pipe, "created_at": _now()}
            )
            record["pipeline_id"] = pid
            self.store.epi_decisions.save(did, record)
        kid = _id("epi_kb")
        self.store.epi_knowledge.save(
            kid,
            {
                "knowledge_id": kid,
                "report_id": report_id,
                "decision_id": did,
                "discussion": [],
                "ai_conclusions": report.get("expert_conclusions", []),
                "owner_decision": result,
                "implementation_results": None,
                "effectiveness": None,
                "recorded_at": _now(),
            },
        )
        return record

    def validate_release(self, *, report_id: str) -> dict[str, Any]:
        report = self.store.epi_reports.get(report_id)
        if not report:
            raise NotFoundError(f"report not found: {report_id}")
        result = self.library.validation.validate(expected_kpi=report.get("kpi", []))
        vid = _id("epi_val")
        record = {"validation_id": vid, "report_id": report_id, **result, "validated_at": _now()}
        self.store.epi_validations.save(vid, record)
        return record

    def knowledge_history(self) -> dict[str, Any]:
        items = self.store.epi_knowledge.list_all()
        return {"count": len(items), "entries": items}

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.epi_bootstraps.list_all()),
            "feedback": len(self.store.epi_feedback.list_all()),
            "reports": len(self.store.epi_reports.list_all()),
            "decisions": len(self.store.epi_decisions.list_all()),
            "pipelines": len(self.store.epi_pipelines.list_all()),
            "knowledge": len(self.store.epi_knowledge.list_all()),
        }


product_intelligence = ProductIntelligenceSuite()
