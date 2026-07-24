"""Customer profile — Sprint 22.2."""

from __future__ import annotations

from typing import Any


class CustomerProfile:
    def create(
        self,
        *,
        name: str,
        preferences: list[str] | None = None,
        allergies: list[str] | None = None,
        crm_ref: str = "enterprise_crm",
    ) -> dict[str, Any]:
        if not name:
            raise ValueError("customer name is required")
        return {
            "name": name.strip(),
            "visit_history": [],
            "photos": [],
            "notes": [],
            "preferences": list(preferences or []),
            "allergies": list(allergies or []),
            "bonuses": 0.0,
            "certificates": [],
            "memberships": [],
            "purchase_history": [],
            "crm_ref": crm_ref,
            "uses_enterprise_crm": True,
        }
