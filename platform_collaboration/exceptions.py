# Collaboration engine exceptions.

from __future__ import annotations


class CollaborationError(Exception):
    def __init__(self, message: str, *, code: str = "collaboration_error") -> None:
        super().__init__(message)
        self.code = code


class SessionNotFoundError(CollaborationError):
    def __init__(self, session_id: str) -> None:
        super().__init__(f"Collaboration session not found: {session_id}", code="session_not_found")
        self.session_id = session_id


class AgentNotInSessionError(CollaborationError):
    def __init__(self, agent_id: str, session_id: str) -> None:
        super().__init__(f"Agent {agent_id} not in session {session_id}", code="agent_not_in_session")


class ConsensusFailedError(CollaborationError):
    def __init__(self, message: str = "Consensus not reached") -> None:
        super().__init__(message, code="consensus_failed")


class NegotiationFailedError(CollaborationError):
    def __init__(self, message: str = "Negotiation failed") -> None:
        super().__init__(message, code="negotiation_failed")
