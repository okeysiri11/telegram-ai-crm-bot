"""email MFA."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.security.mfa import challenge_mfa
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class EmailMFA:
    method = "email"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def challenge(self, *, subject: str, code: str = "") -> dict[str, Any]:
        return challenge_mfa(self.store, method=self.method, subject=subject, code=code)
