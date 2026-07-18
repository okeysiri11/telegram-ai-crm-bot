# Legacy migration tracking — backward-compatible entry point.

from __future__ import annotations

from typing import Any

from platform_legacy.migration_report import build_migration_report


def migration_report() -> dict[str, Any]:
    """Return migration progress and deprecated API usage."""
    return build_migration_report()


def mark_deprecated_api(name: str) -> None:
    from platform_legacy.deprecation_manager import deprecation_manager

    deprecation_manager.mark_api_used(name)
