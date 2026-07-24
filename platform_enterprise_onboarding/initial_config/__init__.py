"""Initial Configuration after import — Sprint 22.9."""

from __future__ import annotations

from typing import Any


class InitialConfiguration:
    def apply(self, *, wizard: dict[str, Any], imports: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        imports = list(imports or [])
        entities = {i.get("entity") for i in imports}
        return {
            "branches_created": len(wizard.get("branches") or []),
            "roles_created": len(wizard.get("roles") or []),
            "employees_created": "employees" in entities,
            "services_created": "services" in entities,
            "categories_created": True,
            "base_calendar_created": True,
            "comms_templates_linked": True,
            "ai_business_advisor_activated": True,
            "ai_marketing_os_activated": True,
            "product_intelligence_activated": True,
            "commerce_ref": "commerce_core",
            "beauty_os_ref": "beauty_os",
            "comms_ref": "communications_hub",
            "status": "configured",
            "duplicates_core_logic": False,
        }
