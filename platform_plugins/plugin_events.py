# Plugin lifecycle events.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class PluginLifecycleEvent(BaseEvent):
    plugin_id: str
    version: str = ""
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class PluginInstalledEvent(PluginLifecycleEvent):
    pass


@dataclass(kw_only=True)
class PluginEnabledEvent(PluginLifecycleEvent):
    pass


@dataclass(kw_only=True)
class PluginDisabledEvent(PluginLifecycleEvent):
    pass


@dataclass(kw_only=True)
class PluginReloadedEvent(PluginLifecycleEvent):
    pass


@dataclass(kw_only=True)
class PluginFailedEvent(PluginLifecycleEvent):
    error: str = ""


@dataclass(kw_only=True)
class PluginRemovedEvent(PluginLifecycleEvent):
    pass


async def publish_plugin_event(event: PluginLifecycleEvent) -> None:
    from events.event_bus import PlatformEventBus

    await PlatformEventBus.publish(event, wait=True)

    try:
        from platform_realtime.event_dispatcher import RealtimeEventDispatcher

        await RealtimeEventDispatcher.publish_plugin_loaded(
            {
                "plugin_id": event.plugin_id,
                "action": event.event_type.replace("Event", "").lower(),
                "version": event.version,
                "message": event.message,
            }
        )
    except Exception:
        pass
