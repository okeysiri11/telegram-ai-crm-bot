# Platform notification interfaces — scaffold.
# TelegramProvider is fully implemented. Email/SMS/Push are stubs.
# Parallel to services/notification_center.py — not replacing it.

from __future__ import annotations

import abc
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class NotificationProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    async def send(
        self,
        *,
        to: str | int,
        body: str,
        subject: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        ...


class TelegramProvider(NotificationProvider):
    name = "telegram"

    async def send(
        self,
        *,
        to: str | int,
        body: str,
        subject: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        from config import BOT_TOKEN
        from aiogram import Bot

        if not BOT_TOKEN:
            logger.error("TelegramProvider: BOT_TOKEN missing")
            return False
        text = f"{subject}\n\n{body}" if subject else body
        bot = Bot(token=BOT_TOKEN)
        try:
            await bot.send_message(chat_id=int(to), text=text[:4000])
            return True
        except Exception:
            logger.exception("TelegramProvider send failed to=%s", to)
            return False
        finally:
            await bot.session.close()


class EmailProvider(NotificationProvider):
    name = "email"

    async def send(
        self,
        *,
        to: str | int,
        body: str,
        subject: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        logger.info("[EmailProvider STUB] to=%s subject=%s", to, subject)
        return True


class SMSProvider(NotificationProvider):
    name = "sms"

    async def send(
        self,
        *,
        to: str | int,
        body: str,
        subject: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        logger.info("[SMSProvider STUB] to=%s body=%s", to, (body or "")[:80])
        return True


class PushProvider(NotificationProvider):
    name = "push"

    async def send(
        self,
        *,
        to: str | int,
        body: str,
        subject: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        logger.info("[PushProvider STUB] to=%s subject=%s", to, subject)
        return True


class NotificationCenter:
    """Scaffold notification facade."""

    def __init__(self) -> None:
        self.providers: dict[str, NotificationProvider] = {
            "telegram": TelegramProvider(),
            "email": EmailProvider(),
            "sms": SMSProvider(),
            "push": PushProvider(),
        }

    async def send(self, channel: str, *, to: str | int, body: str, subject: str | None = None) -> bool:
        provider = self.providers.get(channel)
        if provider is None:
            logger.error("Unknown channel: %s", channel)
            return False
        return await provider.send(to=to, body=body, subject=subject)
