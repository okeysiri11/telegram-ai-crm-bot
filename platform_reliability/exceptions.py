# Reliability layer exceptions.

from __future__ import annotations


class ReliabilityError(Exception):
    def __init__(self, message: str, *, code: str = "reliability_error") -> None:
        super().__init__(message)
        self.code = code


class CircuitOpenError(ReliabilityError):
    def __init__(self, circuit_id: str) -> None:
        super().__init__(f"Circuit breaker open: {circuit_id}", code="circuit_open")
        self.circuit_id = circuit_id


class MaxRetriesExceededError(ReliabilityError):
    def __init__(self, attempts: int) -> None:
        super().__init__(f"Max retries exceeded: {attempts}", code="max_retries_exceeded")
        self.attempts = attempts


class CheckpointNotFoundError(ReliabilityError):
    def __init__(self, checkpoint_id: str) -> None:
        super().__init__(f"Checkpoint not found: {checkpoint_id}", code="checkpoint_not_found")
        self.checkpoint_id = checkpoint_id


class RecoveryFailedError(ReliabilityError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="recovery_failed")
