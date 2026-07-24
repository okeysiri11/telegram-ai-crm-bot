"""Enterprise UX Polish & Pilot Readiness — Sprint 23.1 / v6.12.0.

Design target: src/modules/enterprise-pilot-readiness → platform_enterprise_pilot_readiness.
Polish existing suites for real pilots — no new business modules. AI proposes UX fixes only.
"""

from platform_enterprise_pilot_readiness.facade import PilotReadinessLibrary, pilot_readiness_library

__all__ = ["PilotReadinessLibrary", "pilot_readiness_library"]
