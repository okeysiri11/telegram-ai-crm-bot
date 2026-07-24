"""Enterprise Autonomous Optimization Engine — Sprint 24.6 / v7.6.0.

Design target: src/modules/enterprise-autonomous-optimization → platform_enterprise_autonomous_optimization.
Continuous improvement proposals only. Path: Optimizer → Council → Owner → Approve/Reject/Modify.
AI never implements critical changes alone.
"""

from platform_enterprise_autonomous_optimization.facade import AutonomousOptimizationLibrary, autonomous_optimization_library

__all__ = ["AutonomousOptimizationLibrary", "autonomous_optimization_library"]
