"""Financial controls — limits, permissions, approval matrix, audit, fraud flags."""

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


class FinancialControls:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.roles = list(DEFAULT_CONFIG.finance_roles)

    def set_limit(
        self, *, role: str, max_amount: float, currency: str = "USD"
    ) -> dict[str, Any]:
        if role not in self.roles:
            raise ValidationError(f"role must be one of {self.roles}")
        if float(max_amount) <= 0:
            raise ValidationError("max_amount must be positive")
        lid = _id("pay_lim")
        return self.store.pay_limits.save(
            lid,
            {
                "limit_id": lid,
                "role": role,
                "max_amount": float(max_amount),
                "currency": currency.upper(),
                "at": _now(),
            },
        )

    def grant(self, *, role: str, permission: str, resource: str = "payments") -> dict[str, Any]:
        if role not in self.roles:
            raise ValidationError(f"role must be one of {self.roles}")
        if not permission:
            raise ValidationError("permission required")
        pid = _id("pay_perm")
        return self.store.pay_permissions.save(
            pid,
            {
                "permission_id": pid,
                "role": role,
                "permission": permission,
                "resource": resource,
                "at": _now(),
            },
        )

    def approval_rule(
        self, *, min_amount: float, required_role: str, currency: str = "USD"
    ) -> dict[str, Any]:
        if required_role not in self.roles:
            raise ValidationError(f"required_role must be one of {self.roles}")
        rid = _id("pay_mtx")
        return self.store.pay_approval_matrix.save(
            rid,
            {
                "rule_id": rid,
                "min_amount": float(min_amount),
                "required_role": required_role,
                "currency": currency.upper(),
                "at": _now(),
            },
        )

    def audit(self, *, action: str, actor: str = "system", detail: str = "") -> dict[str, Any]:
        if not action:
            raise ValidationError("action required")
        aid = _id("pay_aud")
        return self.store.pay_audit.save(
            aid,
            {
                "audit_id": aid,
                "action": action,
                "actor": actor,
                "detail": detail,
                "at": _now(),
            },
        )

    def fraud_flag(
        self, *, payment_id: str, reason: str, severity: str = "medium"
    ) -> dict[str, Any]:
        if not payment_id:
            raise ValidationError("payment_id required")
        if not reason:
            raise ValidationError("reason required")
        fid = _id("pay_frd")
        return self.store.pay_fraud_flags.save(
            fid,
            {
                "flag_id": fid,
                "payment_id": payment_id,
                "reason": reason,
                "severity": severity,
                "status": "open",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "limits": self.store.pay_limits.count(),
            "permissions": self.store.pay_permissions.count(),
            "approval_rules": self.store.pay_approval_matrix.count(),
            "audit_entries": self.store.pay_audit.count(),
            "fraud_flags": self.store.pay_fraud_flags.count(),
        }
