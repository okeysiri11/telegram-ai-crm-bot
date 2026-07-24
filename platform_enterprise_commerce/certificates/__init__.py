"""Gift Certificate Engine — Sprint 22.7."""

from __future__ import annotations

from typing import Any
from datetime import datetime, timedelta, timezone


class GiftCertificateEngine:
    def issue(self, *, face_value: float, customer_id: str = "", days_valid: int = 365) -> dict[str, Any]:
        if face_value <= 0:
            raise ValueError("face_value must be positive")
        now = datetime.now(timezone.utc)
        return {
            "face_value": float(face_value),
            "balance": float(face_value),
            "customer_id": customer_id or None,
            "status": "issued",
            "expires_at": (now + timedelta(days=days_valid)).isoformat(),
            "history": [{"event": "issued", "amount": float(face_value)}],
        }

    def activate(self, cert: dict[str, Any]) -> dict[str, Any]:
        updated = dict(cert)
        updated["status"] = "active"
        history = list(updated.get("history") or [])
        history.append({"event": "activated", "amount": 0})
        updated["history"] = history
        return updated

    def redeem(self, cert: dict[str, Any], *, amount: float) -> dict[str, Any]:
        if cert.get("status") not in ("active", "issued"):
            raise ValueError("certificate is not redeemable")
        amount = float(amount)
        if amount <= 0:
            raise ValueError("redeem amount must be positive")
        balance = float(cert.get("balance", 0))
        if amount > balance:
            raise ValueError("redeem exceeds certificate balance")
        updated = dict(cert)
        updated["balance"] = round(balance - amount, 2)
        updated["status"] = "exhausted" if updated["balance"] <= 0 else "active"
        history = list(updated.get("history") or [])
        history.append({"event": "redeem", "amount": amount})
        updated["history"] = history
        return updated
