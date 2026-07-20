# ConsensusEngine — voting, weighted, confidence-based, majority, supervisor override.

from __future__ import annotations

import time

from platform_collaboration.config import DEFAULT_COLLABORATION_CONFIG, CollaborationEngineConfig
from platform_collaboration.exceptions import ConsensusFailedError
from platform_collaboration.models import (
    AgentParticipant,
    CollaborationSession,
    ConsensusModel,
    ConsensusResult,
)


class ConsensusEngine:
    def __init__(self, *, config: CollaborationEngineConfig | None = None) -> None:
        self._config = config or DEFAULT_COLLABORATION_CONFIG

    def reach_consensus(
        self,
        session: CollaborationSession,
        *,
        proposal: str,
        votes: dict[str, str] | None = None,
        model: ConsensusModel | None = None,
    ) -> ConsensusResult:
        started = time.monotonic()
        consensus_model = model or session.consensus_model

        if votes is None:
            votes = {aid: proposal for aid in session.participants if session.participants[aid].status == "active"}

        try:
            if consensus_model == ConsensusModel.VOTING:
                result = self._simple_voting(votes)
            elif consensus_model == ConsensusModel.WEIGHTED_VOTING:
                result = self._weighted_voting(session, votes)
            elif consensus_model == ConsensusModel.CONFIDENCE_BASED:
                result = self._confidence_based(session, votes)
            elif consensus_model == ConsensusModel.SUPERVISOR_OVERRIDE:
                result = self._supervisor_override(session, proposal)
            else:
                result = self._majority_consensus(votes)
        except ConsensusFailedError:
            return ConsensusResult(
                success=False,
                model=consensus_model,
                consensus_time_ms=round((time.monotonic() - started) * 1000, 2),
            )

        result.model = consensus_model
        result.consensus_time_ms = round((time.monotonic() - started) * 1000, 2)
        result.votes = dict(votes)
        return result

    def _simple_voting(self, votes: dict[str, str]) -> ConsensusResult:
        if not votes:
            raise ConsensusFailedError()
        counts: dict[str, int] = {}
        for v in votes.values():
            counts[v] = counts.get(v, 0) + 1
        decision = max(counts, key=counts.get)  # type: ignore[arg-type]
        return ConsensusResult(success=True, decision=decision, confidence=counts[decision] / len(votes) * 100)

    def _weighted_voting(self, session: CollaborationSession, votes: dict[str, str]) -> ConsensusResult:
        if not votes:
            raise ConsensusFailedError()
        scores: dict[str, float] = {}
        total_weight = 0.0
        for agent_id, vote in votes.items():
            p = session.participants.get(agent_id)
            weight = p.weight if p else 1.0
            total_weight += weight
            scores[vote] = scores.get(vote, 0.0) + weight
        decision = max(scores, key=scores.get)  # type: ignore[arg-type]
        confidence = scores[decision] / max(total_weight, 1) * 100
        return ConsensusResult(success=True, decision=decision, confidence=round(confidence, 2))

    def _confidence_based(self, session: CollaborationSession, votes: dict[str, str]) -> ConsensusResult:
        if not votes:
            raise ConsensusFailedError()
        scores: dict[str, float] = {}
        total = 0.0
        for agent_id, vote in votes.items():
            p = session.participants.get(agent_id)
            conf = p.confidence if p else 50.0
            total += conf
            scores[vote] = scores.get(vote, 0.0) + conf
        decision = max(scores, key=scores.get)  # type: ignore[arg-type]
        return ConsensusResult(success=True, decision=decision, confidence=round(scores[decision] / max(total, 1) * 100, 2))

    def _majority_consensus(self, votes: dict[str, str]) -> ConsensusResult:
        result = self._simple_voting(votes)
        counts: dict[str, int] = {}
        for v in votes.values():
            counts[v] = counts.get(v, 0) + 1
        majority = len(votes) / 2
        if counts.get(result.decision, 0) <= majority:
            raise ConsensusFailedError("No majority reached")
        return result

    def _supervisor_override(self, session: CollaborationSession, proposal: str) -> ConsensusResult:
        if session.supervisor_id and session.supervisor_id in session.participants:
            sup = session.participants[session.supervisor_id]
            return ConsensusResult(success=True, decision=proposal, confidence=sup.confidence)
        return ConsensusResult(success=True, decision=proposal, confidence=100.0)


consensus_engine = ConsensusEngine()
