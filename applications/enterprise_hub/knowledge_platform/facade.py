"""Knowledge Platform Suite facade — Sprint 20.3."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.knowledge_platform.analytics.quality import QualityAnalytics
from applications.enterprise_hub.knowledge_platform.analytics.relevance import RelevanceAnalytics
from applications.enterprise_hub.knowledge_platform.analytics.usage import UsageAnalytics
from applications.enterprise_hub.knowledge_platform.chunking import ChunkingEngine
from applications.enterprise_hub.knowledge_platform.citation import CitationEngine
from applications.enterprise_hub.knowledge_platform.connectors.confluence import ConfluenceConnector
from applications.enterprise_hub.knowledge_platform.connectors.custom import CustomConnector
from applications.enterprise_hub.knowledge_platform.connectors.filesystem import FilesystemConnector
from applications.enterprise_hub.knowledge_platform.connectors.github import GitHubConnector
from applications.enterprise_hub.knowledge_platform.connectors.google_drive import GoogleDriveConnector
from applications.enterprise_hub.knowledge_platform.connectors.notion import NotionConnector
from applications.enterprise_hub.knowledge_platform.connectors.onedrive import OneDriveConnector
from applications.enterprise_hub.knowledge_platform.connectors.sharepoint import SharePointConnector
from applications.enterprise_hub.knowledge_platform.document_manager import DocumentManager
from applications.enterprise_hub.knowledge_platform.embedding_manager import EmbeddingManager
from applications.enterprise_hub.knowledge_platform.knowledge_graph import KnowledgeGraph
from applications.enterprise_hub.knowledge_platform.knowledge_manager import KnowledgeManager
from applications.enterprise_hub.knowledge_platform.memory_manager import MemoryManager
from applications.enterprise_hub.knowledge_platform.ontology import Ontology
from applications.enterprise_hub.knowledge_platform.parsers.docx import DocxParser
from applications.enterprise_hub.knowledge_platform.parsers.email import EmailParser
from applications.enterprise_hub.knowledge_platform.parsers.html import HtmlParser
from applications.enterprise_hub.knowledge_platform.parsers.images import ImageParser
from applications.enterprise_hub.knowledge_platform.parsers.markdown import MarkdownParser
from applications.enterprise_hub.knowledge_platform.parsers.pdf import PdfParser
from applications.enterprise_hub.knowledge_platform.parsers.pptx import PptxParser
from applications.enterprise_hub.knowledge_platform.parsers.xlsx import XlsxParser
from applications.enterprise_hub.knowledge_platform.rag_engine import RAGEngine
from applications.enterprise_hub.knowledge_platform.ranking import RankingEngine
from applications.enterprise_hub.knowledge_platform.retrieval import RetrievalEngine
from applications.enterprise_hub.knowledge_platform.semantic_search import SemanticSearch
from applications.enterprise_hub.knowledge_platform.vector_index import VectorIndex
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class KnowledgePlatformSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.manager = KnowledgeManager(self.store)
        self.documents = DocumentManager(self.store)
        self.chunking = ChunkingEngine(self.store)
        self.embeddings = EmbeddingManager(self.store)
        self.vectors = VectorIndex(self.store)
        self.retrieval = RetrievalEngine(self.store)
        self.semantic = SemanticSearch(self.store)
        self.rag = RAGEngine(self.store)
        self.graph = KnowledgeGraph(self.store)
        self.ontology = Ontology(self.store)
        self.memory = MemoryManager(self.store)
        self.ranking = RankingEngine()
        self.citations = CitationEngine(self.store)
        self.usage = UsageAnalytics(self.store)
        self.quality = QualityAnalytics(self.store)
        self.relevance = RelevanceAnalytics(self.store)
        self.filesystem = FilesystemConnector(self.store)
        self.google_drive = GoogleDriveConnector(self.store)
        self.onedrive = OneDriveConnector(self.store)
        self.sharepoint = SharePointConnector(self.store)
        self.notion = NotionConnector(self.store)
        self.confluence = ConfluenceConnector(self.store)
        self.github = GitHubConnector(self.store)
        self.custom_connector = CustomConnector(self.store)
        self.pdf = PdfParser()
        self.docx = DocxParser()
        self.xlsx = XlsxParser()
        self.pptx = PptxParser()
        self.html = HtmlParser()
        self.markdown = MarkdownParser()
        self.email = EmailParser()
        self.images = ImageParser()

    def index_document(self, *, document_id: str) -> dict[str, Any]:
        chunks = self.chunking.chunk(document_id=document_id)
        indexed = []
        for ch in chunks:
            indexed.append(
                self.vectors.index_chunk(
                    chunk_id=ch["chunk_id"],
                    document_id=document_id,
                    text=ch["text"],
                    metadata={"index": ch["index"]},
                )
            )
        return {"document_id": document_id, "chunks": len(chunks), "vectors": len(indexed)}

    def bootstrap(self) -> dict[str, Any]:
        base = self.manager.create_base(name="Corporate KB", description="Enterprise knowledge", owner="knowledge-ops")
        ont = self.ontology.define(name="enterprise-core")

        parsed_md = self.markdown.parse(
            raw="# Sales Playbook\nUse CRM for all enterprise deals and legal review for contracts.",
            title="Sales Playbook",
        )
        parsed_pdf = self.pdf.parse(raw="Contract policy: all MSAs require legal review.", title="Contract Policy")
        parsed_docx = self.docx.parse(raw="Finance SOP for quarterly forecasting.", title="Finance SOP")

        doc1 = self.documents.ingest(
            title=parsed_md["title"],
            content=parsed_md["content"],
            doc_type="markdown",
            owner="sales",
            tags=["sales", "crm"],
            department="sales",
        )
        doc2 = self.documents.ingest(
            title=parsed_pdf["title"],
            content=parsed_pdf["content"],
            doc_type="pdf",
            owner="legal",
            tags=["legal", "contracts"],
            department="legal",
        )
        doc3 = self.documents.ingest(
            title=parsed_docx["title"],
            content=parsed_docx["content"],
            doc_type="docx",
            owner="finance",
            tags=["finance"],
            department="finance",
        )
        for d in (doc1, doc2, doc3):
            self.manager.attach_document(base_id=base["base_id"], document_id=d["document_id"])
            self.index_document(document_id=d["document_id"])

        gov = self.manager.govern(document_id=doc2["document_id"], classification="confidential", access=["legal", "admin"])

        conn_fs = self.filesystem.sync(path="/kb/sales")
        conn_gh = self.github.sync(path="org/docs", meta={"branch": "main"})
        conn_nt = self.notion.sync(path="workspace/wiki")

        user = self.graph.add_entity(kind="user", name="Alex Admin")
        company = self.graph.add_entity(kind="company", name="Bidex")
        project = self.graph.add_entity(kind="project", name="Enterprise CRM")
        contract = self.graph.add_entity(kind="contract", name="MSA-100")
        task = self.graph.add_entity(kind="task", name="Review MSA")
        document_ent = self.graph.add_entity(kind="document", name=doc2["title"], meta={"document_id": doc2["document_id"]})
        agent = self.graph.add_entity(kind="ai_agent", name="Legal Agent")
        process = self.graph.add_entity(kind="business_process", name="Contract Review")
        rel1 = self.graph.link(source_id=user["entity_id"], target_id=project["entity_id"], relation="works_on")
        rel2 = self.graph.link(source_id=contract["entity_id"], target_id=document_ent["entity_id"], relation="references")
        rel3 = self.graph.link(source_id=agent["entity_id"], target_id=process["entity_id"], relation="produced_by")
        rel4 = self.graph.link(source_id=company["entity_id"], target_id=project["entity_id"], relation="owns")
        rel5 = self.graph.link(source_id=task["entity_id"], target_id=contract["entity_id"], relation="related_to")

        mem_st = self.memory.store_memory(tier="short_term", key="last_query", value="contract policy")
        mem_lt = self.memory.store_memory(tier="long_term", key="playbook", value="sales")
        mem_pr = self.memory.store_memory(tier="project", key="crm", value="active", scope=project["entity_id"])
        mem_org = self.memory.store_memory(tier="organization", key="policy", value="msa-legal")
        mem_pers = self.memory.store_memory(tier="personal", key="prefs", value={"lang": "en"}, owner="alex")
        mem_ai = self.memory.store_memory(tier="ai_shared", key="context", value={"domain": "legal"})
        ctx = self.memory.build_context()

        answer = self.rag.answer(query="contract legal review policy", mode="hybrid", top_k=3, expand=True)
        search = self.semantic.search(query="sales CRM deals", mode="semantic", top_k=3)

        usage = self.usage.report()
        quality = self.quality.report()
        relevance = self.relevance.report()

        return {
            "bootstrap": True,
            "base_id": base["base_id"],
            "ontology_id": ont["ontology_id"],
            "document_sales_id": doc1["document_id"],
            "document_legal_id": doc2["document_id"],
            "document_finance_id": doc3["document_id"],
            "governance_id": gov["governance_id"],
            "connector_fs_id": conn_fs["connector_id"],
            "connector_github_id": conn_gh["connector_id"],
            "connector_notion_id": conn_nt["connector_id"],
            "entity_user_id": user["entity_id"],
            "entity_company_id": company["entity_id"],
            "entity_project_id": project["entity_id"],
            "entity_contract_id": contract["entity_id"],
            "entity_task_id": task["entity_id"],
            "entity_document_id": document_ent["entity_id"],
            "entity_agent_id": agent["entity_id"],
            "entity_process_id": process["entity_id"],
            "relation_ids": [rel1["relation_id"], rel2["relation_id"], rel3["relation_id"], rel4["relation_id"], rel5["relation_id"]],
            "memory_ids": [
                mem_st["memory_id"],
                mem_lt["memory_id"],
                mem_pr["memory_id"],
                mem_org["memory_id"],
                mem_pers["memory_id"],
                mem_ai["memory_id"],
            ],
            "context_id": ctx["context_id"],
            "answer_id": answer["answer_id"],
            "citation_id": answer["citation_id"],
            "search_retrieval_id": search["retrieval_id"],
            "usage_id": usage["analytics_id"],
            "quality_id": quality["analytics_id"],
            "relevance_id": relevance["analytics_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "manager": self.manager.status(),
            "documents": self.documents.status(),
            "vectors": self.vectors.status(),
            "graph": self.graph.status(),
            "ontology": self.ontology.status(),
            "memory": self.memory.status(),
            "answers": self.store.ekp_answers.count(),
            "retrievals": self.store.ekp_retrievals.count(),
        }


knowledge_platform = KnowledgePlatformSuite()
