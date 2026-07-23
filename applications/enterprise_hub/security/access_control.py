"""Access control facade combining authz + policies."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.security.authorization import AuthorizationService
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class AccessControl:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.authorization = AuthorizationService(self.store)

    def check(
        self,
        *,
        identity_id: str,
        permission: str,
        mode: str = "rbac",
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.authorization.authorize(
            identity_id=identity_id,
            permission=permission,
            mode=mode,
            attributes=attributes,
        )

    def status(self) -> dict[str, Any]:
        return self.authorization.status()
