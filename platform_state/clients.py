"""Client adapters — Telegram / Web / Desktop / Mobile / AI → PlatformState."""

from __future__ import annotations

from typing import Any

from platform_state.service import platform_state


class ClientRuntimeAdapter:
    """Thin client facade — all clients share the same PlatformStateService."""

    def __init__(self, client_id: str) -> None:
        self.client_id = client_id

    async def create_task(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("source_client", self.client_id)
        kwargs.setdefault("skip_db", True)
        return await platform_state.tasks.create(**kwargs)

    async def create_calendar_event(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("source_client", self.client_id)
        kwargs.setdefault("skip_db", True)
        return await platform_state.calendar.create_event(**kwargs)

    async def notify(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("source_client", self.client_id)
        return await platform_state.notifications.create(**kwargs)

    async def ensure_conversation(self, external_id: str, **kwargs: Any) -> dict[str, Any]:
        return await platform_state.conversations.ensure(
            source_client=self.client_id,
            external_id=external_id,
            **kwargs,
        )

    async def append_message(self, conversation_id: str, content: str, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("role", "user")
        return await platform_state.conversations.append(
            conversation_id=conversation_id,
            content=content,
            source_client=self.client_id,
            **kwargs,
        )

    async def store_memory(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("source_client", self.client_id)
        return await platform_state.memory.store(**kwargs)

    async def upload_file(self, name: str, **kwargs: Any) -> dict[str, Any]:
        return await platform_state.files.upload(name=name, source_client=self.client_id, **kwargs)

    async def upsert_lead(self, lead: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        return await platform_state.crm.update_lead(lead, source_client=self.client_id, **kwargs)

    def snapshot(self, **kwargs: Any) -> dict[str, Any]:
        return platform_state.snapshot(**kwargs).to_dict()

    def delta(self, since: str | None = None, **kwargs: Any) -> dict[str, Any]:
        return platform_state.delta(since, **kwargs)

    def register_cursor(self, *, last_revision: str | None = None, slices: list[str] | None = None) -> dict[str, Any]:
        return platform_state.register_client_cursor(
            self.client_id,
            last_revision=last_revision,
            slices=slices,
        )


telegram_runtime = ClientRuntimeAdapter("telegram")
web_runtime = ClientRuntimeAdapter("web")
desktop_runtime = ClientRuntimeAdapter("desktop")
mobile_runtime = ClientRuntimeAdapter("mobile")
api_runtime = ClientRuntimeAdapter("api")
ai_runtime = ClientRuntimeAdapter("ai")
