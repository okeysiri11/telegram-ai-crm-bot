# Platform SDK bootstrap — register and build verticals at startup.

from __future__ import annotations

import logging

from platform_sdk.vertical_builder import vertical_builder
from platform_sdk.vertical_registry import vertical_registry
from platform_sdk.verticals import BUILTIN_VERTICALS

logger = logging.getLogger(__name__)


def register_platform_verticals() -> int:
    """Register all built-in vertical classes (idempotent for tests)."""
    count = 0
    for vertical_cls in BUILTIN_VERTICALS:
        code = vertical_cls.vertical_code
        if code in vertical_registry.list_codes():
            continue
        vertical_registry.register(vertical_cls)
        count += 1
    logger.info("platform_verticals_registered count=%s", count)
    return count


def build_platform_verticals() -> dict:
    """Build all registered verticals with injected providers."""
    register_platform_verticals()
    return vertical_builder.build_all()


async def bootstrap_platform_sdk() -> dict:
    """Full SDK startup: load workflows, register, build verticals."""
    from platform_sdk.workflow_loader import sdk_workflow_loader

    loaded = sdk_workflow_loader.ensure_loaded()
    registered = register_platform_verticals()
    built = vertical_builder.build_all()
    return {
        "workflows_loaded": loaded,
        "verticals_registered": registered,
        "verticals_built": len(built),
        "vertical_codes": vertical_registry.list_codes(),
    }
