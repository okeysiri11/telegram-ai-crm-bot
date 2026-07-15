"""notifications domain facade — empty strangler entrypoint.

Do not call from production handlers until migration phase.
"""

from __future__ import annotations


class NotificationsFacade:
    """Scaffold facade for domain `notifications`."""

    domain = "notifications"

    def health(self) -> dict:
        return {"domain": self.domain, "scaffold": True}
