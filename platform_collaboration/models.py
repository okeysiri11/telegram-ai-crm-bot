# Collaboration domain models.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CollaborationMode(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"
    HIERARCHICAL = "hierarchical"
    PEER_TO_PEER = "peer_to_peer"
    SUPERVISOR_WORKER = "supervisor_worker"


class CoordinationStrategy(str, Enum):
    ROLE_BASED = "role_based"
    CAPABILITY_MATCH = "capability_match"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    SUPERVISOR_DELEGATE = "supervisor_delegate"
    PEER_CONSENSUS = "peer_consensus"


class CollaborationRole(str, Enum):
    SUPERVISOR = "supervisor"
    WORKER = "worker"
    COORDINATOR = "coordinator"
    PEER = "peer"
    SPECIALIST = "specialist"
    OBSERVER = "observer"


class MessageType(str, Enum):
    CAPABILITY_ANNOUNCEMENT = "capability_announcement"
    TASK_DELEGATION = "task_delegation"
    INTERMEDIATE_RESULT = "intermediate_result"
    PROGRESS_UPDATE = "progress_update"
    COMPLETION = "completion"
    NEGOTIATION = "negotiation"
    CONSENSUS_VOTE = "consensus_vote"
    CONFLICT = "conflict"


class ConsensusModel(str, Enum):
    VOTING = "voting"
    WEIGHTED_VOTING = "weighted_voting"
    CONFIDENCE_BASED = "confidence_based"
    MAJORITY = "majority"
    SUPERVISOR_OVERRIDE = "supervisor_override"


@dataclass
class AgentMessage:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    sender_id: str = ""
    recipient_id: str | None = None  # None = broadcast
    message_type: MessageType = MessageType.PROGRESS_UPDATE
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "session_id": self.session_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "payload": dict(self.payload),
            "timestamp": self.timestamp,
        }


@dataclass
class SharedContext:
    goal: str = ""
    session_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    intermediate_results: dict[str, Any] = field(default_factory=dict)
    capabilities: dict[str, list[str]] = field(default_factory=dict)
    assignments: dict[str, str] = field(default_factory=dict)  # task_id -> agent_id
    metadata: dict[str, Any] = field(default_factory=dict)

    def merge_result(self, agent_id: str, result: dict[str, Any]) -> None:
        self.intermediate_results[agent_id] = result

    def announce_capability(self, agent_id: str, capabilities: list[str]) -> None:
        self.capabilities[agent_id] = list(capabilities)

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "session_id": self.session_id,
            "data": dict(self.data),
            "intermediate_results": dict(self.intermediate_results),
            "capabilities": {k: list(v) for k, v in self.capabilities.items()},
            "assignments": dict(self.assignments),
        }


@dataclass
class AgentParticipant:
    agent_id: str
    role: CollaborationRole = CollaborationRole.WORKER
    weight: float = 1.0
    confidence: float = 50.0
    capabilities: list[str] = field(default_factory=list)
    status: str = "active"  # active | failed | completed | idle
    joined_at: float = field(default_factory=time.time)


@dataclass
class CollaborationTask:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    capability: str | None = None
    owner_id: str | None = None
    priority: float = 50.0
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"  # pending | assigned | running | completed | failed
    result: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    goal: str = ""
    mode: CollaborationMode = CollaborationMode.SUPERVISOR_WORKER
    strategy: CoordinationStrategy = CoordinationStrategy.SUPERVISOR_DELEGATE
    consensus_model: ConsensusModel = ConsensusModel.WEIGHTED_VOTING
    supervisor_id: str | None = None
    participants: dict[str, AgentParticipant] = field(default_factory=dict)
    shared_context: SharedContext = field(default_factory=SharedContext)
    tasks: list[CollaborationTask] = field(default_factory=list)
    messages: list[AgentMessage] = field(default_factory=list)
    status: str = "active"  # active | negotiating | consensus | completed | failed
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    collaboration_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "mode": self.mode.value,
            "strategy": self.strategy.value,
            "status": self.status,
            "participant_count": len(self.participants),
            "task_count": len(self.tasks),
            "message_count": len(self.messages),
            "collaboration_time_ms": self.collaboration_time_ms,
        }


@dataclass
class NegotiationResult:
    success: bool = True
    task_id: str = ""
    owner_id: str | None = None
    agreed_priority: float = 50.0
    agreed_tool: str | None = None
    rounds: int = 0
    conflicts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "task_id": self.task_id,
            "owner_id": self.owner_id,
            "agreed_priority": self.agreed_priority,
            "rounds": self.rounds,
            "conflicts": list(self.conflicts),
        }


@dataclass
class ConsensusResult:
    success: bool = True
    decision: str = ""
    votes: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    model: ConsensusModel = ConsensusModel.MAJORITY
    consensus_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "decision": self.decision,
            "confidence": self.confidence,
            "model": self.model.value,
            "consensus_time_ms": self.consensus_time_ms,
        }


@dataclass
class CollaborationResult:
    session: CollaborationSession
    success: bool = True
    completed_tasks: list[str] = field(default_factory=list)
    failed_tasks: list[str] = field(default_factory=list)
    consensus_results: list[ConsensusResult] = field(default_factory=list)
    negotiation_results: list[NegotiationResult] = field(default_factory=list)
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    delegations: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session": self.session.to_dict(),
            "success": self.success,
            "completed_tasks": list(self.completed_tasks),
            "failed_tasks": list(self.failed_tasks),
            "consensus_results": [c.to_dict() for c in self.consensus_results],
            "negotiation_results": [n.to_dict() for n in self.negotiation_results],
            "conflicts_detected": self.conflicts_detected,
            "conflicts_resolved": self.conflicts_resolved,
            "delegations": self.delegations,
        }
