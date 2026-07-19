"""Tests — Sprint 2.2 Semantic Memory & Knowledge Engine."""

from __future__ import annotations

import pytest

from platform_memory.config import SemanticMemoryConfig
from platform_memory.context_assembler import ContextAssembler
from platform_memory.entities import MemoryEntity, MemoryFilters
from platform_memory.memory_service import MemoryService
from platform_memory.models import ContextAssemblyRequest, ConversationRole
from platform_memory.providers.embedding_provider import DummyEmbeddingProvider, cosine_similarity
from platform_memory.repositories.agent_memory_repository import AgentMemoryRepository
from platform_memory.repositories.business_memory_repository import BusinessMemoryRepository
from platform_memory.repositories.conversation_history_repository import ConversationHistoryRepository
from platform_memory.repositories.in_memory_semantic_repository import InMemoryMemoryRepository
from platform_memory.repositories.project_memory_repository import ProjectMemoryRepository
from platform_memory.repositories.session_memory_repository import SessionMemoryRepository
from platform_memory.repositories.user_profile_repository import UserProfileRepository
from platform_memory.search.memory_search_service import MemorySearchService


@pytest.fixture
def repository() -> InMemoryMemoryRepository:
    return InMemoryMemoryRepository()


@pytest.fixture
def embedding() -> DummyEmbeddingProvider:
    return DummyEmbeddingProvider()


@pytest.fixture
def search_service(repository: InMemoryMemoryRepository, embedding: DummyEmbeddingProvider) -> MemorySearchService:
    return MemorySearchService(
        repository=repository,
        embedding=embedding,
        config=SemanticMemoryConfig(similarity_threshold=0.1, max_memories=10),
    )


@pytest.fixture
def memory_service_fresh() -> MemoryService:
    return MemoryService(
        semantic_config=SemanticMemoryConfig(similarity_threshold=0.1, max_memories=10),
    )


@pytest.mark.asyncio
async def test_memory_entity_create():
    entity = MemoryEntity.create(text="Fleet insurance policy", embedding=[0.1, 0.2], owner_id="u1")
    assert entity.id
    assert entity.text == "Fleet insurance policy"
    assert entity.importance_score == 0.5


@pytest.mark.asyncio
async def test_memory_repository_crud(repository: InMemoryMemoryRepository, embedding: DummyEmbeddingProvider):
    entity = MemoryEntity.create(text="Customer prefers electric SUVs", embedding=await embedding.embed("ev"))
    saved = await repository.save(entity)
    loaded = await repository.get(saved.id)
    assert loaded is not None
    assert loaded.text == saved.text

    saved.text = "Customer prefers electric trucks"
    updated = await repository.update(saved)
    assert updated.text.endswith("trucks")

    assert await repository.delete(saved.id) is True
    assert await repository.get(saved.id) is None


@pytest.mark.asyncio
async def test_memory_repository_keyword_search(repository: InMemoryMemoryRepository, embedding: DummyEmbeddingProvider):
    await repository.save(
        MemoryEntity.create(text="Collision coverage for fleet vehicles", embedding=await embedding.embed("a"))
    )
    await repository.save(
        MemoryEntity.create(text="Weather forecast for Kyiv", embedding=await embedding.embed("b"))
    )
    hits = await repository.search("collision fleet", limit=5)
    assert len(hits) == 1
    assert "Collision" in hits[0].text


@pytest.mark.asyncio
async def test_memory_repository_semantic_search(repository: InMemoryMemoryRepository, embedding: DummyEmbeddingProvider):
    text_a = "Comprehensive auto insurance collision protection"
    text_b = "Unrelated cooking recipe for pasta"
    emb_a = await embedding.embed(text_a)
    emb_b = await embedding.embed(text_b)
    await repository.save(MemoryEntity.create(text=text_a, embedding=emb_a))
    await repository.save(MemoryEntity.create(text=text_b, embedding=emb_b))

    query_emb = emb_a
    hits = await repository.search_by_embedding(query_emb, similarity_threshold=0.0, limit=5)
    assert hits
    assert hits[0][0].text == text_a
    assert hits[0][1] == pytest.approx(1.0, abs=0.01)


@pytest.mark.asyncio
async def test_memory_repository_recent_and_important(repository: InMemoryMemoryRepository, embedding: DummyEmbeddingProvider):
    low = MemoryEntity.create(text="low", embedding=await embedding.embed("low"), importance_score=0.1)
    high = MemoryEntity.create(text="high", embedding=await embedding.embed("high"), importance_score=0.95)
    await repository.save(low)
    await repository.save(high)

    important = await repository.important(limit=1)
    assert important[0].text == "high"

    recent = await repository.recent(limit=2)
    assert len(recent) == 2


@pytest.mark.asyncio
async def test_dummy_embedding_deterministic(embedding: DummyEmbeddingProvider):
    a = await embedding.embed("hello world")
    b = await embedding.embed("hello world")
    assert a == b
    assert len(a) == embedding.dimensions


def test_cosine_similarity_identical():
    vec = [1.0, 0.0, 0.0]
    assert cosine_similarity(vec, vec) == pytest.approx(1.0, abs=0.01)


@pytest.mark.asyncio
async def test_memory_search_service_semantic(search_service: MemorySearchService, repository: InMemoryMemoryRepository, embedding: DummyEmbeddingProvider):
    await repository.save(
        MemoryEntity.create(
            text="Lead scoring model for automotive sales pipeline",
            embedding=await embedding.embed("automotive sales"),
            importance_score=0.8,
        )
    )
    await repository.save(
        MemoryEntity.create(
            text="Unrelated weather report",
            embedding=await embedding.embed("weather"),
            importance_score=0.2,
        )
    )

    hits = await search_service.search("automotive lead scoring")
    assert hits
    assert "automotive" in hits[0].entity.text.lower()
    assert hits[0].score >= hits[-1].score


@pytest.mark.asyncio
async def test_memory_search_keyword_fallback(search_service: MemorySearchService, repository: InMemoryMemoryRepository, embedding: DummyEmbeddingProvider):
    await repository.save(
        MemoryEntity.create(
            text="Unique keyword xyzzy policy document",
            embedding=await embedding.embed("unrelated"),
            importance_score=0.5,
        )
    )
    hits = await search_service.search("xyzzy policy")
    assert hits
    assert "xyzzy" in hits[0].entity.text


@pytest.mark.asyncio
async def test_context_assembler_semantic_priority(search_service: MemorySearchService, repository: InMemoryMemoryRepository, embedding: DummyEmbeddingProvider):
    from platform_memory.providers.in_memory import build_in_memory_providers

    bundle = build_in_memory_providers()
    assembler = ContextAssembler(
        conversation=ConversationHistoryRepository(bundle.conversation),
        user_profile=UserProfileRepository(bundle.user_profile),
        agent_memory=AgentMemoryRepository(bundle.agent_memory),
        business_memory=BusinessMemoryRepository(bundle.business_memory),
        session_memory=SessionMemoryRepository(bundle.session_memory),
        project_memory=ProjectMemoryRepository(bundle.project_memory),
        memory_search=search_service,
    )

    await assembler._conversation.append_message(
        session_id="s1",
        role=ConversationRole.USER.value,
        content="I need fleet insurance",
        user_id="u1",
        agent_id="a1",
    )
    await repository.save(
        MemoryEntity.create(
            text="Fleet collision coverage is mandatory",
            embedding=await embedding.embed("fleet collision"),
            owner_id="u1",
            agent_id="a1",
            session_id="s1",
            importance_score=0.9,
        )
    )

    result = await assembler.assemble(
        ContextAssemblyRequest(
            session_id="s1",
            user_id="u1",
            agent_id="a1",
            query="fleet collision insurance",
            current_message="What are my options?",
        )
    )

    assert "Current conversation" in result.prompt_context
    assert "Semantic memories" in result.prompt_context
    assert "fleet" in result.prompt_context.lower()


@pytest.mark.asyncio
async def test_memory_service_remember_and_search_semantic(memory_service_fresh: MemoryService):
    saved = await memory_service_fresh.remember_semantic(
        text="Customer wants comprehensive collision coverage",
        owner_id="u1",
        agent_id="a1",
        importance_score=0.85,
    )
    assert saved["id"]

    hits = await memory_service_fresh.search_semantic("collision coverage", owner_id="u1", agent_id="a1")
    assert hits
    assert hits[0]["score"] > 0


@pytest.mark.asyncio
async def test_memory_service_context_includes_semantic(memory_service_fresh: MemoryService):
    await memory_service_fresh.remember_semantic(
        text="Preferred contact channel is Telegram",
        owner_id="u42",
        agent_id="agent-x",
        session_id="sess-1",
        importance_score=0.7,
    )
    await memory_service_fresh.append_conversation(
        session_id="sess-1",
        role="user",
        content="Remind me how to reach support",
        user_id="u42",
        agent_id="agent-x",
    )
    bundle = await memory_service_fresh.build_ai_context(
        session_id="sess-1",
        user_id="u42",
        agent_id="agent-x",
        query="contact support",
    )
    assert bundle.prompt_context
    assert "Telegram" in bundle.prompt_context or bundle.relevant_memory


@pytest.mark.asyncio
async def test_batch_embed(embedding: DummyEmbeddingProvider):
    vectors = await embedding.batch_embed(["one", "two", "three"])
    assert len(vectors) == 3
    assert all(len(v) == embedding.dimensions for v in vectors)
