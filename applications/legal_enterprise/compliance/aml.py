"""Sanctions & AML — watchlists, PEP, scoring, transaction review."""

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


class SanctionsAML:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.risk_levels = list(DEFAULT_CONFIG.cp_risk_levels)

    def monitor_sanctions(self, *, name: str, list_name: str = "UN", matched: bool = False) -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        sid = _id("cp_san")
        return self.store.cp_sanctions.save(
            sid,
            {
                "screening_id": sid,
                "name": name,
                "list_name": list_name,
                "matched": bool(matched),
                "at": _now(),
            },
        )

    def register_pep(self, *, name: str, role: str = "", country: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("PEP name required")
        pid = _id("cp_pep")
        return self.store.cp_peps.save(
            pid,
            {
                "pep_id": pid,
                "name": name,
                "role": role,
                "country": country,
                "at": _now(),
            },
        )

    def aml_score(
        self, *, counterparty_id: str = "", name: str = "", score: float = 40.0
    ) -> dict[str, Any]:
        if counterparty_id and self.store.cp_counterparties.get(counterparty_id) is None:
            raise NotFoundError("counterparty", counterparty_id)
        if not counterparty_id and not name:
            raise ValidationError("counterparty_id or name required")
        sc = max(0.0, min(100.0, float(score)))
        level = "high" if sc >= 70 else "medium" if sc >= 40 else "low"
        aid = _id("cp_aml")
        return self.store.cp_aml_scores.save(
            aid,
            {
                "aml_id": aid,
                "counterparty_id": counterparty_id,
                "name": name,
                "score": sc,
                "risk_level": level,
                "at": _now(),
            },
        )

    def watchlist(self, *, name: str, list_name: str = "internal", hit: bool = False) -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        wid = _id("cp_wl")
        return self.store.cp_watchlists.save(
            wid,
            {
                "watch_id": wid,
                "name": name,
                "list_name": list_name,
                "hit": bool(hit),
                "at": _now(),
            },
        )

    def detect_high_risk(self, *, entity_name: str, reason: str = "") -> dict[str, Any]:
        if not entity_name:
            raise ValidationError("entity_name required")
        hid = _id("cp_hr")
        return self.store.cp_high_risk.save(
            hid,
            {
                "detection_id": hid,
                "entity_name": entity_name,
                "reason": reason or "elevated AML indicators",
                "at": _now(),
            },
        )

    def review_transaction(
        self,
        *,
        transaction_ref: str,
        amount: float = 0.0,
        counterparty_id: str = "",
        status: str = "cleared",
    ) -> dict[str, Any]:
        if not transaction_ref:
            raise ValidationError("transaction_ref required")
        tid = _id("cp_txn")
        return self.store.cp_txn_reviews.save(
            tid,
            {
                "review_id": tid,
                "transaction_ref": transaction_ref,
                "amount": float(amount),
                "counterparty_id": counterparty_id,
                "status": status,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "sanctions": self.store.cp_sanctions.count(),
            "peps": self.store.cp_peps.count(),
            "aml_scores": self.store.cp_aml_scores.count(),
            "watchlists": self.store.cp_watchlists.count(),
            "high_risk": self.store.cp_high_risk.count(),
            "txn_reviews": self.store.cp_txn_reviews.count(),
        }
