"""Contract builder — templates, generators, clause library."""

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


CONTRACT_TYPES = ("sales", "service", "employment", "nda", "lease", "custom")


class ContractBuilder:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.di_contract_types)
        self.clause_kinds = list(DEFAULT_CONFIG.di_clause_kinds)

    def register_template(
        self,
        *,
        name: str,
        contract_type: str,
        clauses: list[str] | None = None,
        body: str = "",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("template name required")
        ct = contract_type.lower().strip()
        if ct not in self.types:
            raise ValidationError(f"contract_type must be one of {self.types}")
        tid = _id("di_tpl")
        return self.store.di_templates.save(
            tid,
            {
                "template_id": tid,
                "name": name,
                "contract_type": ct,
                "clauses": clauses or [],
                "body": body,
                "created_at": _now(),
            },
        )

    def add_clause(
        self,
        *,
        title: str,
        kind: str = "general",
        text: str = "",
        mandatory: bool = False,
    ) -> dict[str, Any]:
        if not title:
            raise ValidationError("clause title required")
        k = kind.lower().strip()
        if k not in self.clause_kinds:
            raise ValidationError(f"kind must be one of {self.clause_kinds}")
        cid = _id("di_cls")
        return self.store.di_clause_library.save(
            cid,
            {
                "clause_id": cid,
                "title": title,
                "kind": k,
                "text": text or f"{title} clause text.",
                "mandatory": bool(mandatory),
                "created_at": _now(),
            },
        )

    def generate(
        self,
        *,
        contract_type: str,
        title: str,
        parties: list[str] | None = None,
        template_id: str = "",
        clause_ids: list[str] | None = None,
        custom_body: str = "",
    ) -> dict[str, Any]:
        ct = contract_type.lower().strip()
        if ct not in self.types:
            raise ValidationError(f"contract_type must be one of {self.types}")
        if not title:
            raise ValidationError("title required")
        if template_id and self.store.di_templates.get(template_id) is None:
            raise NotFoundError("template", template_id)
        selected = []
        for cid in clause_ids or []:
            clause = self.store.di_clause_library.get(cid)
            if clause is None:
                raise NotFoundError("clause", cid)
            selected.append(clause)
        cid = _id("di_ctr")
        body = custom_body or f"{ct.title()} agreement: {title}"
        if selected:
            body += "\n\n" + "\n\n".join(c["text"] for c in selected)
        return self.store.di_contracts.save(
            cid,
            {
                "contract_id": cid,
                "contract_type": ct,
                "title": title,
                "parties": parties or [],
                "template_id": template_id,
                "clause_ids": [c["clause_id"] for c in selected],
                "body": body,
                "status": "draft",
                "created_at": _now(),
            },
        )

    def generate_sales(self, **kwargs: Any) -> dict[str, Any]:
        return self.generate(contract_type="sales", **kwargs)

    def generate_service(self, **kwargs: Any) -> dict[str, Any]:
        return self.generate(contract_type="service", **kwargs)

    def generate_employment(self, **kwargs: Any) -> dict[str, Any]:
        return self.generate(contract_type="employment", **kwargs)

    def generate_nda(self, **kwargs: Any) -> dict[str, Any]:
        return self.generate(contract_type="nda", **kwargs)

    def generate_lease(self, **kwargs: Any) -> dict[str, Any]:
        return self.generate(contract_type="lease", **kwargs)

    def generate_custom(self, **kwargs: Any) -> dict[str, Any]:
        return self.generate(contract_type="custom", **kwargs)

    def status(self) -> dict[str, Any]:
        return {
            "templates": self.store.di_templates.count(),
            "clauses": self.store.di_clause_library.count(),
            "contracts": self.store.di_contracts.count(),
        }
