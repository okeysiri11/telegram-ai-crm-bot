"""Enterprise Digital Twin 2.0 — Sprint 24.5 / v7.5.0.

Design target: src/modules/enterprise-digital-twin → platform_enterprise_digital_twin.
Realtime enterprise digital copy. Distinct from legacy Digital Twin (EDT).
Source of truth for Predictive Intelligence, Simulation Lab, and AI Orchestrator.
"""

from platform_enterprise_digital_twin.facade import EnterpriseDigitalTwinLibrary, enterprise_digital_twin_library

__all__ = ["EnterpriseDigitalTwinLibrary", "enterprise_digital_twin_library"]
