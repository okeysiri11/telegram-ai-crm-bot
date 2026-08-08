"""ADOS Hercules — Enterprise Execution Engine (Epic Hercules 1.0).

Unified computational kernel for CRM, ERP, AI Studio, verticals, Telegram, agents.
Wraps platform_jobs + platform_ai; does not duplicate vendor SDKs or job queues.
"""

from __future__ import annotations

VERSION = "1.0.0"
EPIC = "HERCULES_1.0"


def __getattr__(name: str):
    if name == "HerculesRuntime":
        from platform_hercules.runtime.hercules_runtime import HerculesRuntime

        return HerculesRuntime
    if name == "hercules_runtime":
        from platform_hercules.runtime.hercules_runtime import hercules_runtime

        return hercules_runtime
    raise AttributeError(f"module 'platform_hercules' has no attribute {name!r}")


__all__ = ["HerculesRuntime", "hercules_runtime", "VERSION", "EPIC"]
