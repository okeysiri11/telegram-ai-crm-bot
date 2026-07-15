# Unified notification center — Telegram / Email / SMS / Push providers.

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
        subject: str | None = None,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        ...


class TelegramProvider(NotificationProvider):
    name = "telegram"

    async def send(
        self,
        *,
        to: str | int,
        subject: str | None = None,
        body: str,
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
        subject: str | None = None,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        # Stub — wire SMTP / SendGrid in production via SMTP_* env vars.
        smtp_host = os.getenv("SMTP_HOST")
        if not smtp_host:
            logger.info("EmailProvider stub: to=%s subject=%s", to, subject)
            return True
        logger.warning("EmailProvider SMTP not yet implemented — message logged only")
        return True


class SMSProvider(NotificationProvider):
    name = "sms"

    async def send(
        self,
        *,
        to: str | int,
        subject: str | None = None,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        # Stub — Twilio / MessageBird via SMS_PROVIDER_URL.
        if not os.getenv("SMS_PROVIDER_URL"):
            logger.info("SMSProvider stub: to=%s body=%s", to, body[:80])
            return True
        logger.warning("SMSProvider not yet implemented — message logged only")
        return True


class PushProvider(NotificationProvider):
    name = "push"

    async def send(
        self,
        *,
        to: str | int,
        subject: str | None = None,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        logger.info("PushProvider stub: to=%s subject=%s", to, subject)
        return True


class NotificationCenterV1:
    _providers: dict[str, NotificationProvider] | None = None

    @classmethod
    def providers(cls) -> dict[str, NotificationProvider]:
        if cls._providers is None:
            cls._providers = {
                "telegram": TelegramProvider(),
                "email": EmailProvider(),
                "sms": SMSProvider(),
                "push": PushProvider(),
            }
        return cls._providers

    @classmethod
    async def send(
        cls,
        *,
        channel: str,
        to: str | int,
        body: str,
        subject: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        provider = cls.providers().get(channel)
        if provider is None:
            logger.error("Unknown notification channel: %s", channel)
            return False
        ok = await provider.send(to=to, subject=subject, body=body, metadata=metadata)
        try:
            from services.pg_platform_audit_engine import PlatformAuditEngineV1

            await PlatformAuditEngineV1.log(
                event_type="NOTIFICATION_SENT",
                entity_type="notification",
                entity_id=str(to),
                payload={"channel": channel, "ok": ok, "subject": subject},
            )
        except Exception:
            pass
        return ok

    @classmethod
    async def notify_managers(cls, body: str) -> None:
        from config import DEFAULT_AUTO_MANAGER_ID, DEFAULT_DEALER_MANAGER_ID

        for tid in {DEFAULT_AUTO_MANAGER_ID, DEFAULT_DEALER_MANAGER_ID}:
            if tid:
                await cls.send(channel="telegram", to=tid, body=body)

    @classmethod
    async def notify_owner(cls, body: str) -> None:
        from config import OWNER_ID

        if OWNER_ID:
            await cls.send(channel="telegram", to=OWNER_ID, body=body, subject="Owner alert")

    @classmethod
    async def notify_managers_and_owner(cls, body: str) -> None:
        await cls.notify_managers(body)
        await cls.notify_owner(body)
