"""Legislation Intelligence Suite facade — Sprint 17.1."""

from __future__ import annotations

from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.legislation_intelligence.analysis import AILegalAnalysis
from applications.legal_enterprise.legislation_intelligence.cross_references import CrossReferences
from applications.legal_enterprise.legislation_intelligence.regulatory import RegulatoryIntelligence
from applications.legal_enterprise.legislation_intelligence.repository import LegislationRepository
from applications.legal_enterprise.legislation_intelligence.search import AILegalSearch
from applications.legal_enterprise.legislation_intelligence.services import (
    LegislationIntelligenceDashboard,
    LegislationIntelligenceKnowledge,
)
from applications.legal_enterprise.legislation_intelligence.version_control import VersionControl
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


class LegislationIntelligenceSuite:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.repository = LegislationRepository(self.store)
        self.versions = VersionControl(self.store)
        self.regulatory = RegulatoryIntelligence(self.store)
        self.search = AILegalSearch(self.store)
        self.cross_refs = CrossReferences(self.store)
        self.analysis = AILegalAnalysis(self.store)
        self.dashboard = LegislationIntelligenceDashboard(self.store)
        self.knowledge = LegislationIntelligenceKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        constitution = self.repository.ingest_constitution(
            title="National Constitution",
            code="CONST-LI-1",
            jurisdiction="national",
            authority="Constituent Assembly",
            effective_on="1991-01-01",
            body="Foundational constitutional order.",
            articles=[{"number": "1", "title": "Sovereignty", "text": "The people are sovereign."}],
        )
        code = self.repository.ingest_code(
            title="Civil Code",
            code="CIV-LI-1",
            jurisdiction="national",
            authority="Parliament",
            effective_on="2000-01-01",
            body="General civil obligations and contracts.",
            articles=[
                {"number": "10", "title": "Contracts", "text": "Contracts require mutual consent."},
                {"number": "11", "title": "Damages", "text": "Breach creates liability for damages."},
            ],
        )
        law = self.repository.ingest_law(
            title="Data Protection Law",
            code="DPL-1",
            jurisdiction="national",
            authority="Parliament",
            effective_on="2020-05-25",
            body="Personal data processing obligations for controllers.",
        )
        regulation = self.repository.ingest_regulation(
            title="Data Protection Implementing Regulation",
            code="DPR-1",
            jurisdiction="national",
            authority="Cabinet",
            effective_on="2020-08-01",
            body="Implements DPL-1 for regulated industries.",
        )
        resolution = self.repository.ingest_government_resolution(
            title="Government Resolution on Digital Identity",
            code="GR-88",
            jurisdiction="national",
            authority="Government",
        )
        order = self.repository.ingest_ministerial_order(
            title="Ministerial Order on Filing Formats",
            code="MO-12",
            jurisdiction="national",
            authority="Ministry of Justice",
        )
        treaty = self.repository.ingest_treaty(
            title="Mutual Legal Assistance Treaty",
            code="MLAT-1",
            jurisdiction="international",
            authority="States Parties",
        )
        local = self.repository.ingest_local_regulation(
            title="City Zoning Ordinance",
            code="LOC-Z-1",
            jurisdiction="city-central",
            authority="City Council",
        )

        hist = self.versions.record_history(
            document_id=law["document_id"], version="1.0", summary="Initial enactment", effective_on="2020-05-25"
        )
        self.versions.record_history(
            document_id=law["document_id"], version="1.1", summary="Clarified controller duties", effective_on="2022-01-01"
        )
        cmp_ = self.versions.compare_versions(
            document_id=law["document_id"],
            from_version="1.0",
            to_version="1.1",
            changes=["Article 5 expanded", "Definitions updated"],
        )
        amd = self.versions.track_amendment(
            document_id=law["document_id"],
            amendment_ref="AMD-2022-01",
            description="Controller clarification",
            effective_on="2022-01-01",
        )
        self.versions.track_effective_date(
            document_id=regulation["document_id"], effective_on="2020-08-01", event="enters_force"
        )
        snap = self.versions.snapshot(
            document_id=code["document_id"], label="baseline-2000", payload={"articles": 2}
        )
        self.versions.mark_repealed(
            document_id=local["document_id"],
            repealed_on="2025-12-31",
            replaced_by="LOC-Z-2",
            reason="superseded by comprehensive zoning code",
        )

        self.regulatory.classify_law(document_id=law["document_id"], label="statutory")
        self.regulatory.classify_industry(document_id=law["document_id"], label="technology")
        self.regulatory.classify_topic(document_id=law["document_id"], label="privacy")
        self.regulatory.classify_jurisdiction(document_id=law["document_id"], label="national")
        self.regulatory.classify_authority(document_id=law["document_id"], label="Parliament")

        search = self.search.semantic(query="data protection controller", limit=5)
        self.search.natural_language(query="What laws regulate personal data?", limit=5)
        self.search.keyword(query="contracts", limit=5)
        self.search.article(query="Damages", limit=5)
        self.search.citation(query="DPL-1", limit=5)
        self.search.related(query="privacy", limit=5)
        self.search.cross_reference(query="DPR-1", limit=5)

        xref = self.cross_refs.referenced_law(
            from_id=regulation["document_id"], to_id=law["document_id"], detail="implements"
        )
        self.cross_refs.related_regulation(
            from_id=law["document_id"], to_id=regulation["document_id"], detail="paired regulation"
        )
        self.cross_refs.dependency(
            from_id=regulation["document_id"], to_id=constitution["document_id"], detail="constitutional basis"
        )
        arts = [a for a in self.store.li_articles.list_all() if a["document_id"] == code["document_id"]]
        if len(arts) >= 2:
            self.cross_refs.article_relationship(
                from_id=arts[0]["article_id"], to_id=arts[1]["article_id"], detail="remedy follows breach"
            )
        conflict = self.cross_refs.detect_conflict(
            document_a=order["document_id"],
            document_b=regulation["document_id"],
            severity="low",
            detail="format vs substance overlap",
        )
        dup = self.cross_refs.detect_duplicate(
            document_a=resolution["document_id"],
            document_b=order["document_id"],
            similarity=0.42,
            detail="shared digital identity theme",
        )

        summary = self.analysis.summarize(document_id=law["document_id"])
        plain = self.analysis.plain_language(document_id=law["document_id"])
        self.analysis.identify_conflicts(document_id=regulation["document_id"])
        self.analysis.gap_analysis(document_id=law["document_id"])
        impact = self.analysis.legal_impact(document_id=law["document_id"])
        self.analysis.change_impact(document_id=law["document_id"])

        self.knowledge.publish(base="legislation", key=constitution["document_id"], payload={"code": "CONST-LI-1"})
        self.knowledge.publish(base="regulation", key=regulation["document_id"], payload={"code": "DPR-1"})
        if arts:
            self.knowledge.publish(base="article", key=arts[0]["article_id"], payload={"number": arts[0]["number"]})
        self.knowledge.publish(base="reference", key=xref["xref_id"], payload={"relation": "referenced_law"})

        dash = self.dashboard.render(dashboard_type="legislation")
        return {
            "bootstrap": True,
            "constitution_id": constitution["document_id"],
            "code_id": code["document_id"],
            "law_id": law["document_id"],
            "regulation_id": regulation["document_id"],
            "resolution_id": resolution["document_id"],
            "order_id": order["document_id"],
            "treaty_id": treaty["document_id"],
            "local_id": local["document_id"],
            "history_id": hist["history_id"],
            "comparison_id": cmp_["comparison_id"],
            "amendment_id": amd["amendment_id"],
            "snapshot_id": snap["snapshot_id"],
            "search_id": search["search_id"],
            "xref_id": xref["xref_id"],
            "conflict_id": conflict["conflict_id"],
            "duplicate_id": dup["duplicate_id"],
            "summary_id": summary["analysis_id"],
            "plain_id": plain["analysis_id"],
            "impact_id": impact["analysis_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "repository": self.repository.status(),
            "versions": self.versions.status(),
            "regulatory": self.regulatory.status(),
            "search": self.search.status(),
            "cross_refs": self.cross_refs.status(),
            "analysis": self.analysis.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


legislation_intelligence = LegislationIntelligenceSuite()
