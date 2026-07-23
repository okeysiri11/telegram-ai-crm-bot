"""Billing engine — subscriptions, invoices, payments, limits, history."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.models import BILLING_STATUSES, SUBSCRIPTION_STATUSES
from applications.enterprise_hub.tenancy.tenant_registry import TenantRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class BillingEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tenants = TenantRegistry(self.store)

    def subscribe(
        self,
        *,
        tenant_id: str,
        plan: str = "business",
        amount: float = 0.0,
        currency: str = "USD",
    ) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        sid = _id("tn_sub")
        return self.store.tn_subscriptions.save(
            sid,
            {
                "subscription_id": sid,
                "tenant_id": tenant_id,
                "plan": plan,
                "amount": float(amount),
                "currency": currency,
                "status": "active",
                "created_at": _now(),
            },
        )

    def invoice(
        self,
        *,
        tenant_id: str,
        subscription_id: str,
        amount: float,
        currency: str = "USD",
    ) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        sub = self.store.tn_subscriptions.get(subscription_id)
        if not sub:
            raise NotFoundError(f"subscription not found: {subscription_id}")
        iid = _id("tn_inv")
        return self.store.tn_invoices.save(
            iid,
            {
                "invoice_id": iid,
                "tenant_id": tenant_id,
                "subscription_id": subscription_id,
                "amount": float(amount),
                "currency": currency,
                "status": "open",
                "created_at": _now(),
            },
        )

    def pay(self, *, invoice_id: str, method: str = "card") -> dict[str, Any]:
        inv = self.store.tn_invoices.get(invoice_id)
        if not inv:
            raise NotFoundError(f"invoice not found: {invoice_id}")
        pid = _id("tn_pay")
        payment = self.store.tn_payments.save(
            pid,
            {
                "payment_id": pid,
                "invoice_id": invoice_id,
                "tenant_id": inv["tenant_id"],
                "amount": inv["amount"],
                "currency": inv.get("currency", "USD"),
                "method": method,
                "status": "succeeded",
                "at": _now(),
            },
        )
        inv["status"] = "paid"
        self.store.tn_invoices.save(invoice_id, inv)
        return payment

    def set_limits(self, *, tenant_id: str, limits: dict[str, Any]) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        if not isinstance(limits, dict) or not limits:
            raise ValidationError("limits dict is required")
        lid = _id("tn_lim")
        return self.store.tn_limits.save(
            lid,
            {
                "limit_id": lid,
                "tenant_id": tenant_id,
                "limits": limits,
                "billing_statuses": list(BILLING_STATUSES),
                "subscription_statuses": list(SUBSCRIPTION_STATUSES),
                "at": _now(),
            },
        )

    def history(self, *, tenant_id: str) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        return {
            "tenant_id": tenant_id,
            "subscriptions": [s for s in self.store.tn_subscriptions.list_all() if s.get("tenant_id") == tenant_id],
            "invoices": [i for i in self.store.tn_invoices.list_all() if i.get("tenant_id") == tenant_id],
            "payments": [p for p in self.store.tn_payments.list_all() if p.get("tenant_id") == tenant_id],
        }

    def status(self) -> dict[str, Any]:
        return {
            "subscriptions": self.store.tn_subscriptions.count(),
            "invoices": self.store.tn_invoices.count(),
            "payments": self.store.tn_payments.count(),
            "limits": self.store.tn_limits.count(),
        }
