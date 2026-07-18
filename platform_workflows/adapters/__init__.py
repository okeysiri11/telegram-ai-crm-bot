# Adapters — legacy workflow systems delegate to the unified engine.

from platform_workflows.adapters.legacy_rules import LegacyRuleEngineAdapter, legacy_rule_engine
from platform_workflows.adapters.python_definitions import register_builtin_workflows

__all__ = [
    "LegacyRuleEngineAdapter",
    "legacy_rule_engine",
    "register_builtin_workflows",
]
