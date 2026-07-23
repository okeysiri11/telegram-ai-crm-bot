"""Authentication service."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.security.providers import authenticate_provider
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class AuthenticationService:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def login(
        self,
        *,
        subject: str,
        provider: str = "local",
        secret: str = "",
    ) -> dict[str, Any]:
        return authenticate_provider(
            self.store, provider=provider, subject=subject, secret=secret
        )

    def status(self) -> dict[str, Any]:
        return {"auth_events": self.store.isam_auth_events.count()}
