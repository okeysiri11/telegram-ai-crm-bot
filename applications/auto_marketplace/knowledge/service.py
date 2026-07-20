# Sales knowledge base for AI agents.

from __future__ import annotations

from applications.auto_marketplace.ai_sales.models import KnowledgeArticle
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class KnowledgeService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store
        if self._store.knowledge_articles.count() == 0:
            self._seed_defaults()

    def _seed_defaults(self) -> None:
        defaults = [
            KnowledgeArticle(
                title="Financing Options",
                category="financing",
                content="We offer lease, loan, and cash purchase options with competitive rates.",
                tags=["financing", "loan", "lease"],
            ),
            KnowledgeArticle(
                title="Trade-In Process",
                category="trade_in",
                content="Bring your vehicle for appraisal. Trade-in credit applies to your purchase.",
                tags=["trade-in", "appraisal"],
            ),
            KnowledgeArticle(
                title="Test Drive Policy",
                category="sales",
                content="Test drives available by appointment. Valid license required.",
                tags=["test-drive", "appointment"],
            ),
        ]
        for article in defaults:
            self._store.knowledge_articles.save(article.article_id, article)

    def create(self, article: KnowledgeArticle) -> KnowledgeArticle:
        return self._store.knowledge_articles.save(article.article_id, article)

    def get(self, article_id: str) -> KnowledgeArticle | None:
        return self._store.knowledge_articles.get(article_id)

    def search(self, query: str, *, category: str = "") -> list[KnowledgeArticle]:
        if self._store.knowledge_articles.count() == 0:
            self._seed_defaults()
        q = query.lower()
        results: list[KnowledgeArticle] = []
        for article in self._store.knowledge_articles.list_all():
            if category and article.category != category:
                continue
            haystack = f"{article.title} {article.content} {' '.join(article.tags)}".lower()
            if not q or q in haystack:
                results.append(article)
        return results

    def list_by_category(self, category: str) -> list[KnowledgeArticle]:
        return [a for a in self._store.knowledge_articles.list_all() if a.category == category]


knowledge_service = KnowledgeService()
