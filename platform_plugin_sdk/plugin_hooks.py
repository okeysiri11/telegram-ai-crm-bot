# Plugin hook system — lifecycle and platform event hooks.

from __future__ import annotations

import inspect
import logging
from enum import Enum
from typing import Any, Awaitable, Callable

from platform_plugin_sdk.exceptions import PluginHookError

logger = logging.getLogger(__name__)

HookHandler = Callable[..., Any | Awaitable[Any]]


class HookName(str, Enum):
    ON_INSTALL = "on_install"
    ON_ENABLE = "on_enable"
    ON_DISABLE = "on_disable"
    ON_RELOAD = "on_reload"
    ON_REQUEST_CREATED = "on_request_created"
    ON_REQUEST_COMPLETED = "on_request_completed"
    ON_WORKFLOW_STARTED = "on_workflow_started"
    ON_WORKFLOW_COMPLETED = "on_workflow_completed"
    ON_CONFIGURATION_CHANGED = "on_configuration_changed"
    ON_JOB_COMPLETED = "on_job_completed"
    ON_EVENT = "on_event"


PLATFORM_EVENT_HOOKS: dict[str, HookName] = {
    "RequestCreatedEvent": HookName.ON_REQUEST_CREATED,
    "RequestCompletedEvent": HookName.ON_REQUEST_COMPLETED,
    "WorkflowStartedEvent": HookName.ON_WORKFLOW_STARTED,
    "WorkflowCompletedEvent": HookName.ON_WORKFLOW_COMPLETED,
    "ConfigurationChangedEvent": HookName.ON_CONFIGURATION_CHANGED,
    "JobCompletedEvent": HookName.ON_JOB_COMPLETED,
}


class PluginHookRegistry:
    """Registers and dispatches plugin hooks in isolation."""

    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id
        self._hooks: dict[str, list[HookHandler]] = {}
        self._bus_handlers: list[str] = []

    def register(self, hook: HookName | str, handler: HookHandler) -> None:
        key = hook.value if isinstance(hook, HookName) else str(hook)
        self._hooks.setdefault(key, []).append(handler)

    async def dispatch(self, hook: HookName | str, ctx: Any, **payload: Any) -> None:
        key = hook.value if isinstance(hook, HookName) else str(hook)
        handlers = self._hooks.get(key, [])
        for handler in handlers:
            await self._invoke(handler, ctx, **payload)

    def wire_platform_events(self, ctx: Any) -> None:
        """Subscribe plugin hooks to platform EventBus events."""
        from events.event_bus import PlatformEventBus

        for event_name, hook_name in PLATFORM_EVENT_HOOKS.items():
            if hook_name.value not in self._hooks:
                continue

            async def _bridge(event: Any, *, _hook=hook_name) -> None:
                await self.dispatch(_hook, ctx, event=event)

            handler_id = PlatformEventBus.subscribe(event_name, _bridge, handler_id=f"plugin_{self.plugin_id}_{event_name}")
            self._bus_handlers.append(handler_id)

    def unwire_platform_events(self) -> None:
        from events.event_bus import reset_subscribers

        reset_subscribers()
        self._bus_handlers.clear()

    async def _invoke(self, handler: HookHandler, ctx: Any, **payload: Any) -> None:
        try:
            sig = inspect.signature(handler)
            params = list(sig.parameters.values())
            if params and params[0].name in ("ctx", "context", "c"):
                result = handler(ctx, **payload)
            elif params and params[0].name == "self":
                result = handler(**payload)
            else:
                result = handler(ctx, **payload)
            if inspect.isawaitable(result):
                await result
        except Exception as exc:
            logger.exception("plugin_hook_failed plugin=%s handler=%s", self.plugin_id, handler)
            raise PluginHookError(str(exc)) from exc

    def handlers_for(self, hook: HookName | str) -> list[HookHandler]:
        key = hook.value if isinstance(hook, HookName) else str(hook)
        return list(self._hooks.get(key, []))
