"""Secrets package — SecretManager (layer) + SecretsManager (hardening)."""

from __future__ import annotations

from platform_security.secrets.manager import SecretManager, secret_manager
from platform_security.secrets.vault import SecretsManager

__all__ = [
    "SecretManager",
    "secret_manager",
    "SecretsManager",
]
