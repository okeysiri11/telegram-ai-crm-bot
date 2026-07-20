# Platform Agent Registry — plugin-based AI agent system.

from platform_agents.agents import BUILTIN_AGENTS, register_builtin_agents
from platform_agents.base_agent import BaseAgent
from platform_agents.exceptions import (
    AgentAlreadyRegisteredError,
    AgentNotFoundError,
    AgentPluginLoadError,
    AgentRegistryError,
    AgentValidationError,
)
from platform_agents.models import AgentCapability, AgentExecutionResult, AgentMetadata
from platform_agents.plugin_loader import AgentPluginLoader, agent_plugin_loader
from platform_agents.registry import AgentRegistry, agent_registry
from platform_agents.validation import validate_capabilities, validate_metadata

__all__ = [
    "AgentAlreadyRegisteredError",
    "AgentCapability",
    "AgentExecutionResult",
    "AgentMetadata",
    "AgentNotFoundError",
    "AgentPluginLoadError",
    "AgentPluginLoader",
    "AgentRegistry",
    "AgentRegistryError",
    "AgentValidationError",
    "BaseAgent",
    "BUILTIN_AGENTS",
    "agent_plugin_loader",
    "agent_registry",
    "register_builtin_agents",
    "validate_capabilities",
    "validate_metadata",
]
