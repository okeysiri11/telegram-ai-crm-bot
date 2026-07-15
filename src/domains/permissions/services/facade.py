"""permissions domain facade — empty strangler entrypoint.

Do not call from production handlers until migration phase.
"""

from __future__ import annotations


class PermissionsFacade:
    """Scaffold facade for domain `permissions`."""

    domain = "permissions"

    def health(self) -> dict:
        return {"domain": self.domain, "scaffold": True}
