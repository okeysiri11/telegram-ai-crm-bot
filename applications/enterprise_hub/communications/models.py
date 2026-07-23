"""Notification models and constants — Sprint 19.4."""

from __future__ import annotations

from typing import Any

QUEUE_STATUSES = (
    "pending",
    "processing",
    "delivered",
    "failed",
    "retry",
    "expired",
)

PRIORITIES = ("critical", "high", "medium", "low", "silent")

CHANNELS = (
    "email",
    "telegram",
    "sms",
    "push",
    "websocket",
    "webhook",
    "corporate_chat",
    "future",
)

TEMPLATE_KINDS = (
    "crm",
    "invoice",
    "lead",
    "task",
    "approval",
    "security",
    "ai_alert",
    "report",
)

TEMPLATE_FORMATS = ("markdown", "html", "plain")

PRIORITY_CHANNEL_MAP: dict[str, list[str]] = {
    "critical": ["telegram", "sms", "push", "email"],
    "high": ["telegram", "push", "email"],
    "medium": ["email", "push"],
    "low": ["email"],
    "silent": ["websocket"],
}


def normalize_status(value: str) -> str:
    return (value or "").lower().strip()


def empty_delivery_tracking(**kwargs: Any) -> dict[str, Any]:
    return {
        "message_id": kwargs.get("message_id", ""),
        "recipient": kwargs.get("recipient", ""),
        "channel": kwargs.get("channel", ""),
        "status": kwargs.get("status", "pending"),
        "retries": kwargs.get("retries", 0),
        "delivered_at": kwargs.get("delivered_at"),
        "read_at": kwargs.get("read_at"),
        "error": kwargs.get("error", ""),
        "latency_ms": kwargs.get("latency_ms", 0.0),
    }
