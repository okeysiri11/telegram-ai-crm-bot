"""Client Account — Sprint 22.8."""

from __future__ import annotations

from typing import Any


class ClientAccount:
    def create(
        self,
        *,
        customer_id: str,
        name: str,
        phone: str = "",
        email: str = "",
    ) -> dict[str, Any]:
        if not customer_id or not name:
            raise ValueError("customer_id and name are required")
        return {
            "customer_id": customer_id,
            "name": name.strip(),
            "phone": phone,
            "email": email,
            "photos": [],
            "bonuses": 0.0,
            "certificates": [],
            "memberships": [],
            "visit_history": [],
            "purchase_history": [],
            "payment_history": [],
            "favorite_masters": [],
            "favorite_services": [],
            "crm_ref": "enterprise_crm",
            "commerce_ref": "commerce_core",
        }

    def enrich(
        self,
        account: dict[str, Any],
        *,
        bonuses: float | None = None,
        certificates: list[dict[str, Any]] | None = None,
        memberships: list[dict[str, Any]] | None = None,
        visits: list[dict[str, Any]] | None = None,
        purchases: list[dict[str, Any]] | None = None,
        payments: list[dict[str, Any]] | None = None,
        favorite_masters: list[str] | None = None,
        favorite_services: list[str] | None = None,
        photos: list[str] | None = None,
    ) -> dict[str, Any]:
        updated = dict(account)
        if bonuses is not None:
            updated["bonuses"] = float(bonuses)
        if certificates is not None:
            updated["certificates"] = list(certificates)
        if memberships is not None:
            updated["memberships"] = list(memberships)
        if visits is not None:
            updated["visit_history"] = list(visits)
        if purchases is not None:
            updated["purchase_history"] = list(purchases)
        if payments is not None:
            updated["payment_history"] = list(payments)
        if favorite_masters is not None:
            updated["favorite_masters"] = list(favorite_masters)
        if favorite_services is not None:
            updated["favorite_services"] = list(favorite_services)
        if photos is not None:
            updated["photos"] = list(photos)
        return updated
