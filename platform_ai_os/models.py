"""Enterprise Multi-Agent Operating System — Sprint 27.1."""

from __future__ import annotations

VERSION = "9.2.0"
API_PREFIX = "/api/ai-os/v1"
MAOS_PREFIX = "/api/ai-os/v1/maos"
WEB_PATH = "src/web/ai-os"
SPRINT = "27.1"

ARCHITECTURE = (
    "executive_ai_director",
    "agent_registry_v2",
    "agent_communication_bus",
    "task_orchestrator",
    "ai_memory_manager",
    "ai_collaboration",
    "executive_dashboard",
)

BUS_MESSAGE_TYPES = ("request", "response", "event", "broadcast", "stream")
ORCHESTRATOR_MODES = ("parallel", "sequential", "conditional", "retry", "rollback", "timeout")
MEMORY_LAYERS = (
    "short",
    "session",
    "workspace",
    "organization",
    "knowledge",
    "semantic",
)
COLLABORATION_ACTIONS = ("discuss", "vote", "select_best", "critique", "merge")

KPI_TARGETS = {
    "executive_ai_ready": True,
    "agent_registry_ready": True,
    "communication_bus_ready": True,
    "task_orchestrator_ready": True,
    "memory_manager_ready": True,
    "collaboration_ready": True,
    "executive_dashboard_ready": True,
}

PRINCIPLES = (
    "single_executive_director",
    "capability_aware_routing",
    "dag_first_orchestration",
    "shared_layered_memory",
    "collaborative_consensus",
    "observable_multi_agent_ops",
    "phase4_enterprise_ai_os",
)
