"""Case Management Foundation — cases, participants, documents, evidence, tasks."""

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


class CaseManagement:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.statuses = list(DEFAULT_CONFIG.case_statuses)

    def register_case(
        self,
        *,
        title: str,
        case_number: str = "",
        court_id: str = "",
        category_code: str = "",
        status: str = "draft",
    ) -> dict[str, Any]:
        if not title:
            raise ValidationError("case title required")
        st = status.lower().strip()
        if st not in self.statuses:
            raise ValidationError(f"status must be one of {self.statuses}")
        if court_id and self.store.courts.get(court_id) is None:
            raise NotFoundError("court", court_id)
        cid = _id("case")
        record = {
            "case_id": cid,
            "title": title,
            "case_number": case_number or cid,
            "court_id": court_id,
            "category_code": category_code,
            "status": st,
            "created_at": _now(),
        }
        self.store.cases.save(cid, record)
        self.set_status(case_id=cid, status=st, note="case registered")
        self.add_timeline_event(case_id=cid, event="created", detail=title)
        return record

    def set_status(self, *, case_id: str, status: str, note: str = "") -> dict[str, Any]:
        case = self.store.cases.get(case_id)
        if case is None:
            raise NotFoundError("case", case_id)
        st = status.lower().strip()
        if st not in self.statuses:
            raise ValidationError(f"status must be one of {self.statuses}")
        case["status"] = st
        self.store.cases.save(case_id, case)
        sid = _id("case_st")
        return self.store.case_statuses.save(
            sid,
            {
                "status_id": sid,
                "case_id": case_id,
                "status": st,
                "note": note,
                "at": _now(),
            },
        )

    def add_timeline_event(
        self,
        *,
        case_id: str,
        event: str,
        detail: str = "",
    ) -> dict[str, Any]:
        if self.store.cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if not event:
            raise ValidationError("event required")
        tid = _id("case_tl")
        return self.store.case_timelines.save(
            tid,
            {
                "timeline_id": tid,
                "case_id": case_id,
                "event": event,
                "detail": detail,
                "at": _now(),
            },
        )

    def add_participant(
        self,
        *,
        case_id: str,
        role_code: str,
        party_name: str,
        party_ref: str = "",
    ) -> dict[str, Any]:
        if self.store.cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if not party_name:
            raise ValidationError("party_name required")
        role = role_code.lower().strip()
        if role not in DEFAULT_CONFIG.legal_roles:
            raise ValidationError(f"role_code must be one of {DEFAULT_CONFIG.legal_roles}")
        pid = _id("case_pt")
        return self.store.participants.save(
            pid,
            {
                "participant_id": pid,
                "case_id": case_id,
                "role_code": role,
                "party_name": party_name,
                "party_ref": party_ref,
                "created_at": _now(),
            },
        )

    def register_document(
        self,
        *,
        case_id: str,
        title: str,
        document_type: str = "filing",
        uri: str = "",
    ) -> dict[str, Any]:
        if self.store.cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if not title:
            raise ValidationError("document title required")
        did = _id("case_doc")
        return self.store.documents.save(
            did,
            {
                "document_id": did,
                "case_id": case_id,
                "title": title,
                "document_type": document_type,
                "uri": uri,
                "created_at": _now(),
            },
        )

    def register_evidence(
        self,
        *,
        case_id: str,
        label: str,
        evidence_type: str = "exhibit",
        description: str = "",
    ) -> dict[str, Any]:
        if self.store.cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if not label:
            raise ValidationError("evidence label required")
        eid = _id("case_ev")
        return self.store.evidence.save(
            eid,
            {
                "evidence_id": eid,
                "case_id": case_id,
                "label": label,
                "evidence_type": evidence_type,
                "description": description,
                "created_at": _now(),
            },
        )

    def create_task(
        self,
        *,
        case_id: str,
        title: str,
        assignee: str = "",
        due_on: str = "",
    ) -> dict[str, Any]:
        if self.store.cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if not title:
            raise ValidationError("task title required")
        tid = _id("case_task")
        return self.store.tasks.save(
            tid,
            {
                "task_id": tid,
                "case_id": case_id,
                "title": title,
                "assignee": assignee,
                "due_on": due_on,
                "status": "open",
                "created_at": _now(),
            },
        )

    def add_note(self, *, case_id: str, author: str, body: str) -> dict[str, Any]:
        if self.store.cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if not body:
            raise ValidationError("note body required")
        nid = _id("case_note")
        return self.store.case_notes.save(
            nid,
            {
                "note_id": nid,
                "case_id": case_id,
                "author": author or "system",
                "body": body,
                "created_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "cases": self.store.cases.count(),
            "status_events": self.store.case_statuses.count(),
            "timeline_events": self.store.case_timelines.count(),
            "participants": self.store.participants.count(),
            "documents": self.store.documents.count(),
            "evidence": self.store.evidence.count(),
            "tasks": self.store.tasks.count(),
            "notes": self.store.case_notes.count(),
        }
