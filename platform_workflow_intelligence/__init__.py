"""Workflow Intelligence & AI Execution Engine — Sprint 24.1 / v7.1.0.

Design target: src/modules/workflow-intelligence → platform_workflow_intelligence.
Unifies Workflow Engine, AI Orchestrator/Council, Advisor, Marketing, Commerce, Comms.
AI never starts critical processes alone; Owner Decision Center required.
"""

from platform_workflow_intelligence.facade import WorkflowIntelligenceLibrary, workflow_intelligence_library

__all__ = ["WorkflowIntelligenceLibrary", "workflow_intelligence_library"]
