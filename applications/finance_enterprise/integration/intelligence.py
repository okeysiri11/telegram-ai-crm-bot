"""Enterprise financial intelligence — cross-platform profitability, cash flow, risk."""

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


class EnterpriseFinancialIntelligence:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.analytic_types = list(DEFAULT_CONFIG.int_analytic_types)

    def analyze(
        self,
        *,
        analytic_type: str,
        subject: str,
        value: float = 0.0,
        platforms: list[str] | None = None,
        detail: str = "",
    ) -> dict[str, Any]:
        at = analytic_type.lower().strip()
        if at not in self.analytic_types:
            raise ValidationError(f"analytic_type must be one of {self.analytic_types}")
        if not subject:
            raise ValidationError("subject required")
        aid = _id("int_bi")
        return self.store.int_analytics.save(
            aid,
            {
                "analytic_id": aid,
                "analytic_type": at,
                "subject": subject,
                "value": float(value),
                "platforms": platforms or [],
                "detail": detail or f"{at.replace('_', ' ')} for {subject}",
                "at": _now(),
            },
        )

    def map_dependency(
        self, *, from_platform: str, to_platform: str, dependency: str, strength: float = 0.5
    ) -> dict[str, Any]:
        if not from_platform or not to_platform or not dependency:
            raise ValidationError("from_platform, to_platform, and dependency required")
        did = _id("int_dep")
        return self.store.int_dependencies.save(
            did,
            {
                "dependency_id": did,
                "from_platform": from_platform.lower(),
                "to_platform": to_platform.lower(),
                "dependency": dependency,
                "strength": max(0.0, min(1.0, float(strength))),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "analytics": self.store.int_analytics.count(),
            "dependencies": self.store.int_dependencies.count(),
            "types": self.analytic_types,
        }
