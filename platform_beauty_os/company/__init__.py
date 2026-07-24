"""Company profile — Sprint 22.2."""

from __future__ import annotations

from typing import Any


class CompanyProfile:
    def create(
        self,
        *,
        name: str,
        timezone: str = "UTC",
        currency: str = "USD",
        contacts: dict[str, Any] | None = None,
        social: dict[str, str] | None = None,
        tax: dict[str, Any] | None = None,
        schedule: dict[str, Any] | None = None,
        logo: str = "",
    ) -> dict[str, Any]:
        if not name or not str(name).strip():
            raise ValueError("company name is required")
        return {
            "name": name.strip(),
            "logo": logo,
            "branches": [],
            "schedule": schedule or {"mon-fri": "09:00-20:00", "sat": "10:00-18:00"},
            "contacts": contacts or {},
            "social": social or {},
            "tax": tax or {},
            "currency": currency,
            "timezone": timezone,
            "industry": "beauty",
        }
