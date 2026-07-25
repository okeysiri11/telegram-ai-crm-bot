"""Enterprise Test Infrastructure Foundation — Sprint 25.1 / v8.1.0.

Design target: src/platform/testing → platform_testing.
Unified Test Center for Smoke, Integration, Regression, Performance, Chaos and more.
Does not duplicate platform_quality / EQA — additive enterprise test infrastructure.
"""

from platform_testing.facade import TestInfrastructureLibrary, test_infrastructure_library

__all__ = ["TestInfrastructureLibrary", "test_infrastructure_library"]
