"""Conflict resolution — re-exports Sprint 34.2D ConflictResolutionEngine."""

from __future__ import annotations

from platform_state.conflict_engine import (
    ConflictResolutionEngine,
    ConflictResult,
    ConflictResolver,
    MergeStrategy,
    conflict_engine,
    conflict_resolver,
)

__all__ = [
    "ConflictResolutionEngine",
    "ConflictResult",
    "ConflictResolver",
    "MergeStrategy",
    "conflict_engine",
    "conflict_resolver",
]
