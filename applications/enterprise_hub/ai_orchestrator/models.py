"""AI Orchestration models — Sprint 20.1."""

from __future__ import annotations

AGENT_STATUSES = ("idle", "busy", "degraded", "offline", "ready")
TASK_STATUSES = ("pending", "planned", "dispatched", "running", "completed", "failed", "canceled")
TASK_PRIORITIES = ("low", "normal", "high", "critical")
STRATEGIES = ("sequential", "parallel", "voting", "delegation", "collaborative")
MEMORY_TIERS = ("short_term", "long_term", "corporate", "vector", "documents")
POLICY_KINDS = ("collaboration", "model_limit", "priority", "cost_quality")
