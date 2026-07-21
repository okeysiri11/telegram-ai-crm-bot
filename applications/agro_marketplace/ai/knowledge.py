# Agricultural knowledge base — taxonomy, seasonality, regional, standards.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.ai.models import KnowledgeArticle, KnowledgeKind
from applications.agro_marketplace.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.agro_marketplace.shared.store import AgroStore, agro_store

_SEED: list[dict[str, Any]] = [
    {
        "kind": KnowledgeKind.CROP_TAXONOMY,
        "title": "Cereal grains",
        "body": "Wheat, maize, barley, sorghum and rice are primary cereal commodities.",
        "tags": ["grains", "taxonomy"],
        "crop": "wheat",
    },
    {
        "kind": KnowledgeKind.CROP_TAXONOMY,
        "title": "Cash crops",
        "body": "Coffee, tea, cocoa and cotton are common export cash crops.",
        "tags": ["cash_crops", "taxonomy"],
        "crop": "coffee",
    },
    {
        "kind": KnowledgeKind.SEASONALITY,
        "title": "Long rains planting",
        "body": "Long rains season typically supports maize planting in East Africa (Mar–May).",
        "tags": ["season", "maize"],
        "region": "East Africa",
        "crop": "maize",
    },
    {
        "kind": KnowledgeKind.SEASONALITY,
        "title": "Harvest windows",
        "body": "Cereal harvest windows vary by altitude; dry-down moisture below 14% preferred.",
        "tags": ["harvest", "moisture"],
        "crop": "maize",
    },
    {
        "kind": KnowledgeKind.REGIONAL,
        "title": "Rift Valley grains",
        "body": "Rift Valley is a major grain surplus region with strong warehouse capacity.",
        "tags": ["rift", "grains"],
        "region": "Rift",
    },
    {
        "kind": KnowledgeKind.MARKET_TREND,
        "title": "Export premium for graded lots",
        "body": "Grade A lots with certificates typically command 5–15% price premiums.",
        "tags": ["price", "quality"],
    },
    {
        "kind": KnowledgeKind.QUALITY_STANDARD,
        "title": "Moisture and foreign material",
        "body": "Target moisture ≤14%, foreign material ≤2% for most grain contracts.",
        "tags": ["quality", "standards"],
        "crop": "wheat",
    },
    {
        "kind": KnowledgeKind.EXPORT_REGULATION,
        "title": "Phytosanitary documentation",
        "body": "Export shipments generally require phytosanitary certificates and origin docs.",
        "tags": ["export", "compliance"],
    },
]


class AgroKnowledgeService:
    def __init__(
        self,
        store: AgroStore | None = None,
        ecosystem: EcosystemBridge | None = None,
    ) -> None:
        self._store = store or agro_store
        self._ecosystem = ecosystem or ecosystem_bridge
        self._seeded = False

    def _ensure_seeded(self) -> None:
        if self._seeded and self._store.knowledge_articles.count() > 0:
            return
        if self._store.knowledge_articles.count() == 0:
            for item in _SEED:
                article = KnowledgeArticle(
                    kind=item["kind"],
                    title=item["title"],
                    body=item["body"],
                    tags=list(item.get("tags", [])),
                    region=item.get("region", ""),
                    crop=item.get("crop", ""),
                )
                self._store.knowledge_articles.save(article.article_id, article)
        self._seeded = True

    def add_article(self, article: KnowledgeArticle) -> KnowledgeArticle:
        self._ensure_seeded()
        return self._store.knowledge_articles.save(article.article_id, article)

    def list_articles(self, *, kind: KnowledgeKind | None = None) -> list[KnowledgeArticle]:
        self._ensure_seeded()
        items = self._store.knowledge_articles.list_all()
        if kind:
            items = [a for a in items if a.kind == kind]
        return items

    def search(self, query: str, *, kind: KnowledgeKind | None = None) -> list[dict[str, Any]]:
        self._ensure_seeded()
        q = query.lower().strip()
        results: list[dict[str, Any]] = []
        for article in self.list_articles(kind=kind):
            hay = f"{article.title} {article.body} {' '.join(article.tags)} {article.crop} {article.region}".lower()
            if not q or q in hay:
                results.append(article.to_dict())
        # Reuse Ecosystem Knowledge Graph when available
        for node in self._ecosystem.knowledge_lookup(query):
            results.append({"source": "ecosystem_knowledge_graph", **node})
        return results

    def crop_taxonomy(self) -> list[dict[str, Any]]:
        return self.search("", kind=KnowledgeKind.CROP_TAXONOMY)

    def seasonality(self, *, crop: str = "", region: str = "") -> list[dict[str, Any]]:
        items = self.list_articles(kind=KnowledgeKind.SEASONALITY)
        if crop:
            items = [a for a in items if a.crop.lower() == crop.lower() or crop.lower() in a.body.lower()]
        if region:
            items = [a for a in items if a.region.lower() == region.lower() or region.lower() in a.body.lower()]
        return [a.to_dict() for a in items]

    def export_regulations(self, query: str = "export") -> list[dict[str, Any]]:
        return self.search(query, kind=KnowledgeKind.EXPORT_REGULATION)

    def metrics(self) -> dict[str, Any]:
        self._ensure_seeded()
        return {"articles": self._store.knowledge_articles.count()}


agro_knowledge = AgroKnowledgeService()
