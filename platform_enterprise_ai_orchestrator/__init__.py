"""Enterprise AI Orchestrator & Multi-Agent Council — Sprint 24.0 / v7.0.0.

Design target: src/modules/enterprise-ai-orchestrator → platform_enterprise_ai_orchestrator.
Central intelligence for Enterprise AI Platform 7.0. Owner always decides; AI never acts alone.
Extensible council — new agents register without core changes.
"""

from platform_enterprise_ai_orchestrator.facade import EnterpriseAIOrchestratorLibrary, enterprise_ai_orchestrator_library

__all__ = ["EnterpriseAIOrchestratorLibrary", "enterprise_ai_orchestrator_library"]
