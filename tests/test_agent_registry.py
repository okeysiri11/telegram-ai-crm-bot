"""Tests — Platform Agent Registry (Sprint 3.1)."""

from __future__ import annotations

import json

import pytest

from platform_agents.agents.builtin import (
    AutoAgent,
    BUILTIN_AGENTS,
    EngineeringAgent,
    register_builtin_agents,
)
from platform_agents.base_agent import BaseAgent
from platform_agents.exceptions import (
    AgentAlreadyRegisteredError,
    AgentNotFoundError,
    AgentPluginLoadError,
    AgentValidationError,
)
from platform_agents.models import AgentExecutionResult, AgentMetadata
from platform_agents.plugin_loader import AgentPluginLoader
from platform_agents.registry import AgentRegistry
from platform_agents.validation import validate_metadata, validate_plugin_manifest


@pytest.fixture
def registry() -> AgentRegistry:
    reg = AgentRegistry()
    register_builtin_agents(reg)
    yield reg
    reg.reset()


def test_registry_lists_builtin_agents(registry: AgentRegistry):
    agents = registry.list_agents()
    assert len(agents) == len(BUILTIN_AGENTS)
    ids = {a.id for a in agents}
    assert "auto_agent" in ids
    assert "engineering_agent" in ids


def test_registry_get_agent(registry: AgentRegistry):
    agent = registry.get("auto_agent")
    assert agent.name == "Auto Agent"


def test_registry_unregister(registry: AgentRegistry):
    registry.unregister("auto_agent")
    with pytest.raises(AgentNotFoundError):
        registry.get("auto_agent")


def test_registry_duplicate_detection(registry: AgentRegistry):
    with pytest.raises(AgentAlreadyRegisteredError):
        registry.register(AutoAgent)


def test_find_by_capability(registry: AgentRegistry):
    matches = registry.find_by_capability("buy_car")
    assert len(matches) == 1
    assert matches[0].id == "auto_agent"


def test_find_by_capability_priority(registry: AgentRegistry):
    class HighPriorityAuto(BaseAgent):
        agent_id = "auto_agent_priority"
        name = "High Priority Auto"
        description = "Test"
        author = "Test"
        version = "1.0.0"
        capabilities = ["buy_car"]
        priority = 200

        async def execute(self, capability, payload=None):
            return AgentExecutionResult(agent_id=self.agent_id, capability=capability, success=True)

    registry.register(HighPriorityAuto)
    matches = registry.find_by_capability("buy_car")
    assert matches[0].id == "auto_agent_priority"


def test_enable_disable(registry: AgentRegistry):
    registry.disable("auto_agent")
    assert not registry.is_enabled("auto_agent")
    assert registry.find_by_capability("buy_car") == []

    registry.enable("auto_agent")
    assert registry.is_enabled("auto_agent")
    assert len(registry.find_by_capability("buy_car")) == 1


def test_list_agents_exclude_disabled(registry: AgentRegistry):
    registry.disable("legal_agent")
    enabled_only = registry.list_agents(include_disabled=False)
    assert all(a.enabled for a in enabled_only)
    assert not any(a.id == "legal_agent" for a in enabled_only)


def test_metadata_validation():
    meta = AgentMetadata(
        id="bad id",
        name="Test",
        description="Desc",
        version="1.0.0",
        author="Author",
        capabilities=["valid_cap"],
    )
    with pytest.raises(AgentValidationError):
        validate_metadata(meta)


def test_capability_validation():
    meta = AutoAgent.metadata()
    validate_metadata(meta)
    assert "buy_car" in meta.capabilities


def test_empty_capabilities_rejected():
    meta = AgentMetadata(
        id="empty_agent",
        name="Empty",
        description="No caps",
        version="1.0.0",
        author="Author",
        capabilities=[],
    )
    with pytest.raises(AgentValidationError):
        validate_metadata(meta)


@pytest.mark.asyncio
async def test_agent_execute(registry: AgentRegistry):
    agent = registry.get("engineering_agent")
    result = await agent.execute("blueprint_review", {"project": "tower-a"})
    assert result.success
    assert result.capability == "blueprint_review"


def test_plugin_discovery():
    loader = AgentPluginLoader()
    discovered = loader.discover()
    paths = [p.name for p in discovered]
    assert "insurance_agent_plugin" in paths


def test_plugin_load_and_register(registry: AgentRegistry):
    loader = AgentPluginLoader()
    plugin_dir = loader.plugins_root / "insurance_agent_plugin"
    registered = loader.load_and_register(registry, plugin_dir)
    assert "insurance_agent" in registered
    assert registry.get("insurance_agent").name == "Insurance Agent Plugin"


def test_plugin_auto_register_all(registry: AgentRegistry):
    loader = AgentPluginLoader()
    registered = loader.load_and_register(registry)
    assert "insurance_agent" in registered


def test_plugin_manifest_validation(tmp_path):
    plugin_dir = tmp_path / "bad_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.json").write_text(json.dumps({"id": "x"}), encoding="utf-8")
    (plugin_dir / "agent.py").write_text("pass\n", encoding="utf-8")

    with pytest.raises(AgentValidationError):
        validate_plugin_manifest(json.loads((plugin_dir / "plugin.json").read_text()))


def test_plugin_duplicate_id_rejected(registry: AgentRegistry, tmp_path):
    plugin_dir = tmp_path / "duplicate_auto"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.json").write_text(
        json.dumps(
            {
                "id": "auto_agent",
                "name": "Duplicate Auto",
                "description": "Dup",
                "version": "1.0.0",
                "author": "Test",
                "capabilities": ["buy_car"],
            }
        ),
        encoding="utf-8",
    )
    (plugin_dir / "agent.py").write_text(
        '''
from platform_agents.base_agent import BaseAgent
from platform_agents.models import AgentExecutionResult

class Agent(BaseAgent):
    agent_id = "auto_agent"
    name = "Duplicate Auto"
    description = "Dup"
    author = "Test"
    version = "1.0.0"
    capabilities = ["buy_car"]
    async def execute(self, capability, payload=None):
        return AgentExecutionResult(agent_id=self.agent_id, capability=capability, success=True)
''',
        encoding="utf-8",
    )

    loader = AgentPluginLoader(plugins_root=tmp_path)
    with pytest.raises(AgentAlreadyRegisteredError):
        loader.load_and_register(registry, plugin_dir)


def test_plugin_id_mismatch_rejected(registry: AgentRegistry, tmp_path):
    plugin_dir = tmp_path / "mismatch"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.json").write_text(
        json.dumps(
            {
                "id": "plugin_a",
                "name": "Plugin A",
                "description": "Test",
                "version": "1.0.0",
                "author": "Test",
                "capabilities": ["test_cap"],
            }
        ),
        encoding="utf-8",
    )
    (plugin_dir / "agent.py").write_text(
        '''
from platform_agents.base_agent import BaseAgent
from platform_agents.models import AgentExecutionResult

class Agent(BaseAgent):
    agent_id = "plugin_b"
    name = "Plugin B"
    description = "Test"
    author = "Test"
    version = "1.0.0"
    capabilities = ["test_cap"]
    async def execute(self, capability, payload=None):
        return AgentExecutionResult(agent_id=self.agent_id, capability=capability, success=True)
''',
        encoding="utf-8",
    )

    loader = AgentPluginLoader(plugins_root=tmp_path)
    with pytest.raises(AgentPluginLoadError):
        loader.load_and_register(registry, plugin_dir)


def test_registry_summary(registry: AgentRegistry):
    summary = registry.summary()
    assert summary["total"] == len(BUILTIN_AGENTS)
    assert summary["enabled"] == len(BUILTIN_AGENTS)
    assert summary["sources"]["builtin"] == len(BUILTIN_AGENTS)


def test_capabilities_index(registry: AgentRegistry):
    index = registry.capabilities_index()
    assert "legal_contract" in index
    assert index["legal_contract"][0] == "legal_agent"
