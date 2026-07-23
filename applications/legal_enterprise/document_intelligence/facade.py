"""Document Intelligence Suite facade — Sprint 17.4."""

from __future__ import annotations

from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.document_intelligence.clauses import ClauseIntelligence
from applications.legal_enterprise.document_intelligence.comparison import DocumentComparison
from applications.legal_enterprise.document_intelligence.contracts import ContractBuilder
from applications.legal_enterprise.document_intelligence.drafting import AIDraftingAssistant
from applications.legal_enterprise.document_intelligence.ingest import DocumentIngest
from applications.legal_enterprise.document_intelligence.risk import AIRiskReview
from applications.legal_enterprise.document_intelligence.services import (
    DocumentIntelligenceDashboard,
    DocumentIntelligenceKnowledge,
)
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


class DocumentIntelligenceSuite:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.contracts = ContractBuilder(self.store)
        self.ingest = DocumentIngest(self.store)
        self.clauses = ClauseIntelligence(self.store)
        self.risk = AIRiskReview(self.store)
        self.comparison = DocumentComparison(self.store)
        self.drafting = AIDraftingAssistant(self.store)
        self.dashboard = DocumentIntelligenceDashboard(self.store)
        self.knowledge = DocumentIntelligenceKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        conf = self.contracts.add_clause(
            title="Confidentiality", kind="confidentiality", text="Parties shall keep confidential information secret.", mandatory=True
        )
        indem = self.contracts.add_clause(
            title="Indemnity", kind="indemnity", text="Each party indemnifies the other for third-party claims.", mandatory=True
        )
        term = self.contracts.add_clause(
            title="Termination", kind="termination", text="Either party may terminate with 30 days notice.", mandatory=False
        )
        liab = self.contracts.add_clause(
            title="Limitation of Liability", kind="liability", text="Aggregate liability is capped at fees paid.", mandatory=True
        )
        pay = self.contracts.add_clause(
            title="Payment", kind="payment", text="Invoices are due within 30 days.", mandatory=False
        )

        tpl = self.contracts.register_template(
            name="Enterprise NDA Template",
            contract_type="nda",
            clauses=[conf["clause_id"], term["clause_id"]],
            body="Mutual non-disclosure agreement template.",
        )
        sales_tpl = self.contracts.register_template(
            name="Sales Contract Template",
            contract_type="sales",
            clauses=[pay["clause_id"], liab["clause_id"], indem["clause_id"]],
        )

        nda = self.contracts.generate_nda(
            title="LexCorp-Contoso Mutual NDA",
            parties=["LexCorp Holdings", "Contoso Trading LLC"],
            template_id=tpl["template_id"],
            clause_ids=[conf["clause_id"], term["clause_id"]],
        )
        sales = self.contracts.generate_sales(
            title="Master Sales Agreement",
            parties=["LexCorp Holdings", "Contoso Trading LLC"],
            template_id=sales_tpl["template_id"],
            clause_ids=[pay["clause_id"], liab["clause_id"], indem["clause_id"]],
        )
        service = self.contracts.generate_service(
            title="Managed Services Agreement",
            parties=["LexCorp Holdings", "Acme Ops"],
            clause_ids=[term["clause_id"], liab["clause_id"]],
        )
        employment = self.contracts.generate_employment(
            title="Employment Agreement — Counsel",
            parties=["LexCorp Holdings", "Alex Morgan"],
            clause_ids=[conf["clause_id"]],
        )
        lease = self.contracts.generate_lease(
            title="Office Lease Agreement",
            parties=["LexCorp Holdings", "Property Co"],
            clause_ids=[term["clause_id"], pay["clause_id"]],
        )
        custom = self.contracts.generate_custom(
            title="Custom Collaboration Agreement",
            parties=["LexCorp Holdings", "Partner LLC"],
            clause_ids=[conf["clause_id"], indem["clause_id"]],
            custom_body="Custom collaboration terms with reasonable efforts language.",
        )

        pdf = self.ingest.import_document(
            title="Signed NDA Scan",
            format="pdf",
            content="confidentiality indemnity termination payment reasonable efforts",
        )
        docx = self.ingest.import_document(
            title="MSA Draft.docx",
            format="docx",
            content="payment liability indemnity termination",
        )
        self.ingest.process_pdf(document_id=pdf["document_id"])
        self.ingest.process_docx(document_id=docx["document_id"])
        ocr = self.ingest.run_ocr(document_id=pdf["document_id"])
        parsed = self.ingest.parse(document_id=docx["document_id"])
        meta = self.ingest.extract_metadata(document_id=pdf["document_id"])
        self.ingest.classify(document_id=pdf["document_id"], label="nda")
        self.ingest.classify(document_id=docx["document_id"], label="sales")

        det = self.clauses.detect(contract_id=custom["contract_id"])
        self.clauses.classify_clause(clause_text="Governing law is national law.", kind="governing_law")
        validation = self.clauses.validate_mandatory(contract_id=nda["contract_id"])
        self.clauses.detect_missing(contract_id=sales["contract_id"])
        dups = self.clauses.detect_duplicates(contract_id=sales["contract_id"])
        cmp_cls = self.clauses.compare_clauses(clause_a=conf["clause_id"], clause_b=indem["clause_id"])

        self.risk.detect_risks(contract_id=custom["contract_id"])
        self.risk.detect_ambiguous(contract_id=custom["contract_id"])
        self.risk.detect_contradictions(contract_id=sales["contract_id"])
        self.risk.detect_unbalanced(contract_id=sales["contract_id"])
        self.risk.compliance_review(contract_id=nda["contract_id"])
        self.risk.gap_analysis(contract_id=service["contract_id"])
        rev = self.risk.recommend_revisions(contract_id=custom["contract_id"])
        score = self.risk.risk_score(contract_id=custom["contract_id"])

        vcmp = self.comparison.compare_versions(document_a=pdf["document_id"], document_b=docx["document_id"])
        self.comparison.track_change(document_id=docx["document_id"], change="Updated liability cap", author="Jordan Lee")
        redline = self.comparison.generate_redline(document_a=pdf["document_id"], document_b=docx["document_id"])
        sim = self.comparison.similarity(document_a=pdf["document_id"], document_b=docx["document_id"])
        apr = self.comparison.request_approval(
            document_id=docx["document_id"], requester="Jordan Lee", approver="GC"
        )

        draft = self.drafting.draft(prompt="Draft NDA for software evaluation", contract_type="nda")
        suggest = self.drafting.suggest_clause(prompt="Add data processing terms", kind="compliance")
        self.drafting.optimize_language(prompt="Party shall use best efforts to perform")
        self.drafting.plain_language(prompt="Indemnify and hold harmless")
        summary = self.drafting.summarize(prompt=custom["body"])
        nego = self.drafting.negotiate(prompt="Counterparty resists mutual indemnity")

        self.knowledge.publish(base="document", key=pdf["document_id"], payload={"title": pdf["title"]})
        self.knowledge.publish(base="clause", key=conf["clause_id"], payload={"kind": "confidentiality"})
        self.knowledge.publish(base="contract", key=nda["contract_id"], payload={"type": "nda"})
        self.knowledge.publish(base="risk", key=score["risk_id"], payload={"score": score["score"]})
        self.knowledge.publish(base="template", key=tpl["template_id"], payload={"name": tpl["name"]})

        dash = self.dashboard.render(dashboard_type="contract")
        return {
            "bootstrap": True,
            "template_id": tpl["template_id"],
            "clause_id": conf["clause_id"],
            "nda_id": nda["contract_id"],
            "sales_id": sales["contract_id"],
            "service_id": service["contract_id"],
            "employment_id": employment["contract_id"],
            "lease_id": lease["contract_id"],
            "custom_id": custom["contract_id"],
            "pdf_id": pdf["document_id"],
            "docx_id": docx["document_id"],
            "ocr_id": ocr["ocr_id"],
            "parse_id": parsed["parse_id"],
            "metadata_id": meta["metadata_id"],
            "detection_id": det["detection_id"],
            "validation_id": validation["validation_id"],
            "duplicate_id": dups["duplicate_id"],
            "clause_compare_id": cmp_cls["comparison_id"],
            "revision_id": rev["risk_id"],
            "risk_score_id": score["risk_id"],
            "version_compare_id": vcmp["comparison_id"],
            "redline_id": redline["redline_id"],
            "similarity_id": sim["similarity_id"],
            "approval_id": apr["approval_id"],
            "draft_id": draft["draft_id"],
            "suggest_id": suggest["draft_id"],
            "summary_id": summary["draft_id"],
            "negotiate_id": nego["draft_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "contracts": self.contracts.status(),
            "ingest": self.ingest.status(),
            "clauses": self.clauses.status(),
            "risk": self.risk.status(),
            "comparison": self.comparison.status(),
            "drafting": self.drafting.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


document_intelligence = DocumentIntelligenceSuite()
