"""Legal risk management — corporate risk, heatmaps, mitigation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class LegalRiskManagement:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.risk_levels = list(DEFAULT_CONFIG.cp_risk_levels)

    def register_risk(
        self,
        *,
        title: str,
        category: str = "compliance",
        likelihood: str = "medium",
        impact: str = "medium",
        company_id: str = "",
    ) -> dict[str, Any]:
        if not title:
            raise ValidationError("title required")
        for val, label in ((likelihood, "likelihood"), (impact, "impact")):
            if val.lower().strip() not in self.risk_levels:
                raise ValidationError(f"{label} must be one of {self.risk_levels}")
        rid = _id("cp_risk")
        return self.store.cp_risks.save(
            rid,
            {
                "risk_id": rid,
                "title": title,
                "category": category,
                "likelihood": likelihood.lower().strip(),
                "impact": impact.lower().strip(),
                "company_id": company_id,
                "priority": self._priority(likelihood, impact),
                "at": _now(),
            },
        )

    def assess_compliance_risk(
        self, *, title: str, score: float = 50.0, findings: list[str] | None = None
    ) -> dict[str, Any]:
        if not title:
            raise ValidationError("title required")
        aid = _id("cp_rass")
        return self.store.cp_risk_assessments.save(
            aid,
            {
                "assessment_id": aid,
                "title": title,
                "score": max(0.0, min(100.0, float(score))),
                "findings": findings or [],
                "at": _now(),
            },
        )

    def correlate_contract_risk(
        self, *, contract_ref: str, risk_id: str = "", detail: str = ""
    ) -> dict[str, Any]:
        if not contract_ref:
            raise ValidationError("contract_ref required")
        cid = _id("cp_crisk")
        return self.store.cp_contract_risks.save(
            cid,
            {
                "correlation_id": cid,
                "contract_ref": contract_ref,
                "risk_id": risk_id,
                "detail": detail,
                "at": _now(),
            },
        )

    def regulatory_change_impact(
        self, *, change_title: str, impact: str = "medium", detail: str = ""
    ) -> dict[str, Any]:
        if not change_title:
            raise ValidationError("change_title required")
        rid = _id("cp_regch")
        return self.store.cp_reg_changes.save(
            rid,
            {
                "change_id": rid,
                "change_title": change_title,
                "impact": impact,
                "detail": detail,
                "at": _now(),
            },
        )

    def heatmap(self, *, scope: str = "enterprise") -> dict[str, Any]:
        cells: dict[str, int] = {}
        for risk in self.store.cp_risks.list_all():
            key = f"{risk.get('likelihood')}:{risk.get('impact')}"
            cells[key] = cells.get(key, 0) + 1
        hid = _id("cp_heat")
        return self.store.cp_heatmaps.save(
            hid,
            {"heatmap_id": hid, "scope": scope, "cells": cells, "at": _now()},
        )

    def prioritize(self, *, risk_id: str, priority: str = "high") -> dict[str, Any]:
        risk = self.store.cp_risks.get(risk_id)
        if risk is None:
            from applications.legal_enterprise.shared.exceptions import NotFoundError

            raise NotFoundError("risk", risk_id)
        risk["priority"] = priority
        self.store.cp_risks.save(risk_id, risk)
        pid = _id("cp_prio")
        return self.store.cp_priorities.save(
            pid,
            {"priority_id": pid, "risk_id": risk_id, "priority": priority, "at": _now()},
        )

    def recommend_mitigation(self, *, risk_id: str, actions: list[str] | None = None) -> dict[str, Any]:
        if self.store.cp_risks.get(risk_id) is None:
            from applications.legal_enterprise.shared.exceptions import NotFoundError

            raise NotFoundError("risk", risk_id)
        mid = _id("cp_mit")
        return self.store.cp_mitigations.save(
            mid,
            {
                "mitigation_id": mid,
                "risk_id": risk_id,
                "actions": actions or ["Strengthen control", "Schedule audit"],
                "at": _now(),
            },
        )

    def _priority(self, likelihood: str, impact: str) -> str:
        rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        score = rank.get(likelihood.lower(), 2) + rank.get(impact.lower(), 2)
        if score >= 7:
            return "critical"
        if score >= 5:
            return "high"
        if score >= 3:
            return "medium"
        return "low"

    def status(self) -> dict[str, Any]:
        return {
            "risks": self.store.cp_risks.count(),
            "assessments": self.store.cp_risk_assessments.count(),
            "contract_risks": self.store.cp_contract_risks.count(),
            "reg_changes": self.store.cp_reg_changes.count(),
            "heatmaps": self.store.cp_heatmaps.count(),
            "priorities": self.store.cp_priorities.count(),
            "mitigations": self.store.cp_mitigations.count(),
        }
