"""Core Financial Registry — organizations, customers, vendors, accounts, currencies."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.shared.exceptions import ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class FinanceRegistry:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.entity_types = list(DEFAULT_CONFIG.entity_types)

    def register_organization(
        self, *, name: str, jurisdiction: str = "", registration_no: str = ""
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("organization name required")
        oid = _id("fe_org")
        return self.store.organizations.save(
            oid,
            {
                "organization_id": oid,
                "name": name,
                "jurisdiction": jurisdiction,
                "registration_no": registration_no,
                "created_at": _now(),
            },
        )

    def register_customer(
        self, *, name: str, organization_id: str = "", country: str = ""
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("customer name required")
        cid = _id("fe_cust")
        return self.store.customers.save(
            cid,
            {
                "customer_id": cid,
                "name": name,
                "organization_id": organization_id,
                "country": country,
                "created_at": _now(),
            },
        )

    def register_vendor(
        self, *, name: str, organization_id: str = "", country: str = ""
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("vendor name required")
        vid = _id("fe_vend")
        return self.store.vendors.save(
            vid,
            {
                "vendor_id": vid,
                "name": name,
                "organization_id": organization_id,
                "country": country,
                "created_at": _now(),
            },
        )

    def register_financial_account(
        self,
        *,
        name: str,
        account_code: str,
        currency: str = "",
        organization_id: str = "",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("financial account name required")
        if not account_code:
            raise ValidationError("account_code required")
        aid = _id("fe_acct")
        return self.store.financial_accounts.save(
            aid,
            {
                "account_id": aid,
                "name": name,
                "account_code": account_code,
                "currency": currency or DEFAULT_CONFIG.base_currency,
                "organization_id": organization_id,
                "created_at": _now(),
            },
        )

    def register_currency(
        self, *, code: str, name: str = "", decimals: int = 2
    ) -> dict[str, Any]:
        if not code:
            raise ValidationError("currency code required")
        code_u = code.upper().strip()
        cid = _id("fe_ccy")
        return self.store.currencies.save(
            cid,
            {
                "currency_id": cid,
                "code": code_u,
                "name": name or code_u,
                "decimals": max(0, int(decimals)),
                "created_at": _now(),
            },
        )

    def register_cost_center(
        self, *, code: str, name: str, organization_id: str = ""
    ) -> dict[str, Any]:
        if not code or not name:
            raise ValidationError("cost center code and name required")
        cid = _id("fe_cc")
        return self.store.cost_centers.save(
            cid,
            {
                "cost_center_id": cid,
                "code": code,
                "name": name,
                "organization_id": organization_id,
                "created_at": _now(),
            },
        )

    def register_entity(
        self, *, name: str, entity_type: str = "other", ref_id: str = ""
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("entity name required")
        et = entity_type.lower().strip()
        if et not in self.entity_types:
            raise ValidationError(f"entity_type must be one of {self.entity_types}")
        eid = _id("fe_ent")
        return self.store.financial_entities.save(
            eid,
            {
                "entity_id": eid,
                "name": name,
                "entity_type": et,
                "ref_id": ref_id,
                "created_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "organizations": self.store.organizations.count(),
            "customers": self.store.customers.count(),
            "vendors": self.store.vendors.count(),
            "financial_accounts": self.store.financial_accounts.count(),
            "currencies": self.store.currencies.count(),
            "cost_centers": self.store.cost_centers.count(),
            "financial_entities": self.store.financial_entities.count(),
        }
