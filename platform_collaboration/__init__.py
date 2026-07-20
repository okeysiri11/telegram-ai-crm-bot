# Platform Multi-Agent Collaboration Engine.

from platform_collaboration.collaboration_engine import CollaborationEngine, collaboration_engine
from platform_collaboration.collaboration_events import (
    AgentJoinedEvent,
    CollaborationCompletedEvent,
    CollaborationFailedEvent,
    CollaborationStartedEvent,
    ConflictDetectedEvent,
    ConflictResolvedEvent,
    ConsensusReachedEvent,
    TaskDelegatedEvent,
)
from platform_collaboration.config import DEFAULT_COLLABORATION_CONFIG, CollaborationEngineConfig
from platform_collaboration.conflict_resolver import ConflictResolver, conflict_resolver
from platform_collaboration.consensus_engine import ConsensusEngine, consensus_engine
from platform_collaboration.coordination import STRATEGY_REGISTRY
from platform_collaboration.integrations import CollaborationIntegrations, collaboration_integrations
from platform_collaboration.metrics import CollaborationMetrics, collaboration_metrics
from platform_collaboration.models import (
    AgentMessage,
    AgentParticipant,
    CollaborationMode,
    CollaborationResult,
    CollaborationRole,
    CollaborationSession,
    CollaborationTask,
    ConsensusModel,
    ConsensusResult,
    CoordinationStrategy,
    MessageType,
    NegotiationResult,
    SharedContext,
)
from platform_collaboration.negotiation_engine import NegotiationEngine, negotiation_engine
from platform_collaboration.pipeline import CollaborationPipeline, collaboration_pipeline

__all__ = [
    "DEFAULT_COLLABORATION_CONFIG",
    "AgentJoinedEvent",
    "AgentMessage",
    "AgentParticipant",
    "CollaborationCompletedEvent",
    "CollaborationEngine",
    "CollaborationEngineConfig",
    "CollaborationFailedEvent",
    "CollaborationIntegrations",
    "CollaborationMetrics",
    "CollaborationMode",
    "CollaborationPipeline",
    "CollaborationResult",
    "CollaborationRole",
    "CollaborationSession",
    "CollaborationStartedEvent",
    "CollaborationTask",
    "ConflictDetectedEvent",
    "ConflictResolvedEvent",
    "ConflictResolver",
    "ConsensusEngine",
    "ConsensusModel",
    "ConsensusReachedEvent",
    "ConsensusResult",
    "CoordinationStrategy",
    "MessageType",
    "NegotiationEngine",
    "NegotiationResult",
    "SharedContext",
    "STRATEGY_REGISTRY",
    "TaskDelegatedEvent",
    "collaboration_engine",
    "collaboration_integrations",
    "collaboration_metrics",
    "collaboration_pipeline",
    "conflict_resolver",
    "consensus_engine",
    "negotiation_engine",
]
