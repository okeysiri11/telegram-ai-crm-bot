"""Corporate governance — companies, shareholders, board, executives, resolutions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CorporateGovernance:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def register_company(
        self,
        *,
        name: str,
        jurisdiction: str = "",
        registration_no: str = "",
        structure: str = "corporation",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("company name required")
        cid = _id("cp_co")
        return self.store.cp_companies.save(
            cid,
            {
                "company_id": cid,
                "name": name,
                "jurisdiction": jurisdiction,
                "registration_no": registration_no,
                "structure": structure,
                "created_at": _now(),
            },
        )

    def register_structure(
        self, *, company_id: str, parent_id: str = "", relation: str = "subsidiary"
    ) -> dict[str, Any]:
        if self.store.cp_companies.get(company_id) is None:
            raise NotFoundError("company", company_id)
        if parent_id and self.store.cp_companies.get(parent_id) is None:
            raise NotFoundError("company", parent_id)
        sid = _id("cp_str")
        return self.store.cp_structures.save(
            sid,
            {
                "structure_id": sid,
                "company_id": company_id,
                "parent_id": parent_id,
                "relation": relation,
                "at": _now(),
            },
        )

    def register_shareholder(
        self, *, company_id: str, name: str, ownership_pct: float = 0.0
    ) -> dict[str, Any]:
        if self.store.cp_companies.get(company_id) is None:
            raise NotFoundError("company", company_id)
        if not name:
            raise ValidationError("shareholder name required")
        sid = _id("cp_sh")
        return self.store.cp_shareholders.save(
            sid,
            {
                "shareholder_id": sid,
                "company_id": company_id,
                "name": name,
                "ownership_pct": max(0.0, min(100.0, float(ownership_pct))),
                "at": _now(),
            },
        )

    def register_board_member(
        self, *, company_id: str, name: str, role: str = "director"
    ) -> dict[str, Any]:
        if self.store.cp_companies.get(company_id) is None:
            raise NotFoundError("company", company_id)
        if not name:
            raise ValidationError("board member name required")
        bid = _id("cp_brd")
        return self.store.cp_board.save(
            bid,
            {
                "board_id": bid,
                "company_id": company_id,
                "name": name,
                "role": role,
                "at": _now(),
            },
        )

    def register_executive(
        self, *, company_id: str, name: str, title: str = "CEO"
    ) -> dict[str, Any]:
        if self.store.cp_companies.get(company_id) is None:
            raise NotFoundError("company", company_id)
        if not name:
            raise ValidationError("executive name required")
        eid = _id("cp_exec")
        return self.store.cp_executives.save(
            eid,
            {
                "executive_id": eid,
                "company_id": company_id,
                "name": name,
                "title": title,
                "at": _now(),
            },
        )

    def register_document(
        self, *, company_id: str, title: str, document_type: str = "charter", uri: str = ""
    ) -> dict[str, Any]:
        if self.store.cp_companies.get(company_id) is None:
            raise NotFoundError("company", company_id)
        if not title:
            raise ValidationError("document title required")
        did = _id("cp_cdoc")
        return self.store.cp_corp_documents.save(
            did,
            {
                "document_id": did,
                "company_id": company_id,
                "title": title,
                "document_type": document_type,
                "uri": uri or f"vault://cp/{company_id}/{did}",
                "at": _now(),
            },
        )

    def register_resolution(
        self, *, company_id: str, title: str, adopted_on: str = "", status: str = "adopted"
    ) -> dict[str, Any]:
        if self.store.cp_companies.get(company_id) is None:
            raise NotFoundError("company", company_id)
        if not title:
            raise ValidationError("resolution title required")
        rid = _id("cp_res")
        return self.store.cp_resolutions.save(
            rid,
            {
                "resolution_id": rid,
                "company_id": company_id,
                "title": title,
                "adopted_on": adopted_on,
                "status": status,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "companies": self.store.cp_companies.count(),
            "structures": self.store.cp_structures.count(),
            "shareholders": self.store.cp_shareholders.count(),
            "board": self.store.cp_board.count(),
            "executives": self.store.cp_executives.count(),
            "documents": self.store.cp_corp_documents.count(),
            "resolutions": self.store.cp_resolutions.count(),
        }
