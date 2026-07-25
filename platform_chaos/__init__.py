"""Enterprise Chaos Engineering & Fault Tolerance — Sprint 25.3 / v8.3.0.

Design target: src/platform/chaos → platform_chaos.
Simulates failures, validates recovery/retry/fallback/circuit breakers without touching production systems.
"""

from platform_chaos.facade import ChaosLibrary, chaos_library

__all__ = ["ChaosLibrary", "chaos_library"]
