# Heartbeat — ping every 30s, disconnect inactive clients.

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone

from platform_realtime.connection_manager import connection_manager

if False:  # pragma: no cover — typing-only import avoids cycle at runtime
    from platform_realtime.realtime_hub import RealtimeHub

logger = logging.getLogger(__name__)

PING_INTERVAL_SECONDS = 30
PONG_TIMEOUT_SECONDS = 90


class HeartbeatManager:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False

    def start(self, hub: "RealtimeHub") -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(hub), name="realtime-heartbeat")
        logger.info("realtime_heartbeat_started interval=%ss", PING_INTERVAL_SECONDS)

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("realtime_heartbeat_stopped")

    async def _loop(self, hub: "RealtimeHub") -> None:
        while self._running:
            try:
                await self._tick(hub)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("realtime_heartbeat_tick_failed")
            await asyncio.sleep(PING_INTERVAL_SECONDS)

    async def _tick(self, hub: "RealtimeHub") -> None:
        stale = await connection_manager.stale_connections(
            pong_timeout_seconds=PONG_TIMEOUT_SECONDS,
        )
        for connection in stale:
            logger.warning(
                "realtime_stale_disconnect id=%s user=%s last_pong=%.1fs ago",
                connection.connection_id,
                connection.user_telegram_id,
                time.monotonic() - connection.last_pong,
            )
            await hub.disconnect(connection.connection_id, reason="heartbeat_timeout")

        connections = await connection_manager.list_connections()
        ping_payload = json.dumps(
            {
                "type": "ping",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reconnect": True,
            }
        )
        for connection in connections:
            await connection_manager.touch_ping(connection.connection_id)
            sent = await hub.send_raw(connection.connection_id, ping_payload)
            if not sent:
                hub.metrics.record_drop()


heartbeat_manager = HeartbeatManager()
