"""Autonomous AIOS models — Sprint 20.4."""

from __future__ import annotations

TASK_STATES = (
    "planned",
    "running",
    "waiting",
    "blocked",
    "suspended",
    "completed",
    "failed",
    "cancelled",
)

PRIORITIES = ("low", "normal", "high", "critical")
EXECUTION_MODES = ("sequential", "parallel", "distributed", "recursive", "collaborative")
GOAL_KINDS = ("strategic", "operational")
