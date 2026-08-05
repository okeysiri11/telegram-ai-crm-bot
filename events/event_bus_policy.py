# Platform Event Bus policy — Sprint 32.3.
# Canonical bus: events.event_bus.PlatformEventBus. No second SoR.

from __future__ import annotations

from typing import Any

CANONICAL_EVENT_BUS = "events.event_bus.PlatformEventBus"
CANONICAL_PATH = "events/event_bus.py"

EVENT_BUS_POLICY = {
    "mandatory_cross_module": True,
    "forbid_new_event_bus_sor": True,
    "canonical": CANONICAL_EVENT_BUS,
    "path": CANONICAL_PATH,
    "legacy_allowlist": [
        "platform_events_legacy.py",
        "ecosystem/communication/event_bus/bus.py",
        "applications/finance_enterprise/integration/event_bus.py",
        "applications/enterprise_hub/event_platform/event_bus.py",
        "applications/platform_builder/team_map/engine.py",
        "src/web/src/integration-hub/enterpriseEventBus.ts",
        "src/kernel/events/",
        "platform_enterprise_event_bus/",  # Sprint 36.1 ops façade wrapping PlatformEventBus
    ],
    "rule": "Modules must communicate via PlatformEventBus publish/subscribe; "
    "do not import sibling application packages for side effects.",
}


def event_bus_policy() -> dict[str, Any]:
    return dict(EVENT_BUS_POLICY)


def get_platform_event_bus():
    from events.event_bus import PlatformEventBus, event_bus

    return PlatformEventBus, event_bus
