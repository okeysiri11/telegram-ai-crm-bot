# LegalEnterpriseApplication — Sprint 17.0 foundation.

from __future__ import annotations

from typing import Any

from applications.legal_enterprise.cases import CaseManagement
from applications.legal_enterprise.config import DEFAULT_CONFIG, LegalEnterpriseConfig
from applications.legal_enterprise.courts import CourtInfrastructure
from applications.legal_enterprise.legal_registry import LegalRegistry
from applications.legal_enterprise.legislation import LegislationRegistry
from applications.legal_enterprise.legislation_intelligence.facade import LegislationIntelligenceSuite
from applications.legal_enterprise.services import LegalDashboard, LegalKnowledge
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


class LegalEnterpriseApplication:
    def __init__(
        self,
        *,
        config: LegalEnterpriseConfig | None = None,
        store: LegalEnterpriseStore | None = None,
        legislation_intelligence_svc: LegislationIntelligenceSuite | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or legal_enterprise_store
        self.registry = LegalRegistry(self.store)
        self.legislation = LegislationRegistry(self.store)
        self.courts = CourtInfrastructure(self.store)
        self.cases = CaseManagement(self.store)
        self.dashboard = LegalDashboard(self.store)
        self.knowledge = LegalKnowledge(self.store)
        self.legislation_intelligence = legislation_intelligence_svc or LegislationIntelligenceSuite(
            self.store
        )

    def reset(self) -> None:
        self.store.reset()

    def bootstrap(self) -> dict[str, Any]:
        entity = self.registry.register_entity(
            name="LexCorp Holdings",
            entity_type="corporation",
            jurisdiction="US-DE",
            registration_no="DE-1001",
        )
        individual = self.registry.register_individual(
            full_name="Alex Morgan",
            national_id="ID-7788",
            residency="US-NY",
        )
        attorney = self.registry.register_attorney(
            full_name="Jordan Lee",
            bar_number="BAR-4421",
            firm="Lee & Partners",
            specializations=["commercial", "litigation"],
        )
        agency = self.registry.register_agency(
            name="Ministry of Justice",
            agency_type="ministry",
            country="US",
        )
        role_plaintiff = self.registry.register_role(role_code="plaintiff")
        role_defendant = self.registry.register_role(role_code="defendant")
        role_counsel = self.registry.register_role(role_code="counsel")

        constitution = self.legislation.register_constitution(
            title="National Constitution",
            code="CONST-1",
            jurisdiction="national",
            articles=120,
        )
        civil = self.legislation.register_civil_code(
            title="Civil Code",
            code="CIV-1",
            jurisdiction="national",
            articles=2500,
        )
        commercial = self.legislation.register_commercial_code(
            title="Commercial Code",
            code="COM-1",
            jurisdiction="national",
        )
        criminal = self.legislation.register_criminal_code(
            title="Criminal Code",
            code="CRIM-1",
            jurisdiction="national",
        )
        admin = self.legislation.register_administrative_code(
            title="Administrative Code",
            code="ADM-1",
            jurisdiction="national",
        )
        tax = self.legislation.register_tax_code(
            title="Tax Code",
            code="TAX-1",
            jurisdiction="national",
        )
        labor = self.legislation.register_labor_code(
            title="Labor Code",
            code="LAB-1",
            jurisdiction="national",
        )
        treaty = self.legislation.register_treaty(
            title="Cross-Border Judicial Assistance Treaty",
            code="TRT-1",
            jurisdiction="international",
        )

        regional = self.courts.register_regional(
            name="Central Regional Court",
            region="central",
            jurisdiction_code="REG-C",
        )
        appeal = self.courts.register_appeal(
            name="Central Court of Appeal",
            region="central",
            jurisdiction_code="APL-C",
        )
        supreme = self.courts.register_supreme(
            name="Supreme Court",
            jurisdiction_code="SUP-N",
        )
        self.courts.define_hierarchy(
            lower_court_id=regional["court_id"],
            higher_court_id=appeal["court_id"],
        )
        self.courts.define_hierarchy(
            lower_court_id=appeal["court_id"],
            higher_court_id=supreme["court_id"],
        )
        jurisdiction = self.courts.register_jurisdiction(
            code="REG-C",
            name="Central Region",
            territory="central",
            court_id=regional["court_id"],
        )
        category = self.courts.register_case_category(
            code="commercial",
            name="Commercial Dispute",
            description="Contract and commercial litigation",
        )

        judge = self.registry.register_judge(
            full_name="Hon. Sam Rivera",
            court_id=regional["court_id"],
            title="Presiding Judge",
        )

        case = self.cases.register_case(
            title="LexCorp v. Contoso Trade Dispute",
            case_number="CASE-2026-001",
            court_id=regional["court_id"],
            category_code="commercial",
            status="filed",
        )
        self.cases.add_participant(
            case_id=case["case_id"],
            role_code="plaintiff",
            party_name=entity["name"],
            party_ref=entity["entity_id"],
        )
        self.cases.add_participant(
            case_id=case["case_id"],
            role_code="counsel",
            party_name=attorney["full_name"],
            party_ref=attorney["attorney_id"],
        )
        self.cases.add_participant(
            case_id=case["case_id"],
            role_code="defendant",
            party_name="Contoso Trading LLC",
        )
        doc = self.cases.register_document(
            case_id=case["case_id"],
            title="Complaint",
            document_type="filing",
            uri="vault://cases/CASE-2026-001/complaint.pdf",
        )
        evidence = self.cases.register_evidence(
            case_id=case["case_id"],
            label="Master Supply Agreement",
            evidence_type="contract",
            description="Signed MSA dated 2024-03-01",
        )
        task = self.cases.create_task(
            case_id=case["case_id"],
            title="Prepare discovery schedule",
            assignee=attorney["full_name"],
            due_on="2026-08-01",
        )
        note = self.cases.add_note(
            case_id=case["case_id"],
            author=attorney["full_name"],
            body="Initial filing complete; awaiting service confirmation.",
        )

        self.knowledge.publish(base="law", key=civil["legislation_id"], payload={"code": "CIV-1"})
        self.knowledge.publish(base="court", key=regional["court_id"], payload={"level": "regional"})
        self.knowledge.publish(base="case", key=case["case_id"], payload={"number": case["case_number"]})
        self.knowledge.publish(base="document", key=doc["document_id"], payload={"title": doc["title"]})
        self.knowledge.relate(
            from_base="case",
            from_key=case["case_id"],
            to_base="court",
            to_key=regional["court_id"],
            relation="filed_in",
        )
        self.knowledge.relate(
            from_base="case",
            from_key=case["case_id"],
            to_base="law",
            to_key=civil["legislation_id"],
            relation="cites",
        )
        self.knowledge.relate(
            from_base="document",
            from_key=doc["document_id"],
            to_base="case",
            to_key=case["case_id"],
            relation="belongs_to",
        )

        dash = self.dashboard.render(dashboard_type="legal")
        return {
            "bootstrap": True,
            "entity_id": entity["entity_id"],
            "individual_id": individual["individual_id"],
            "attorney_id": attorney["attorney_id"],
            "judge_id": judge["judge_id"],
            "agency_id": agency["agency_id"],
            "role_plaintiff_id": role_plaintiff["role_id"],
            "role_defendant_id": role_defendant["role_id"],
            "role_counsel_id": role_counsel["role_id"],
            "constitution_id": constitution["legislation_id"],
            "civil_code_id": civil["legislation_id"],
            "commercial_code_id": commercial["legislation_id"],
            "criminal_code_id": criminal["legislation_id"],
            "administrative_code_id": admin["legislation_id"],
            "tax_code_id": tax["legislation_id"],
            "labor_code_id": labor["legislation_id"],
            "treaty_id": treaty["legislation_id"],
            "regional_court_id": regional["court_id"],
            "appeal_court_id": appeal["court_id"],
            "supreme_court_id": supreme["court_id"],
            "jurisdiction_id": jurisdiction["jurisdiction_id"],
            "category_id": category["category_id"],
            "case_id": case["case_id"],
            "document_id": doc["document_id"],
            "evidence_id": evidence["evidence_id"],
            "task_id": task["task_id"],
            "note_id": note["note_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": self.config.application_version,
        }

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "application": self.config.application,
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "release_status": self.config.release_status,
            "enterprise_foundation": self.config.enterprise_foundation,
            "platform_dependency": self.config.platform_dependency,
            "ecosystem_dependency": self.config.ecosystem_dependency,
            "api_prefix": self.config.api_prefix,
            "legal_enterprise_foundation_ready": True,
            "legal_registry_ready": True,
            "legislation_registry_ready": True,
            "court_infrastructure_ready": True,
            "case_management_foundation_ready": True,
            "legal_knowledge_graph_ready": True,
            "legislation_intelligence_ready": True,
            "ai_legal_search_ready": True,
            "regulatory_intelligence_ready": True,
            "legal_knowledge_platform_ready": True,
            "engines": {
                "legal_registry": self.config.legal_registry,
                "legislation_registry": self.config.legislation_registry,
                "court_infrastructure": self.config.court_infrastructure,
                "case_management": self.config.case_management,
                "legislation_intelligence": self.config.legislation_intelligence,
                "knowledge": self.config.knowledge,
                "analytics": self.config.analytics,
            },
            "registry": self.registry.status(),
            "legislation": self.legislation.status(),
            "courts": self.courts.status(),
            "cases": self.cases.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
            "legislation_intelligence": self.legislation_intelligence.status(),
        }


legal_enterprise = LegalEnterpriseApplication()
