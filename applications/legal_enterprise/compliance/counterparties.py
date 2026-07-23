"""Counterparty due diligence — KYC/KYB and risk classification."""

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


class CounterpartyDueDiligence:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.cp_counterparty_types)
        self.risk_levels = list(DEFAULT_CONFIG.cp_risk_levels)

    def register(
        self,
        *,
        name: str,
        counterparty_type: str = "vendor",
        country: str = "",
        risk_level: str = "medium",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        ct = counterparty_type.lower().strip()
        if ct not in self.types:
            raise ValidationError(f"counterparty_type must be one of {self.types}")
        rl = risk_level.lower().strip()
        if rl not in self.risk_levels:
            raise ValidationError(f"risk_level must be one of {self.risk_levels}")
        cid = _id("cp_ctp")
        return self.store.cp_counterparties.save(
            cid,
            {
                "counterparty_id": cid,
                "name": name,
                "counterparty_type": ct,
                "country": country,
                "risk_level": rl,
                "at": _now(),
            },
        )

    def register_vendor(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(counterparty_type="vendor", **kwargs)

    def register_customer(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(counterparty_type="customer", **kwargs)

    def register_partner(self, **kwargs: Any) -> dict[str, Any]:
        return self.register(counterparty_type="partner", **kwargs)

    def run_kyc(self, *, counterparty_id: str, status: str = "passed") -> dict[str, Any]:
        if self.store.cp_counterparties.get(counterparty_id) is None:
            raise NotFoundError("counterparty", counterparty_id)
        kid = _id("cp_kyc")
        return self.store.cp_kyc.save(
            kid,
            {
                "kyc_id": kid,
                "counterparty_id": counterparty_id,
                "status": status,
                "at": _now(),
            },
        )

    def run_kyb(self, *, counterparty_id: str, status: str = "passed") -> dict[str, Any]:
        if self.store.cp_counterparties.get(counterparty_id) is None:
            raise NotFoundError("counterparty", counterparty_id)
        kid = _id("cp_kyb")
        return self.store.cp_kyb.save(
            kid,
            {
                "kyb_id": kid,
                "counterparty_id": counterparty_id,
                "status": status,
                "at": _now(),
            },
        )

    def classify_risk(self, *, counterparty_id: str, risk_level: str) -> dict[str, Any]:
        ctp = self.store.cp_counterparties.get(counterparty_id)
        if ctp is None:
            raise NotFoundError("counterparty", counterparty_id)
        rl = risk_level.lower().strip()
        if rl not in self.risk_levels:
            raise ValidationError(f"risk_level must be one of {self.risk_levels}")
        ctp["risk_level"] = rl
        self.store.cp_counterparties.save(counterparty_id, ctp)
        rid = _id("cp_crsk")
        return self.store.cp_counterparty_risk.save(
            rid,
            {
                "classification_id": rid,
                "counterparty_id": counterparty_id,
                "risk_level": rl,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "counterparties": self.store.cp_counterparties.count(),
            "kyc": self.store.cp_kyc.count(),
            "kyb": self.store.cp_kyb.count(),
            "risk_classifications": self.store.cp_counterparty_risk.count(),
        }
