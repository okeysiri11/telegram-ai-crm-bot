"""oidc identity provider."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.security.providers import authenticate_provider
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class OidcProvider:
    name = "oidc"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def authenticate(self, *, subject: str, secret: str = "") -> dict[str, Any]:
        return authenticate_provider(
            self.store, provider=self.name, subject=subject, secret=secret
        )
