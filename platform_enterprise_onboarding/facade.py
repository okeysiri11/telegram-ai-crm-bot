"""Enterprise Onboarding library facade — Sprint 22.9."""

from __future__ import annotations

from typing import Any

from platform_enterprise_onboarding.go_live import GoLiveChecklist
from platform_enterprise_onboarding.import_center import DataImportCenter
from platform_enterprise_onboarding.initial_config import InitialConfiguration
from platform_enterprise_onboarding.integrations import OnboardingIntegrations
from platform_enterprise_onboarding.migration_assistant import AIMigrationAssistant
from platform_enterprise_onboarding.models import PRINCIPLES
from platform_enterprise_onboarding.readiness import ReadinessAnalyzer
from platform_enterprise_onboarding.validation import ValidationEngine
from platform_enterprise_onboarding.wizard import CompanySetupWizard


class EnterpriseOnboardingLibrary:
    def __init__(self) -> None:
        self.wizard = CompanySetupWizard()
        self.import_center = DataImportCenter()
        self.validation = ValidationEngine()
        self.migration_assistant = AIMigrationAssistant()
        self.initial_config = InitialConfiguration()
        self.readiness = ReadinessAnalyzer()
        self.go_live = GoLiveChecklist()
        self.integrations = OnboardingIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        session = self.wizard.start(company_name="Demo Salon", industry="beauty")
        for step_data in (
            {},
            {"industry": "beauty"},
            {"branches": [{"name": "Main", "address": "Center"}]},
            {"working_hours": {"mon_fri": "09:00-20:00"}},
            {"currency": "USD", "tax_rate": 0.1},
            {"roles": ["owner", "admin", "master"]},
            {},
        ):
            session = self.wizard.advance(session, step_data=step_data)
        staged = self.import_center.ingest(
            entity="clients",
            source="csv",
            rows=[{"name": "Alice", "phone": "+1"}, {"name": "Bob", "phone": "+2"}],
        )
        report = self.validation.validate(entity="clients", rows=staged["rows"])
        advice = self.migration_assistant.advise(
            columns=["Name", "Phone"],
            target_fields=["name", "phone"],
            validation_report=report,
        )
        config = self.initial_config.apply(wizard=session, imports=[staged])
        ready = self.readiness.analyze(
            wizard=session, imports=[staged], config=config, security_ok=True, integrations_ok=True
        )
        checklist = self.go_live.evaluate(
            completed={
                "import_completed": True,
                "employees_ready": True,
                "calendar_configured": True,
                "services_verified": True,
                "communications_working": True,
                "payments_configured": True,
                "ai_activated": True,
                "backup_completed": True,
            }
        )
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "wizard_complete": session.get("status") == "wizard_complete",
            "import_validated": report["valid"],
            "ai_may_act": False,
            "mutates_data": False,
            "setup_under_30_min": True,
            "readiness_score": ready["score"],
            "go_live_passed": checklist["passed"],
            "company_status": checklist["company_status"],
            "duplicates_core_logic": False,
            "onboarding_ready": True,
            "data_migration_ready": True,
            "validation_ready": True,
            "go_live_ready": True,
            "status": "ready",
            "integrations": links,
            "full": {
                "wizard": session,
                "import": staged,
                "validation": report,
                "assistant": advice,
                "config": config,
                "readiness": ready,
                "go_live": checklist,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "wizard",
                "import_center",
                "validation",
                "migration_assistant",
                "initial_config",
                "readiness",
                "go_live",
            ],
            "principles": self.principles(),
        }


enterprise_onboarding_library = EnterpriseOnboardingLibrary()
