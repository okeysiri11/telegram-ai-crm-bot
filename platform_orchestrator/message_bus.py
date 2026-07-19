# Inter-agent message bus — agents communicate only through the orchestrator.

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable

from platform_orchestrator.models import AgentMessage, MessageType

logger = logging.getLogger(__name__)

MessageHandler = Callable[[AgentMessage], Awaitable[None] | None]


class AgentMessageBus:
    """In-process message bus for request/response/notification/event messages."""

    def __init__(self, *, history_limit: int = 500) -> None:
        self._subscribers: dict[MessageType, list[MessageHandler]] = defaultdict(list)
        self._history: list[AgentMessage] = []
        self._history_limit = history_limit
        self._pending_responses: dict[str, asyncio.Future[AgentMessage]] = {}

    def reset(self) -> None:
        self._subscribers.clear()
        self._history.clear()
        for future in self._pending_responses.values():
            if not future.done():
                future.cancel()
        self._pending_responses.clear()

    def subscribe(self, message_type: MessageType, handler: MessageHandler) -> None:
        self._subscribers[message_type].append(handler)

    def unsubscribe(self, message_type: MessageType, handler: MessageHandler) -> None:
        handlers = self._subscribers.get(message_type, [])
        if handler in handlers:
            handlers.remove(handler)

    async def publish(self, message: AgentMessage) -> None:
        self._record(message)
        handlers = list(self._subscribers.get(message.message_type, []))
        for handler in handlers:
            result = handler(message)
            if asyncio.iscoroutine(result):
                await result

        if message.message_type == MessageType.RESPONSE and message.correlation_id:
            future = self._pending_responses.pop(message.correlation_id, None)
            if future and not future.done():
                future.set_result(message)

    async def request(
        self,
        source_agent_id: str,
        target_agent_id: str,
        payload: dict[str, Any],
        *,
        timeout_seconds: float = 10.0,
    ) -> AgentMessage:
        correlation_id = AgentMessage(
            message_type=MessageType.REQUEST,
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            payload=payload,
        ).message_id

        request_msg = AgentMessage(
            message_type=MessageType.REQUEST,
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            payload=payload,
            correlation_id=correlation_id,
        )

        loop = asyncio.get_running_loop()
        future: asyncio.Future[AgentMessage] = loop.create_future()
        self._pending_responses[correlation_id] = future
        await self.publish(request_msg)

        try:
            return await asyncio.wait_for(future, timeout=timeout_seconds)
        except asyncio.TimeoutError as exc:
            self._pending_responses.pop(correlation_id, None)
            raise TimeoutError(
                f"Message request from {source_agent_id} to {target_agent_id} timed out"
            ) from exc

    async def respond(self, request: AgentMessage, payload: dict[str, Any]) -> None:
        response = AgentMessage(
            message_type=MessageType.RESPONSE,
            source_agent_id=request.target_agent_id or "",
            target_agent_id=request.source_agent_id,
            payload=payload,
            correlation_id=request.correlation_id or request.message_id,
        )
        await self.publish(response)

    async def notify(self, source_agent_id: str, payload: dict[str, Any], *, target_agent_id: str | None = None) -> None:
        await self.publish(
            AgentMessage(
                message_type=MessageType.NOTIFICATION,
                source_agent_id=source_agent_id,
                target_agent_id=target_agent_id,
                payload=payload,
            )
        )

    async def emit_event(self, source_agent_id: str, payload: dict[str, Any]) -> None:
        await self.publish(
            AgentMessage(
                message_type=MessageType.EVENT,
                source_agent_id=source_agent_id,
                payload=payload,
            )
        )

    def history(self, *, limit: int | None = None) -> list[AgentMessage]:
        cap = limit or self._history_limit
        return self._history[-cap:]

    def queue_length(self) -> int:
        return len(self._pending_responses)

    def _record(self, message: AgentMessage) -> None:
        self._history.append(message)
        if len(self._history) > self._history_limit:
            self._history = self._history[-self._history_limit :]


agent_message_bus = AgentMessageBus()
