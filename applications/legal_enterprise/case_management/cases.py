"""Case registry, lifecycle, timeline, status, priority, ownership."""

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


class CasePlatform:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.statuses = list(DEFAULT_CONFIG.cm_case_statuses)
        self.priorities = list(DEFAULT_CONFIG.cm_priorities)
        self.categories = list(DEFAULT_CONFIG.cm_categories)

    def register(
        self,
        *,
        title: str,
        case_number: str = "",
        category: str = "civil",
        priority: str = "medium",
        status: str = "intake",
        owner: str = "",
        court_name: str = "",
    ) -> dict[str, Any]:
        if not title:
            raise ValidationError("title required")
        cat = category.lower().strip()
        if cat not in self.categories:
            raise ValidationError(f"category must be one of {self.categories}")
        pri = priority.lower().strip()
        if pri not in self.priorities:
            raise ValidationError(f"priority must be one of {self.priorities}")
        st = status.lower().strip()
        if st not in self.statuses:
            raise ValidationError(f"status must be one of {self.statuses}")
        cid = _id("cm_case")
        record = {
            "case_id": cid,
            "title": title,
            "case_number": case_number or cid,
            "category": cat,
            "priority": pri,
            "status": st,
            "owner": owner,
            "court_name": court_name,
            "created_at": _now(),
        }
        self.store.cm_cases.save(cid, record)
        self.set_status(case_id=cid, status=st, note="case registered")
        self.add_timeline(case_id=cid, event="created", detail=title)
        return record

    def set_status(self, *, case_id: str, status: str, note: str = "") -> dict[str, Any]:
        case = self.store.cm_cases.get(case_id)
        if case is None:
            raise NotFoundError("case", case_id)
        st = status.lower().strip()
        if st not in self.statuses:
            raise ValidationError(f"status must be one of {self.statuses}")
        case["status"] = st
        self.store.cm_cases.save(case_id, case)
        sid = _id("cm_st")
        return self.store.cm_status_events.save(
            sid,
            {"status_id": sid, "case_id": case_id, "status": st, "note": note, "at": _now()},
        )

    def set_priority(self, *, case_id: str, priority: str) -> dict[str, Any]:
        case = self.store.cm_cases.get(case_id)
        if case is None:
            raise NotFoundError("case", case_id)
        pri = priority.lower().strip()
        if pri not in self.priorities:
            raise ValidationError(f"priority must be one of {self.priorities}")
        case["priority"] = pri
        self.store.cm_cases.save(case_id, case)
        return case

    def assign_owner(self, *, case_id: str, owner: str) -> dict[str, Any]:
        case = self.store.cm_cases.get(case_id)
        if case is None:
            raise NotFoundError("case", case_id)
        if not owner:
            raise ValidationError("owner required")
        case["owner"] = owner
        self.store.cm_cases.save(case_id, case)
        oid = _id("cm_own")
        return self.store.cm_ownership.save(
            oid,
            {"ownership_id": oid, "case_id": case_id, "owner": owner, "at": _now()},
        )

    def add_timeline(self, *, case_id: str, event: str, detail: str = "") -> dict[str, Any]:
        if self.store.cm_cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if not event:
            raise ValidationError("event required")
        tid = _id("cm_tl")
        return self.store.cm_timelines.save(
            tid,
            {"timeline_id": tid, "case_id": case_id, "event": event, "detail": detail, "at": _now()},
        )

    def relate_cases(
        self, *, case_id: str, related_case_id: str, relation: str = "related"
    ) -> dict[str, Any]:
        if self.store.cm_cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if self.store.cm_cases.get(related_case_id) is None:
            raise NotFoundError("case", related_case_id)
        rid = _id("cm_rel")
        return self.store.cm_related.save(
            rid,
            {
                "relation_id": rid,
                "case_id": case_id,
                "related_case_id": related_case_id,
                "relation": relation,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "cases": self.store.cm_cases.count(),
            "status_events": self.store.cm_status_events.count(),
            "timelines": self.store.cm_timelines.count(),
            "related": self.store.cm_related.count(),
            "ownership": self.store.cm_ownership.count(),
        }
