"""Enterprise Simulation Lab & Scenario Engine — Sprint 24.4 / v7.4.0.

Design target: src/modules/enterprise-simulation-lab → platform_enterprise_simulation_lab.
Safe sandbox for what-if scenarios before real rollout. Owner always decides.
Distinct from legacy Simulation Engine (ESI).
"""

from platform_enterprise_simulation_lab.facade import SimulationLabLibrary, simulation_lab_library

__all__ = ["SimulationLabLibrary", "simulation_lab_library"]
