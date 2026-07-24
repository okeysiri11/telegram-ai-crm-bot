"""Security policies — Sprint 21.4."""

from __future__ import annotations

from typing import Any


class PolicyCatalog:
    def __init__(self) -> None:
        self._policies = [
            {"id": "pol_password", "name": "password_complexity", "min_length": 12},
            {"id": "pol_session", "name": "session_timeout", "minutes": 30},
            {"id": "pol_mfa", "name": "mfa_required_admin", "roles": ["admin"]},
        ]

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._policies)
