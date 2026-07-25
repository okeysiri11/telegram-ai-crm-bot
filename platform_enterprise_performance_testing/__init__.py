"""Enterprise Performance & Load Testing — Sprint 25.2 / v8.2.0.

Design target: src/platform/performance → platform_enterprise_performance_testing
(for CI/CD load/stress/spike/soak gate). Legacy EPF platform_performance remains unchanged.
"""

from platform_enterprise_performance_testing.facade import (
    PerformanceTestingLibrary,
    performance_testing_library,
)

__all__ = ["PerformanceTestingLibrary", "performance_testing_library"]
