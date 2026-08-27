"""Tracking health semantics — never delete events to go green.

Re-exports lifecycle classification. WAITING_PROVIDER does not mark
infrastructure DEGRADED. Dead-letter counts are always exposed.
"""

from __future__ import annotations

from typing import Any

from services.recruiting_ops.tracking_lifecycle import (
    build_tracking_diagnostics,
    classify_item,
    is_durable,
    should_recover_to_delivered,
)

__all__ = [
    "build_tracking_diagnostics",
    "classify_item",
    "is_durable",
    "should_recover_to_delivered",
]


def tracking_health_for_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    return build_tracking_diagnostics(events)
