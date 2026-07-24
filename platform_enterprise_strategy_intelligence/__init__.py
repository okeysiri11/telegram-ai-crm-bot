"""Enterprise Strategy Intelligence — Sprint 24.7 / v7.7.0.

Design target: src/modules/enterprise-strategy-intelligence → platform_enterprise_strategy_intelligence.
Long-term strategy support for owners. Path: Strategy Intelligence → Council → Owner Approval → Execution Workflow.
AI never decides strategy alone.
"""

from platform_enterprise_strategy_intelligence.facade import StrategyIntelligenceLibrary, strategy_intelligence_library

__all__ = ["StrategyIntelligenceLibrary", "strategy_intelligence_library"]
