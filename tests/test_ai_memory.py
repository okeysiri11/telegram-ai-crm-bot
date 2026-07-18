"""Tests — AI Memory & Knowledge Platform."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from events.event_bus import reset_subscribers, subscribe
from platform_ai.memory.chunking import chunker
from platform_ai.memory.memory_embeddings import cosine_similarity, embedding_registry
from platform_ai.memory.memory_retriever import memory_retriever
from platform_ai.memory.memory_service import (
    KnowledgeIndexedEvent,
    KnowledgeSearchEvent,
    MemoryCreatedEvent,
    MemoryDeletedEvent,
    memory_service,
)
from platform_ai.memory.models import ChunkStrategy, IndexRequest, MemoryType, RememberRequest, SearchMode
from platform_management.management_router import register_management_routes
from platform_management.permissions import ManagementRole
from platform_plugin_sdk.models import PluginMetadata
from platform_plugin_sdk.plugin_context import PluginContext


@pytest.fixture(autouse=True)
def _reset_memory():
    memory_service.reset()
    reset_subscribers()
    yield
    memory_service.reset()
    reset_subscribers()


@pytest.fixture(autouse=True)
def _grant_permissions(monkeypatch):
    async def _owner(_tid):
        return ManagementRole.OWNER

    async def _authorize(_principal, _permission):
        return True

    async def _authenticate(_tid):
        from platform_identity.models import AuthMethod, Principal, PlatformRole

        return Principal(
            principal_id="test",
            auth_method=AuthMethod.TELEGRAM_USER,
            telegram_id=42,
            roles=[PlatformRole.OWNER.value],
        )

    monkeypatch.setattr("platform_management.permissions.resolve_role", _owner)
    from platform_identity.identity_service import identity_service

    monkeypatch.setattr(identity_service, "authorize", _authorize)
    monkeypatch.setattr(identity_service, "authenticate_telegram", _authenticate)


@pytest.mark.asyncio
async def test_memory_lifecycle():
    created: list[MemoryCreatedEvent] = []
    subscribe(MemoryCreatedEvent, lambda e: created.append(e))

    record = await memory_service.remember(
        RememberRequest(content="User prefers electric vehicles", memory_type=MemoryType.USER.value, key="preference", user_id="u1")
    )
    assert record["memory_id"]
    assert record["content"] == "User prefers electric vehicles"
    assert len(created) == 1

    recalled = memory_service.recall(key="preference", user_id="u1")
    assert recalled["content"] == "User prefers electric vehicles"

    deleted: list[MemoryDeletedEvent] = []
    subscribe(MemoryDeletedEvent, lambda e: deleted.append(e))
    result = await memory_service.forget(record["memory_id"])
    assert result["deleted"] is True


@pytest.mark.asyncio
async def test_knowledge_indexing():
    indexed: list[KnowledgeIndexedEvent] = []
    subscribe(KnowledgeIndexedEvent, lambda e: indexed.append(e))

    doc = await memory_service.index(
        IndexRequest(
            title="Vehicle Policy",
            content="All fleet vehicles must pass safety inspection.\n\nElectric vehicles get priority charging.",
            doc_type="markdown",
            tags=["policy", "fleet"],
        )
    )
    assert doc["chunk_count"] >= 1
    assert len(indexed) == 1

    docs = memory_service.list_documents()
    assert len(docs) == 1
    assert docs[0]["title"] == "Vehicle Policy"


@pytest.mark.asyncio
async def test_semantic_retrieval():
    await memory_service.index(
        IndexRequest(
            title="Insurance Guide",
            content="Comprehensive coverage protects against collision and theft. Liability is mandatory.",
            doc_type="txt",
        )
    )
    await memory_service.remember(
        RememberRequest(content="Customer asked about collision coverage", memory_type=MemoryType.CONVERSATION.value, key="conv1")
    )

    results = await memory_service.search("collision coverage insurance", mode=SearchMode.HYBRID.value, limit=5)
    assert results["count"] >= 1
    assert any("collision" in r["content"].lower() for r in results["results"])


@pytest.mark.asyncio
async def test_keyword_search():
    await memory_service.remember(
        RememberRequest(content="VIN decoder returned Toyota Camry 2020", memory_type=MemoryType.WORKFLOW.value, key="vin_result")
    )
    results = await memory_service.search("Toyota Camry", mode=SearchMode.KEYWORD.value)
    assert results["count"] >= 1


@pytest.mark.asyncio
async def test_chunking_strategies():
    text = "First paragraph about cars.\n\nSecond paragraph about trucks.\n\nThird paragraph about bikes."
    para = chunker.chunk(text, "doc1", strategy=ChunkStrategy.PARAGRAPH.value)
    assert len(para) == 3

    fixed = chunker.chunk("abcdefghijklmnop", "doc2", strategy=ChunkStrategy.FIXED_SIZE.value, chunk_size=5)
    assert len(fixed) >= 3

    sliding = chunker.chunk("abcdefghijklmnop", "doc3", strategy=ChunkStrategy.SLIDING_WINDOW.value, chunk_size=8, overlap=2)
    assert len(sliding) >= 2

    for chunk in para:
        assert chunk.metadata.get("strategy") == ChunkStrategy.PARAGRAPH.value


@pytest.mark.asyncio
async def test_ranking():
    await memory_service.remember(RememberRequest(content="unrelated content about weather", memory_type=MemoryType.TEMPORARY.value))
    await memory_service.remember(RememberRequest(content="lead scoring model for automotive sales", memory_type=MemoryType.LONG_TERM.value))

    results = await memory_service.search("automotive lead scoring", limit=5)
    if results["results"]:
        assert results["results"][0]["score"] >= results["results"][-1]["score"]


@pytest.mark.asyncio
async def test_search_caching():
    await memory_service.remember(RememberRequest(content="cached memory entry", key="cache_test"))
    first = await memory_service.search("cached memory", use_cache=True)
    second = await memory_service.search("cached memory", use_cache=True)
    assert first["count"] == second["count"]
    invalidated = memory_retriever.invalidate_cache()
    assert invalidated >= 0


@pytest.mark.asyncio
async def test_embeddings():
    provider = embedding_registry.get("local")
    emb = await provider.embed("test text")
    assert len(emb) == provider.dimensions
    sim = cosine_similarity(emb, emb)
    assert sim == pytest.approx(1.0, abs=0.01)


@pytest.mark.asyncio
async def test_knowledge_rebuild():
    doc = await memory_service.index(IndexRequest(title="Test", content="Line one.\n\nLine two.", doc_type="txt"))
    result = await memory_service.rebuild_index(doc["document_id"])
    assert result["rebuilt"] == 1


@pytest.mark.asyncio
async def test_ai_context_injection():
    await memory_service.remember(
        RememberRequest(content="Plugin config: auto vertical enabled", memory_type=MemoryType.PLUGIN.value, plugin_id="auto")
    )
    bundle = await memory_service.build_ai_context(query="auto configuration", plugin_id="auto")
    assert bundle.plugin_context["plugin_id"] == "auto"


@pytest.mark.asyncio
async def test_plugin_sdk_memory():
    ctx = PluginContext(
        plugin_id="auto",
        version="1.0.0",
        metadata=PluginMetadata(plugin_id="auto", name="Auto", version="1.0.0"),
    )
    stored = await ctx.ai.memory.remember("Customer prefers SUVs", key="pref", user_id="u42")
    assert stored["memory_id"]

    doc = await ctx.ai.memory.index_knowledge("FAQ", "How do I decode a VIN? Use the VIN decoder skill.", doc_type="markdown")
    assert doc["chunk_count"] >= 1

    search = await ctx.ai.memory.search("VIN decode")
    assert search["count"] >= 1


@pytest.mark.asyncio
async def test_memory_events():
    searches: list[KnowledgeSearchEvent] = []
    subscribe(KnowledgeSearchEvent, lambda e: searches.append(e))
    await memory_service.remember(RememberRequest(content="event test memory"))
    await memory_service.search("event test")
    assert len(searches) >= 1


@pytest.mark.asyncio
async def test_management_api(actor_header):
    app = web.Application()
    register_management_routes(app)
    async with TestClient(TestServer(app)) as client:
        stats = await client.get("/management/ai/memory/statistics", headers=actor_header)
        assert stats.status == 200

        remember = await client.post(
            "/management/ai/memory/remember",
            json={"content": "API memory test", "memory_type": "session", "key": "api_test"},
            headers=actor_header,
        )
        assert remember.status == 200

        search = await client.post(
            "/management/ai/memory/search",
            json={"query": "API memory"},
            headers=actor_header,
        )
        assert search.status == 200
        body = await search.json()
        assert body["success"] is True

        index = await client.post(
            "/management/ai/memory/knowledge/index",
            json={"title": "API Doc", "content": "Management API knowledge indexing works.", "doc_type": "txt"},
            headers=actor_header,
        )
        assert index.status == 201

        kb = await client.get("/management/ai/memory/knowledge", headers=actor_header)
        assert kb.status == 200
        kb_body = await kb.json()
        assert len(kb_body["data"]["documents"]) >= 1


@pytest.mark.asyncio
async def test_rag_flow():
    """Example RAG: index knowledge → search → inject into context."""
    await memory_service.index(
        IndexRequest(
            title="Product Catalog",
            content="Model X: electric SUV, starting at $45000. Model Y: compact sedan, starting at $28000.",
            doc_type="txt",
            tags=["catalog"],
        )
    )
    search = await memory_service.search_knowledge("electric SUV price")
    assert search["count"] >= 1

    context = await memory_service.inject_context(
        {"input": {"query": "electric SUV price"}},
        query="electric SUV price",
    )
    assert "relevant_knowledge" in context
    assert len(context["relevant_knowledge"]) >= 1
