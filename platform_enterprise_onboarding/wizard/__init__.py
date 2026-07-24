"""Company Setup Wizard — Sprint 22.9."""

from __future__ import annotations

from typing import Any

from platform_enterprise_onboarding.models import INDUSTRIES, WIZARD_STEPS


class CompanySetupWizard:
    def start(self, *, company_name: str, industry: str = "beauty") -> dict[str, Any]:
        if not company_name or not company_name.strip():
            raise ValueError("company_name is required")
        industry = (industry or "beauty").lower()
        if industry not in INDUSTRIES:
            raise ValueError(f"unsupported industry: {industry}")
        return {
            "company_name": company_name.strip(),
            "industry": industry,
            "steps": list(WIZARD_STEPS),
            "current_step": WIZARD_STEPS[0],
            "completed_steps": [],
            "status": "in_progress",
            "branches": [],
            "working_hours": {},
            "currency": None,
            "tax_rate": None,
            "roles": [],
        }

    def advance(self, session: dict[str, Any], *, step_data: dict[str, Any] | None = None) -> dict[str, Any]:
        step_data = step_data or {}
        updated = dict(session)
        current = updated.get("current_step") or WIZARD_STEPS[0]
        steps = list(WIZARD_STEPS)
        if current not in steps:
            raise ValueError(f"unknown step: {current}")

        if current == "company_registration":
            if step_data.get("company_name"):
                updated["company_name"] = str(step_data["company_name"]).strip()
        elif current == "industry_selection":
            industry = str(step_data.get("industry") or updated.get("industry") or "beauty").lower()
            if industry not in INDUSTRIES:
                raise ValueError(f"unsupported industry: {industry}")
            updated["industry"] = industry
        elif current == "branches":
            branches = list(step_data.get("branches") or updated.get("branches") or [])
            if not branches:
                raise ValueError("at least one branch is required")
            updated["branches"] = branches
        elif current == "working_hours":
            hours = dict(step_data.get("working_hours") or updated.get("working_hours") or {})
            if not hours:
                raise ValueError("working_hours required")
            updated["working_hours"] = hours
        elif current == "currency_taxes":
            currency = step_data.get("currency") or updated.get("currency")
            if not currency:
                raise ValueError("currency required")
            updated["currency"] = currency
            updated["tax_rate"] = float(step_data.get("tax_rate", updated.get("tax_rate") or 0))
        elif current == "roles":
            roles = list(step_data.get("roles") or updated.get("roles") or [])
            if not roles:
                raise ValueError("at least one role is required")
            updated["roles"] = roles
        elif current == "readiness_check":
            updated["wizard_ready"] = True

        completed = list(updated.get("completed_steps") or [])
        if current not in completed:
            completed.append(current)
        updated["completed_steps"] = completed
        idx = steps.index(current)
        if idx + 1 < len(steps):
            updated["current_step"] = steps[idx + 1]
            updated["status"] = "in_progress"
        else:
            updated["current_step"] = None
            updated["status"] = "wizard_complete"
            updated["wizard_ready"] = True
        return updated
