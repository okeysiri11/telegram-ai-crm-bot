"""EIP models and constants — Sprint 19.6."""

from __future__ import annotations

PROTOCOLS = (
    "rest",
    "graphql",
    "soap",
    "grpc",
    "websocket",
    "mqtt",
    "kafka",
    "amqp",
    "ftp",
    "smtp",
)

ADAPTERS = (
    "telegram",
    "gmail",
    "outlook",
    "google_drive",
    "onedrive",
    "dropbox",
    "stripe",
    "payoneer",
    "monobank",
    "privatbank",
    "binance",
    "openai",
    "anthropic",
    "claude",
    "custom",
)

SYNC_MODES = (
    "one_way",
    "two_way",
    "realtime",
    "scheduled",
    "incremental",
    "full",
)

AUTH_METHODS = (
    "oauth2",
    "jwt",
    "api_key",
    "client_certificate",
    "encryption",
    "secret_vault",
    "token_rotation",
)

INTEGRATION_STATUSES = ("registered", "running", "stopped", "error", "updating")
