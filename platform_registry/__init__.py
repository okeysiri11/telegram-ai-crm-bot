# Sprint 34.2B — Unified Platform Registry
#
# One platform. Many clients (Web, Telegram, Mobile, Desktop, API, AI).
# Identity registries from 34.2A are re-exported — never duplicated.

from __future__ import annotations

from platform_registry.service import PlatformRegistryService, platform_registry

__all__ = [
    "PlatformRegistryService",
    "platform_registry",
]
