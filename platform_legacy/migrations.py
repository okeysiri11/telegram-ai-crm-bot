# Legacy migration tracking — replaceability metrics.

from __future__ import annotations

from typing import Any

from platform_legacy.registry import legacy_registry


def migration_report() -> dict[str, Any]:
    """Return migration progress and deprecated API usage."""
    progress = legacy_registry.migration_progress()
    progress_data = progress.to_dict()
    metrics = legacy_registry.metrics
    return {
        "progress": progress_data,
        "deprecated_api_hits": dict(metrics.deprecated_api_hits),
        "adapter_call_volume": dict(metrics.calls_by_adapter),
        "adapter_error_volume": dict(metrics.errors_by_adapter),
        "replaceable": progress_data["migration_percent"] >= 0,
    }


def mark_deprecated_api(name: str) -> None:
    legacy_registry.record_deprecated(name)
