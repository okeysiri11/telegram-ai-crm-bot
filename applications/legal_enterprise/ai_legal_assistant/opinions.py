"""Legal opinion support — summaries, authorities, draft opinions."""

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


class LegalOpinionSupport:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def draft_opinion(
        self,
        *,
        issue: str,
        conclusion: str = "",
        authorities: list[str] | None = None,
        risks: list[str] | None = None,
        alternatives: list[str] | None = None,
        counterarguments: list[str] | None = None,
        notes: str = "",
    ) -> dict[str, Any]:
        if not issue:
            raise ValidationError("issue required")
        oid = _id("aa_opn")
        return self.store.aa_opinions.save(
            oid,
            {
                "opinion_id": oid,
                "issue": issue,
                "issue_summary": f"Summary of issue: {issue}",
                "supporting_authorities": authorities or ["Civil Code Art. 10"],
                "alternative_arguments": alternatives or ["Equitable estoppel theory"],
                "counterarguments": counterarguments or ["Waiver by conduct"],
                "risks": risks or ["Adverse appellate interpretation"],
                "research_notes": notes or "Initial research complete.",
                "conclusion": conclusion or "On balance, claim is supportable subject to factual proof.",
                "draft": (
                    f"LEGAL OPINION\nIssue: {issue}\n"
                    f"Conclusion: {conclusion or 'Supportable with residual risk.'}"
                ),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"opinions": self.store.aa_opinions.count()}
