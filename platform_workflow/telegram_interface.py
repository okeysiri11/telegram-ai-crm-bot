# Telegram task interface — no UI implementation, contract only.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TelegramTaskInterface(ABC):
    """Interface for Telegram bot integration — implement in handlers layer."""

    @abstractmethod
    async def send_task_notification(
        self,
        telegram_user_id: str,
        task_id: str,
        message: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> bool: ...

    @abstractmethod
    async def approve_task(self, telegram_user_id: str, task_id: str) -> dict[str, Any]: ...

    @abstractmethod
    async def reject_task(self, telegram_user_id: str, task_id: str, *, reason: str = "") -> dict[str, Any]: ...

    @abstractmethod
    async def complete_task(self, telegram_user_id: str, task_id: str, *, output: dict[str, Any] | None = None) -> dict[str, Any]: ...

    @abstractmethod
    async def request_clarification(self, telegram_user_id: str, task_id: str, question: str) -> dict[str, Any]: ...


class NullTelegramTaskInterface(TelegramTaskInterface):
    """No-op implementation for tests and non-Telegram environments."""

    async def send_task_notification(self, telegram_user_id, task_id, message, *, metadata=None) -> bool:
        return True

    async def approve_task(self, telegram_user_id, task_id) -> dict[str, Any]:
        return {"approved": True, "task_id": task_id}

    async def reject_task(self, telegram_user_id, task_id, *, reason="") -> dict[str, Any]:
        return {"rejected": True, "task_id": task_id, "reason": reason}

    async def complete_task(self, telegram_user_id, task_id, *, output=None) -> dict[str, Any]:
        return {"completed": True, "task_id": task_id, "output": output or {}}

    async def request_clarification(self, telegram_user_id, task_id, question) -> dict[str, Any]:
        return {"clarification_requested": True, "task_id": task_id, "question": question}


null_telegram_interface = NullTelegramTaskInterface()
