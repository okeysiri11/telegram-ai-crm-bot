"""Compliance management — frameworks, requirements, policies, controls."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ComplianceManagement:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.statuses = list(DEFAULT_CONFIG.cp_compliance_statuses)

    def register_framework(self, *, name: str, jurisdiction: str = "", version: str = "1.0") -> dict[str, Any]:
        if not name:
            raise ValidationError("framework name required")
        fid = _id("cp_fw")
        return self.store.cp_frameworks.save(
            fid,
            {
                "framework_id": fid,
                "name": name,
                "jurisdiction": jurisdiction,
                "version": version,
                "at": _now(),
            },
        )

    def register_requirement(
        self, *, framework_id: str, code: str, title: str, description: str = ""
    ) -> dict[str, Any]:
        if self.store.cp_frameworks.get(framework_id) is None:
            raise NotFoundError("framework", framework_id)
        if not code or not title:
            raise ValidationError("code and title required")
        rid = _id("cp_req")
        return self.store.cp_requirements.save(
            rid,
            {
                "requirement_id": rid,
                "framework_id": framework_id,
                "code": code,
                "title": title,
                "description": description,
                "at": _now(),
            },
        )

    def checklist_item(
        self, *, requirement_id: str, company_id: str = "", status: str = "open"
    ) -> dict[str, Any]:
        if self.store.cp_requirements.get(requirement_id) is None:
            raise NotFoundError("requirement", requirement_id)
        st = status.lower().strip()
        if st not in self.statuses:
            raise ValidationError(f"status must be one of {self.statuses}")
        cid = _id("cp_chk")
        return self.store.cp_checklists.save(
            cid,
            {
                "checklist_id": cid,
                "requirement_id": requirement_id,
                "company_id": company_id,
                "status": st,
                "at": _now(),
            },
        )

    def track_status(
        self, *, checklist_id: str, status: str, note: str = ""
    ) -> dict[str, Any]:
        item = self.store.cp_checklists.get(checklist_id)
        if item is None:
            raise NotFoundError("checklist", checklist_id)
        st = status.lower().strip()
        if st not in self.statuses:
            raise ValidationError(f"status must be one of {self.statuses}")
        item["status"] = st
        self.store.cp_checklists.save(checklist_id, item)
        sid = _id("cp_st")
        return self.store.cp_status_events.save(
            sid,
            {
                "status_id": sid,
                "checklist_id": checklist_id,
                "status": st,
                "note": note,
                "at": _now(),
            },
        )

    def register_policy(
        self, *, title: str, policy_type: str = "internal", version: str = "1.0"
    ) -> dict[str, Any]:
        if not title:
            raise ValidationError("policy title required")
        pid = _id("cp_pol")
        return self.store.cp_policies.save(
            pid,
            {
                "policy_id": pid,
                "title": title,
                "policy_type": policy_type,
                "version": version,
                "at": _now(),
            },
        )

    def register_control(
        self, *, name: str, control_type: str = "preventive", policy_id: str = ""
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("control name required")
        if policy_id and self.store.cp_policies.get(policy_id) is None:
            raise NotFoundError("policy", policy_id)
        cid = _id("cp_ctl")
        return self.store.cp_controls.save(
            cid,
            {
                "control_id": cid,
                "name": name,
                "control_type": control_type,
                "policy_id": policy_id,
                "at": _now(),
            },
        )

    def register_exception(
        self, *, control_id: str, reason: str, approved_by: str = "", expires_on: str = ""
    ) -> dict[str, Any]:
        if self.store.cp_controls.get(control_id) is None:
            raise NotFoundError("control", control_id)
        if not reason:
            raise ValidationError("reason required")
        eid = _id("cp_exc")
        return self.store.cp_exceptions.save(
            eid,
            {
                "exception_id": eid,
                "control_id": control_id,
                "reason": reason,
                "approved_by": approved_by,
                "expires_on": expires_on,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "frameworks": self.store.cp_frameworks.count(),
            "requirements": self.store.cp_requirements.count(),
            "checklists": self.store.cp_checklists.count(),
            "status_events": self.store.cp_status_events.count(),
            "policies": self.store.cp_policies.count(),
            "controls": self.store.cp_controls.count(),
            "exceptions": self.store.cp_exceptions.count(),
        }
