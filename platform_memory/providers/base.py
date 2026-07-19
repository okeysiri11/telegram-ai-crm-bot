# Platform Memory — abstract persistence providers.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from platform_memory.models import (
    AgentMemoryRecord,
    BusinessFact,
    ConversationTurn,
    ProjectMemoryRecord,
    SessionMemoryRecord,
    UserFact,
)


class ConversationHistoryProvider(ABC):
    @abstractmethod
    async def append_turn(self, turn: ConversationTurn) -> ConversationTurn:
        raise NotImplementedError

    @abstractmethod
    async def list_turns(
        self,
        *,
        session_id: str | None = None,
        user_id: str | None = None,
        agent_id: str | None = None,
        plugin_id: str | None = None,
        limit: int = 100,
    ) -> list[ConversationTurn]:
        raise NotImplementedError

    @abstractmethod
    async def replace_turns(self, session_id: str, turns: list[ConversationTurn]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        raise NotImplementedError


class UserProfileProvider(ABC):
    @abstractmethod
    async def upsert_fact(self, fact: UserFact) -> UserFact:
        raise NotImplementedError

    @abstractmethod
    async def get_fact(self, user_id: str, key: str) -> UserFact | None:
        raise NotImplementedError

    @abstractmethod
    async def list_facts(self, user_id: str, *, limit: int = 100) -> list[UserFact]:
        raise NotImplementedError

    @abstractmethod
    async def delete_fact(self, user_id: str, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        raise NotImplementedError


class AgentMemoryProvider(ABC):
    @abstractmethod
    async def save(self, record: AgentMemoryRecord) -> AgentMemoryRecord:
        raise NotImplementedError

    @abstractmethod
    async def get(self, memory_id: str) -> AgentMemoryRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_key(
        self,
        agent_id: str,
        memory_key: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> AgentMemoryRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def list_records(
        self,
        *,
        agent_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> list[AgentMemoryRecord]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        raise NotImplementedError


class BusinessMemoryProvider(ABC):
    @abstractmethod
    async def upsert_fact(self, fact: BusinessFact) -> BusinessFact:
        raise NotImplementedError

    @abstractmethod
    async def list_facts(self, organization_id: str, *, limit: int = 100) -> list[BusinessFact]:
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        raise NotImplementedError


class SessionMemoryProvider(ABC):
    @abstractmethod
    async def save(self, record: SessionMemoryRecord) -> SessionMemoryRecord:
        raise NotImplementedError

    @abstractmethod
    async def list_records(
        self,
        *,
        session_id: str | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[SessionMemoryRecord]:
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        raise NotImplementedError


class ProjectMemoryProvider(ABC):
    @abstractmethod
    async def save(self, record: ProjectMemoryRecord) -> ProjectMemoryRecord:
        raise NotImplementedError

    @abstractmethod
    async def list_records(self, project_id: str, *, limit: int = 100) -> list[ProjectMemoryRecord]:
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        raise NotImplementedError


class MemoryProviderBundle:
    """Grouped providers for dependency injection."""

    __slots__ = (
        "conversation",
        "user_profile",
        "agent_memory",
        "business_memory",
        "session_memory",
        "project_memory",
    )

    def __init__(
        self,
        *,
        conversation: ConversationHistoryProvider,
        user_profile: UserProfileProvider,
        agent_memory: AgentMemoryProvider,
        business_memory: BusinessMemoryProvider,
        session_memory: SessionMemoryProvider,
        project_memory: ProjectMemoryProvider,
    ) -> None:
        self.conversation = conversation
        self.user_profile = user_profile
        self.agent_memory = agent_memory
        self.business_memory = business_memory
        self.session_memory = session_memory
        self.project_memory = project_memory

    async def clear_all(self) -> None:
        await self.conversation.clear()
        await self.user_profile.clear()
        await self.agent_memory.clear()
        await self.business_memory.clear()
        await self.session_memory.clear()
        await self.project_memory.clear()


ProviderFilters = dict[str, Any]
