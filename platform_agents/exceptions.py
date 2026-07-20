# Agent registry exceptions.

from __future__ import annotations


class AgentRegistryError(Exception):
    def __init__(self, message: str, *, code: str = "agent_registry_error") -> None:
        super().__init__(message)
        self.code = code


class AgentNotFoundError(AgentRegistryError):
    def __init__(self, agent_id: str) -> None:
        super().__init__(f"Agent not found: {agent_id}", code="agent_not_found")
        self.agent_id = agent_id


class AgentAlreadyRegisteredError(AgentRegistryError):
    def __init__(self, agent_id: str) -> None:
        super().__init__(f"Agent already registered: {agent_id}", code="agent_already_registered")
        self.agent_id = agent_id


class AgentValidationError(AgentRegistryError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="agent_validation_error")


class AgentPluginLoadError(AgentRegistryError):
    def __init__(self, plugin_path: str, message: str) -> None:
        super().__init__(f"Failed to load agent plugin {plugin_path}: {message}", code="agent_plugin_load_error")
        self.plugin_path = plugin_path
