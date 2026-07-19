"""Unit tests — platform_memory AI Memory & Context Engine."""

from __future__ import annotations

import pytest

from events.event_bus import reset_subscribers, subscribe
from platform_memory.config import TokenLimits
from platform_memory.context_assembler import ContextAssembler
from platform_memory.memory_events import ContextAssembledEvent, ConversationAppendedEvent, MemoryStoredEvent
from platform_memory.memory_service import MemoryService
from platform_memory.models import ContextAssemblyRequest, ConversationRole, MemoryCategory
from platform_memory.providers.in_memory import build_in_memory_providers
from platform_memory.repositories import (
    AgentMemoryRepository,
    BusinessMemoryRepository,
    ConversationHistoryRepository,
    ProjectMemoryRepository,
    SessionMemoryRepository,
    UserProfileRepository,
)
from platform_memory.summarizer import MemorySummarizer, estimate_tokens


@pytest.fixture
def providers():
    return build_in_memory_providers()


@pytest.fixture
def memory_service_fresh() -> MemoryService:
    return MemoryService(limits=TokenLimits(max_history_tokens=200, max_context_tokens=500))


@pytest.fixture(autouse=True)
def _clean_events():
    reset_subscribers()
    yield
    reset_subscribers()


@pytest.mark.asyncio
async def test_conversation_history_repository(providers):
    repo = ConversationHistoryRepository(providers.conversation)
    turn = await repo.append_message(
        session_id="s1",
        role=ConversationRole.USER.value,
        content="Hello",
        user_id="u1",
    )
    history = await repo.list_history(session_id="s1")
    assert len(history) == 1
    assert history[0].turn_id == turn.turn_id


@pytest.mark.asyncio
async def test_user_profile_repository(providers):
    repo = UserProfileRepository(providers.user_profile)
    fact = await repo.remember_fact(user_id="u1", key="lang", value="ru")
    assert fact.key == "lang"
    loaded = await repo.get_fact("u1", "lang")
    assert loaded is not None
    assert loaded.value == "ru"


@pytest.mark.asyncio
async def test_agent_memory_repository_recall_by_key(providers):
    repo = AgentMemoryRepository(providers.agent_memory)
    saved = await repo.remember(agent_id="agent1", content="Prefers SMS", memory_key="channel", user_id="u1")
    loaded = await repo.recall_by_key("agent1", "channel", user_id="u1")
    assert loaded.memory_id == saved.memory_id
    updated = await repo.remember(agent_id="agent1", content="Prefers email", memory_key="channel", user_id="u1")
    assert updated.memory_id == saved.memory_id


@pytest.mark.asyncio
async def test_business_and_project_repositories(providers):
    business = BusinessMemoryRepository(providers.business_memory)
    project = ProjectMemoryRepository(providers.project_memory)
    bf = await business.remember_fact(organization_id="org1", key="sla", value="24h")
    pm = await project.remember(project_id="proj1", content="Sprint 2.1 memory engine")
    assert bf.key == "sla"
    assert pm.project_id == "proj1"


@pytest.mark.asyncio
async def test_session_memory_repository(providers):
    repo = SessionMemoryRepository(providers.session_memory)
    record = await repo.remember(session_id="sess1", content="temp cart state", user_id="u1")
    items = await repo.list_memory(session_id="sess1")
    assert len(items) == 1
    assert items[0].memory_id == record.memory_id


def test_summarizer_triggers_on_long_history():
    summarizer = MemorySummarizer()
    from platform_memory.models import ConversationTurn

    turns = [
        ConversationTurn(
            turn_id=str(i),
            session_id="s1",
            role="user",
            content=f"Message number {i} with extra context " * 20,
        )
        for i in range(20)
    ]
    text, condensed = summarizer.summarize_conversation(turns, max_tokens=100)
    assert estimate_tokens(text) <= estimate_tokens("\n".join(f"user: {t.content}" for t in turns))
    assert len(condensed) < len(turns)


@pytest.mark.asyncio
async def test_context_assembler_builds_all_sections(providers):
    conversation = ConversationHistoryRepository(providers.conversation)
    user_profile = UserProfileRepository(providers.user_profile)
    agent_memory = AgentMemoryRepository(providers.agent_memory)
    business = BusinessMemoryRepository(providers.business_memory)
    session = SessionMemoryRepository(providers.session_memory)
    project = ProjectMemoryRepository(providers.project_memory)

    await conversation.append_message(session_id="s1", role="user", content="Need fleet quote", user_id="u1", agent_id="a1")
    await user_profile.remember_fact(user_id="u1", key="company", value="Acme")
    await agent_memory.remember(agent_id="a1", content="Customer prefers electric", user_id="u1")
    await business.remember_fact(organization_id="org1", key="region", value="EU")
    await session.remember(session_id="s1", content="Browsing SUV models", user_id="u1")
    await project.remember(project_id="p1", content="Q3 fleet RFP")

    assembler = ContextAssembler(
        conversation=conversation,
        user_profile=user_profile,
        agent_memory=agent_memory,
        business_memory=business,
        session_memory=session,
        project_memory=project,
        limits=TokenLimits(max_context_tokens=4096),
    )
    result = await assembler.assemble(
        ContextAssemblyRequest(
            session_id="s1",
            user_id="u1",
            agent_id="a1",
            organization_id="org1",
            project_id="p1",
            current_message="What options do we have?",
        )
    )
    assert "Current conversation" in result.prompt_context
    assert "company" in result.prompt_context
    assert "electric" in result.prompt_context
    assert "region" in result.prompt_context
    assert result.total_tokens > 0


@pytest.mark.asyncio
async def test_context_assembler_summarizes_when_over_limit(providers):
    conversation = ConversationHistoryRepository(providers.conversation)
    for i in range(30):
        await conversation.append_message(
            session_id="s2",
            role="user" if i % 2 == 0 else "assistant",
            content=f"Long dialog line {i} " * 15,
            user_id="u2",
        )

    assembler = ContextAssembler(
        conversation=conversation,
        user_profile=UserProfileRepository(providers.user_profile),
        agent_memory=AgentMemoryRepository(providers.agent_memory),
        business_memory=BusinessMemoryRepository(providers.business_memory),
        session_memory=SessionMemoryRepository(providers.session_memory),
        project_memory=ProjectMemoryRepository(providers.project_memory),
        limits=TokenLimits(max_history_tokens=150, max_context_tokens=400, summarize_threshold_ratio=0.5),
    )
    result = await assembler.assemble(ContextAssemblyRequest(session_id="s2", user_id="u2"))
    assert result.summarized is True
    assert result.total_tokens <= 400


@pytest.mark.asyncio
async def test_memory_service_publishes_events(memory_service_fresh):
    stored: list[MemoryStoredEvent] = []
    appended: list[ConversationAppendedEvent] = []
    assembled: list[ContextAssembledEvent] = []
    subscribe(MemoryStoredEvent, lambda e: stored.append(e))
    subscribe(ConversationAppendedEvent, lambda e: appended.append(e))
    subscribe(ContextAssembledEvent, lambda e: assembled.append(e))

    await memory_service_fresh.append_conversation(
        session_id="s3",
        role=ConversationRole.USER.value,
        content="Hi",
        user_id="u3",
        agent_id="a3",
    )
    await memory_service_fresh.remember_agent_memory(
        agent_id="a3",
        content="Long-term preference",
        category=MemoryCategory.LONG_TERM.value,
    )
    await memory_service_fresh.assemble_context(ContextAssemblyRequest(session_id="s3", user_id="u3", agent_id="a3"))

    assert len(appended) == 1
    assert len(stored) == 1
    assert len(assembled) == 1


@pytest.mark.asyncio
async def test_memory_service_reset(memory_service_fresh):
    await memory_service_fresh.remember_user_fact(user_id="u1", key="x", value="y")
    memory_service_fresh.reset()
    bundle = await memory_service_fresh.build_ai_context(user_id="u1")
    assert bundle.user_profile == []
