# Plugin realtime — dashboard updates via Realtime Hub.

from __future__ import annotations

from typing import Any


class PluginRealtime:
    """Publish live dashboard updates without direct WebSocket access."""

    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id

    async def publish_widget_update(self, widget_id: str, data: dict[str, Any]) -> None:
        from platform_realtime.models import RealtimeMessage
        from platform_realtime.realtime_hub import realtime_hub

        message = RealtimeMessage(
            type="event",
            channel="dashboard",
            event="WidgetUpdated",
            widget_id=widget_id,
            data={"plugin_id": self.plugin_id, "widget_id": widget_id, "payload": data},
        )
        await realtime_hub.broadcast_channel("dashboard", message)

    async def publish_channel_event(self, channel: str, event: str, data: dict[str, Any]) -> None:
        from platform_realtime.models import RealtimeMessage
        from platform_realtime.realtime_hub import realtime_hub

        message = RealtimeMessage(
            type="event",
            channel=channel,
            event=event,
            data={"plugin_id": self.plugin_id, **data},
        )
        await realtime_hub.broadcast_channel(channel, message)

    async def publish_plugin_status(self, status: str, details: dict[str, Any] | None = None) -> None:
        from platform_realtime.event_dispatcher import RealtimeEventDispatcher

        await RealtimeEventDispatcher.publish_plugin_loaded(
            {
                "plugin_id": self.plugin_id,
                "status": status,
                "details": details or {},
            }
        )
