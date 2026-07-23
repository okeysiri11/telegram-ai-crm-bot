"""Legislation version control — history, amendments, snapshots."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class VersionControl:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def record_history(
        self,
        *,
        document_id: str,
        version: str,
        summary: str = "",
        effective_on: str = "",
    ) -> dict[str, Any]:
        if not document_id:
            raise ValidationError("document_id required")
        if not version:
            raise ValidationError("version required")
        hid = _id("li_hist")
        return self.store.li_history.save(
            hid,
            {
                "history_id": hid,
                "document_id": document_id,
                "version": version,
                "summary": summary,
                "effective_on": effective_on,
                "recorded_at": _now(),
            },
        )

    def compare_versions(
        self,
        *,
        document_id: str,
        from_version: str,
        to_version: str,
        changes: list[str] | None = None,
    ) -> dict[str, Any]:
        if not document_id:
            raise ValidationError("document_id required")
        cid = _id("li_cmp")
        delta = changes or [f"diff {from_version} -> {to_version}"]
        return self.store.li_comparisons.save(
            cid,
            {
                "comparison_id": cid,
                "document_id": document_id,
                "from_version": from_version,
                "to_version": to_version,
                "changes": delta,
                "change_count": len(delta),
                "at": _now(),
            },
        )

    def track_amendment(
        self,
        *,
        document_id: str,
        amendment_ref: str,
        description: str = "",
        effective_on: str = "",
    ) -> dict[str, Any]:
        if not document_id or not amendment_ref:
            raise ValidationError("document_id and amendment_ref required")
        aid = _id("li_amd")
        return self.store.li_amendments.save(
            aid,
            {
                "amendment_id": aid,
                "document_id": document_id,
                "amendment_ref": amendment_ref,
                "description": description,
                "effective_on": effective_on,
                "at": _now(),
            },
        )

    def mark_repealed(
        self,
        *,
        document_id: str,
        repealed_on: str,
        replaced_by: str = "",
        reason: str = "",
    ) -> dict[str, Any]:
        if not document_id:
            raise ValidationError("document_id required")
        rid = _id("li_rep")
        return self.store.li_repealed.save(
            rid,
            {
                "repeal_id": rid,
                "document_id": document_id,
                "repealed_on": repealed_on,
                "replaced_by": replaced_by,
                "reason": reason,
                "at": _now(),
            },
        )

    def track_effective_date(
        self,
        *,
        document_id: str,
        effective_on: str,
        event: str = "enters_force",
    ) -> dict[str, Any]:
        if not document_id or not effective_on:
            raise ValidationError("document_id and effective_on required")
        eid = _id("li_eff")
        return self.store.li_effective_dates.save(
            eid,
            {
                "effective_id": eid,
                "document_id": document_id,
                "effective_on": effective_on,
                "event": event,
                "at": _now(),
            },
        )

    def snapshot(
        self,
        *,
        document_id: str,
        label: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not document_id or not label:
            raise ValidationError("document_id and label required")
        sid = _id("li_snap")
        return self.store.li_snapshots.save(
            sid,
            {
                "snapshot_id": sid,
                "document_id": document_id,
                "label": label,
                "payload": payload or {},
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "history": self.store.li_history.count(),
            "comparisons": self.store.li_comparisons.count(),
            "amendments": self.store.li_amendments.count(),
            "repealed": self.store.li_repealed.count(),
            "effective_dates": self.store.li_effective_dates.count(),
            "snapshots": self.store.li_snapshots.count(),
        }
