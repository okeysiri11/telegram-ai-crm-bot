"""users domain facade — empty strangler entrypoint.

Do not call from production handlers until migration phase.
"""

from __future__ import annotations


class UsersFacade:
    """Scaffold facade for domain `users`."""

    domain = "users"

    def health(self) -> dict:
        return {"domain": self.domain, "scaffold": True}
