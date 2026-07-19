# Platform Memory — in-memory provider (default for tests and dev).

from __future__ import annotations

from datetime import datetime, timezone

from platform_memory.models import (
    AgentMemoryRecord,
    BusinessFact,
    ConversationTurn,
    ProjectMemoryRecord,
    SessionMemoryRecord,
    UserFact,
)
from platform_memory.providers.base import (
    AgentMemoryProvider,
    BusinessMemoryProvider,
    ConversationHistoryProvider,
    MemoryProviderBundle,
    ProjectMemoryProvider,
    SessionMemoryProvider,
    UserProfileProvider,
)


def _matches(value: str | None, expected: str | None) -> bool:
    return expected is None or value == expected


class InMemoryConversationHistoryProvider(ConversationHistoryProvider):
    def __init__(self) -> None:
        self._turns: list[ConversationTurn] = []

    async def append_turn(self, turn: ConversationTurn) -> ConversationTurn:
        self._turns.append(turn)
        return turn

    async def list_turns(
        self,
        *,
        session_id: str | None = None,
        user_id: str | None = None,
        agent_id: str | None = None,
        plugin_id: str | None = None,
        limit: int = 100,
    ) -> list[ConversationTurn]:
        results = [
            t
            for t in self._turns
            if _matches(t.session_id, session_id)
            and _matches(t.user_id, user_id)
            and _matches(t.agent_id, agent_id)
            and _matches(t.plugin_id, plugin_id)
        ]
        results.sort(key=lambda t: t.created_at)
        return results[-limit:]

    async def replace_turns(self, session_id: str, turns: list[ConversationTurn]) -> None:
        self._turns = [t for t in self._turns if t.session_id != session_id] + list(turns)

    async def clear(self) -> None:
        self._turns.clear()


class InMemoryUserProfileProvider(UserProfileProvider):
    def __init__(self) -> None:
        self._facts: dict[tuple[str, str], UserFact] = {}

    async def upsert_fact(self, fact: UserFact) -> UserFact:
        self._facts[(fact.user_id, fact.key)] = fact
        return fact

    async def get_fact(self, user_id: str, key: str) -> UserFact | None:
        return self._facts.get((user_id, key))

    async def list_facts(self, user_id: str, *, limit: int = 100) -> list[UserFact]:
        facts = [f for (uid, _), f in self._facts.items() if uid == user_id]
        facts.sort(key=lambda f: f.updated_at, reverse=True)
        return facts[:limit]

    async def delete_fact(self, user_id: str, key: str) -> bool:
        return self._facts.pop((user_id, key), None) is not None

    async def clear(self) -> None:
        self._facts.clear()


class InMemoryAgentMemoryProvider(AgentMemoryProvider):
    def __init__(self) -> None:
        self._records: dict[str, AgentMemoryRecord] = {}
        self._by_key: dict[str, str] = {}

    def _scope_key(
        self,
        agent_id: str,
        memory_key: str,
        *,
        user_id: str | None,
        session_id: str | None,
    ) -> str:
        parts = [agent_id, memory_key]
        if user_id:
            parts.append(f"user={user_id}")
        if session_id:
            parts.append(f"session={session_id}")
        return ":".join(parts)

    async def save(self, record: AgentMemoryRecord) -> AgentMemoryRecord:
        updated = AgentMemoryRecord(
            memory_id=record.memory_id,
            agent_id=record.agent_id,
            content=record.content,
            memory_key=record.memory_key,
            user_id=record.user_id,
            session_id=record.session_id,
            category=record.category,
            metadata=dict(record.metadata),
            created_at=record.created_at,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self._records[updated.memory_id] = updated
        if updated.memory_key:
            self._by_key[
                self._scope_key(
                    updated.agent_id,
                    updated.memory_key,
                    user_id=updated.user_id,
                    session_id=updated.session_id,
                )
            ] = updated.memory_id
        return updated

    async def get(self, memory_id: str) -> AgentMemoryRecord | None:
        return self._records.get(memory_id)

    async def get_by_key(
        self,
        agent_id: str,
        memory_key: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> AgentMemoryRecord | None:
        memory_id = self._by_key.get(self._scope_key(agent_id, memory_key, user_id=user_id, session_id=session_id))
        return self._records.get(memory_id) if memory_id else None

    async def list_records(
        self,
        *,
        agent_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> list[AgentMemoryRecord]:
        results = list(self._records.values())
        if agent_id is not None:
            results = [r for r in results if r.agent_id == agent_id]
        if user_id is not None:
            results = [r for r in results if r.user_id == user_id]
        if session_id is not None:
            results = [r for r in results if r.session_id == session_id]
        if category is not None:
            results = [r for r in results if r.category == category]
        results.sort(key=lambda r: r.updated_at, reverse=True)
        return results[:limit]

    async def delete(self, memory_id: str) -> bool:
        record = self._records.pop(memory_id, None)
        if record and record.memory_key:
            self._by_key.pop(
                self._scope_key(
                    record.agent_id,
                    record.memory_key,
                    user_id=record.user_id,
                    session_id=record.session_id,
                ),
                None,
            )
        return record is not None

    async def clear(self) -> None:
        self._records.clear()
        self._by_key.clear()


class InMemoryBusinessMemoryProvider(BusinessMemoryProvider):
    def __init__(self) -> None:
        self._facts: dict[tuple[str, str], BusinessFact] = {}

    async def upsert_fact(self, fact: BusinessFact) -> BusinessFact:
        self._facts[(fact.organization_id, fact.key)] = fact
        return fact

    async def list_facts(self, organization_id: str, *, limit: int = 100) -> list[BusinessFact]:
        facts = [f for (oid, _), f in self._facts.items() if oid == organization_id]
        facts.sort(key=lambda f: f.updated_at, reverse=True)
        return facts[:limit]

    async def clear(self) -> None:
        self._facts.clear()


class InMemorySessionMemoryProvider(SessionMemoryProvider):
    def __init__(self) -> None:
        self._records: dict[str, SessionMemoryRecord] = {}

    async def save(self, record: SessionMemoryRecord) -> SessionMemoryRecord:
        self._records[record.memory_id] = record
        return record

    async def list_records(
        self,
        *,
        session_id: str | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[SessionMemoryRecord]:
        results = list(self._records.values())
        if session_id is not None:
            results = [r for r in results if r.session_id == session_id]
        if user_id is not None:
            results = [r for r in results if r.user_id == user_id]
        results.sort(key=lambda r: r.created_at, reverse=True)
        return results[:limit]

    async def clear(self) -> None:
        self._records.clear()


class InMemoryProjectMemoryProvider(ProjectMemoryProvider):
    def __init__(self) -> None:
        self._records: dict[str, ProjectMemoryRecord] = {}

    async def save(self, record: ProjectMemoryRecord) -> ProjectMemoryRecord:
        self._records[record.memory_id] = record
        return record

    async def list_records(self, project_id: str, *, limit: int = 100) -> list[ProjectMemoryRecord]:
        results = [r for r in self._records.values() if r.project_id == project_id]
        results.sort(key=lambda r: r.updated_at, reverse=True)
        return results[:limit]

    async def clear(self) -> None:
        self._records.clear()


def build_in_memory_providers() -> MemoryProviderBundle:
    return MemoryProviderBundle(
        conversation=InMemoryConversationHistoryProvider(),
        user_profile=InMemoryUserProfileProvider(),
        agent_memory=InMemoryAgentMemoryProvider(),
        business_memory=InMemoryBusinessMemoryProvider(),
        session_memory=InMemorySessionMemoryProvider(),
        project_memory=InMemoryProjectMemoryProvider(),
    )
