# Platform Memory — AI context engine for all agents.

from platform_memory.config import (
    DEFAULT_SEMANTIC_CONFIG,
    DEFAULT_TOKEN_LIMITS,
    SemanticMemoryConfig,
    TokenLimits,
)
from platform_memory.context_assembler import ContextAssembler
from platform_memory.entities import MemoryEntity, MemoryFilters, MemorySearchHit
from platform_memory.memory_service import MemoryService, memory_service
from platform_memory.models import AIContextBundle, ContextAssemblyRequest, ContextAssemblyResult
from platform_memory.providers.embedding_provider import DummyEmbeddingProvider, EmbeddingProvider
from platform_memory.repositories import (
    AgentMemoryRepository,
    BusinessMemoryRepository,
    ConversationHistoryRepository,
    ProjectMemoryRepository,
    SessionMemoryRepository,
    UserProfileRepository,
)
from platform_memory.repositories.memory_repository import MemoryRepository
from platform_memory.repositories.in_memory_semantic_repository import InMemoryMemoryRepository
from platform_memory.search.memory_search_service import MemorySearchService
from platform_memory.service import ContextEngineService, context_engine_service
from platform_memory.runtime_engine import ContextEngine, context_engine
from platform_memory.project_memory_engine import ProjectMemoryEngine, project_memory_engine
from platform_memory.project_memory_service import ProjectMemoryService, project_memory_service
from platform_memory.project_memory_models import MemoryKind, MemoryLayer

# Epic 45.2 — Continuous Memory
from platform_memory.memory_manager import MemoryManager, VERSION as CONTINUOUS_MEMORY_VERSION, memory_manager
from platform_memory.conversation_memory import ConversationMemory, conversation_memory
from platform_memory.working_memory import WorkingMemory, working_memory
from platform_memory.long_term_memory import LongTermMemory, long_term_memory
from platform_memory.smart_recall import SmartRecall, smart_recall
from platform_memory.ai_resume import AiResume, ai_resume
from platform_memory.context_engine_v2 import ContextEngineV2, context_engine_v2

__all__ = [
    "AgentMemoryRepository",
    "AIContextBundle",
    "AiResume",
    "BusinessMemoryRepository",
    "ContextAssembler",
    "ContextAssemblyRequest",
    "ContextAssemblyResult",
    "ContextEngine",
    "ContextEngineService",
    "ContextEngineV2",
    "CONTINUOUS_MEMORY_VERSION",
    "ConversationHistoryRepository",
    "ConversationMemory",
    "DEFAULT_SEMANTIC_CONFIG",
    "DEFAULT_TOKEN_LIMITS",
    "DummyEmbeddingProvider",
    "EmbeddingProvider",
    "InMemoryMemoryRepository",
    "LongTermMemory",
    "MemoryEntity",
    "MemoryFilters",
    "MemoryManager",
    "MemoryRepository",
    "MemorySearchHit",
    "MemorySearchService",
    "MemoryService",
    "ProjectMemoryRepository",
    "SemanticMemoryConfig",
    "SessionMemoryRepository",
    "SmartRecall",
    "TokenLimits",
    "UserProfileRepository",
    "WorkingMemory",
    "ai_resume",
    "context_engine",
    "context_engine_service",
    "context_engine_v2",
    "conversation_memory",
    "long_term_memory",
    "memory_manager",
    "memory_service",
    "MemoryKind",
    "MemoryLayer",
    "ProjectMemoryEngine",
    "ProjectMemoryService",
    "project_memory_engine",
    "project_memory_service",
    "smart_recall",
    "working_memory",
]
