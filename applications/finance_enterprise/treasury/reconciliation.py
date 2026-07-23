"""Bank reconciliation — import, matching, exceptions, reports, audit."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class BankReconciliation:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store

    def import_statement(
        self, *, account_ref: str, period: str, lines: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        if not account_ref or not period:
            raise ValidationError("account_ref and period required")
        sid = _id("tr_stmt")
        entries = lines or [{"memo": "balance", "amount": 0.0, "external_id": "OPEN"}]
        return self.store.tr_statements.save(
            sid,
            {
                "statement_id": sid,
                "account_ref": account_ref,
                "period": period,
                "lines": entries,
                "line_count": len(entries),
                "imported_at": _now(),
            },
        )

    def auto_match(self, *, statement_id: str, book_refs: list[str] | None = None) -> dict[str, Any]:
        stmt = self.store.tr_statements.get(statement_id)
        if stmt is None:
            raise NotFoundError("statement", statement_id)
        matched = []
        refs = book_refs or []
        for i, line in enumerate(stmt.get("lines", [])):
            ref = refs[i] if i < len(refs) else line.get("external_id", f"book-{i}")
            mid = _id("tr_match")
            matched.append(
                self.store.tr_matches.save(
                    mid,
                    {
                        "match_id": mid,
                        "statement_id": statement_id,
                        "line_index": i,
                        "book_ref": ref,
                        "method": "auto",
                        "at": _now(),
                    },
                )
            )
        return {"statement_id": statement_id, "matches": matched, "match_count": len(matched)}

    def manual_reconcile(
        self, *, statement_id: str, line_index: int, book_ref: str, note: str = ""
    ) -> dict[str, Any]:
        if self.store.tr_statements.get(statement_id) is None:
            raise NotFoundError("statement", statement_id)
        if not book_ref:
            raise ValidationError("book_ref required")
        mid = _id("tr_match")
        return self.store.tr_matches.save(
            mid,
            {
                "match_id": mid,
                "statement_id": statement_id,
                "line_index": int(line_index),
                "book_ref": book_ref,
                "method": "manual",
                "note": note,
                "at": _now(),
            },
        )

    def exception(
        self, *, statement_id: str, reason: str, severity: str = "medium"
    ) -> dict[str, Any]:
        if self.store.tr_statements.get(statement_id) is None:
            raise NotFoundError("statement", statement_id)
        if not reason:
            raise ValidationError("reason required")
        eid = _id("tr_exc")
        return self.store.tr_exceptions.save(
            eid,
            {
                "exception_id": eid,
                "statement_id": statement_id,
                "reason": reason,
                "severity": severity,
                "status": "open",
                "at": _now(),
            },
        )

    def report(self, *, statement_id: str) -> dict[str, Any]:
        if self.store.tr_statements.get(statement_id) is None:
            raise NotFoundError("statement", statement_id)
        matches = [m for m in self.store.tr_matches.list_all() if m["statement_id"] == statement_id]
        exceptions = [
            e for e in self.store.tr_exceptions.list_all() if e["statement_id"] == statement_id
        ]
        rid = _id("tr_rrep")
        return self.store.tr_recon_reports.save(
            rid,
            {
                "report_id": rid,
                "statement_id": statement_id,
                "match_count": len(matches),
                "exception_count": len(exceptions),
                "at": _now(),
            },
        )

    def audit(self, *, action: str, actor: str = "system", detail: str = "") -> dict[str, Any]:
        if not action:
            raise ValidationError("action required")
        aid = _id("tr_aud")
        return self.store.tr_recon_audit.save(
            aid,
            {"audit_id": aid, "action": action, "actor": actor, "detail": detail, "at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {
            "statements": self.store.tr_statements.count(),
            "matches": self.store.tr_matches.count(),
            "exceptions": self.store.tr_exceptions.count(),
            "reports": self.store.tr_recon_reports.count(),
            "audit": self.store.tr_recon_audit.count(),
        }
